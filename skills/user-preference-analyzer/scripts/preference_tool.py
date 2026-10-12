#!/usr/bin/env python3
"""Maintain and render an evidence-backed user preference registry."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import sys
import tempfile
import time
from contextlib import contextmanager
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any


VALID_STATUSES = {"proposed", "confirmed", "rejected", "superseded"}
REVIEW_CONFIDENCE_THRESHOLD = 0.92
VALID_CATEGORIES = {
    "communication",
    "documentation",
    "coding",
    "architecture",
    "testing",
    "workflow",
    "scope",
    "safety",
    "decision",
}
REQUIRED_FIELDS = {
    "id",
    "category",
    "preference_key",
    "value",
    "description",
    "evidence",
    "confidence",
    "scope",
    "last_validated",
    "confirmation_status",
    "conflicts_with",
    "linked_skill",
}
EVIDENCE_FIELDS = {"source_type", "source", "observed_at", "detail"}
SECRET_PATTERNS = [
    re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b"),
    re.compile(r"\b(?:ghp|github_pat)_[A-Za-z0-9_]{16,}\b"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"(?i)\b(?:password|passwd|api[_ -]?key|access[_ -]?token)\s*[:=]\s*\S+"),
]


def parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def safe_path(root: Path, candidate: str) -> Path:
    path = (root / candidate).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"Path escapes project root: {candidate}") from exc
    return path


def global_store_root() -> Path:
    """Resolve the Agent-neutral per-user ledger directory."""
    configured = os.environ.get("USER_PREFERENCE_HOME")
    if configured:
        return Path(configured).expanduser().resolve()

    home = Path.home()
    if sys.platform == "win32":
        data_home = Path(os.environ.get("LOCALAPPDATA", home / "AppData/Local"))
    elif sys.platform == "darwin":
        data_home = home / "Library/Application Support"
    else:
        data_home = Path(os.environ.get("XDG_DATA_HOME", home / ".local/share"))
    return (data_home.expanduser() / "user-preferences").resolve()


def load_registry(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict) or not isinstance(data.get("preferences"), list):
        raise ValueError("Registry must be an object with a preferences array")
    data.setdefault("history", [])
    data.setdefault("source_inventory", [])
    data.setdefault("authorized_sources", [])
    return data


@contextmanager
def registry_lock(path: Path, timeout: float = 5.0):
    """Serialize cooperating read-modify-write operations across Agent installs."""
    lock = path.with_name(f".{path.name}.lock")
    deadline = time.monotonic() + timeout
    while True:
        try:
            descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            break
        except FileExistsError:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("账本正在被其他任务使用，请稍后重试。")
            time.sleep(min(0.05, remaining))
    try:
        os.close(descriptor)
        yield
    finally:
        lock.unlink()


def registry_version(data: dict[str, Any]) -> str:
    content = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def contains_secret(value: Any) -> bool:
    rendered = json.dumps(value, ensure_ascii=False)
    return any(pattern.search(rendered) for pattern in SECRET_PATTERNS)


def validate_registry(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    for index, item in enumerate(data.get("preferences", [])):
        label = item.get("id", f"index {index}")
        missing = sorted(REQUIRED_FIELDS - set(item))
        if missing:
            errors.append(f"{label}: missing fields: {', '.join(missing)}")
        if item.get("id") in seen:
            errors.append(f"{label}: duplicate id")
        seen.add(item.get("id"))
        if item.get("category") not in VALID_CATEGORIES:
            errors.append(f"{label}: invalid category")
        if item.get("confirmation_status") not in VALID_STATUSES:
            errors.append(f"{label}: invalid confirmation_status")
        if "confirmation_method" in item and item["confirmation_method"] != "user":
            errors.append(f"{label}: confirmation_method must be user")
        if "confirmed_at" in item:
            try:
                confirmed = datetime.fromisoformat(item["confirmed_at"])
                if confirmed.tzinfo is None:
                    raise ValueError("timezone required")
            except (TypeError, ValueError):
                errors.append(f"{label}: confirmed_at must be an ISO timestamp with timezone")
        confidence = item.get("confidence")
        if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
            errors.append(f"{label}: confidence must be between 0 and 1")
        try:
            parse_date(item.get("last_validated", ""))
        except (TypeError, ValueError):
            errors.append(f"{label}: last_validated must be YYYY-MM-DD")
        evidence = item.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            errors.append(f"{label}: evidence must be a non-empty array")
        else:
            for evidence_index, entry in enumerate(evidence):
                missing_evidence = EVIDENCE_FIELDS - set(entry)
                if missing_evidence:
                    errors.append(
                        f"{label}: evidence {evidence_index} missing "
                        + ", ".join(sorted(missing_evidence))
                    )
                try:
                    parse_date(entry.get("observed_at", ""))
                except (TypeError, ValueError):
                    errors.append(f"{label}: evidence {evidence_index} has invalid date")
        if contains_secret(item):
            errors.append(f"{label}: possible secret detected; remove it before saving")
    if contains_secret(data.get("authorized_sources", [])):
        errors.append("authorized_sources: possible secret detected; remove it before saving")
    if contains_secret(data.get("history", [])):
        errors.append("history: possible secret detected; remove it before saving")
    return errors


def analyze_registry(data: dict[str, Any], stale_days: int) -> dict[str, Any]:
    active = [
        item
        for item in data["preferences"]
        if item["confirmation_status"] not in {"rejected", "superseded"}
    ]
    by_key: dict[str, list[dict[str, Any]]] = {}
    by_id = {item["id"]: item for item in data["preferences"]}
    for item in active:
        by_key.setdefault(item["preference_key"], []).append(item)

    conflict_pairs: set[tuple[str, str]] = set()
    for items in by_key.values():
        values = {json.dumps(item["value"], sort_keys=True, ensure_ascii=False) for item in items}
        if len(values) > 1:
            for left in items:
                for right in items:
                    if left["id"] < right["id"] and left["value"] != right["value"]:
                        conflict_pairs.add((left["id"], right["id"]))
    for item in active:
        for other_id in item.get("conflicts_with", []):
            if (
                other_id in by_id
                and other_id != item["id"]
                and by_id[other_id]["confirmation_status"] not in {"rejected", "superseded"}
            ):
                conflict_pairs.add(tuple(sorted((item["id"], other_id))))

    today = date.today()
    stale = []
    for item in active:
        age = (today - parse_date(item["last_validated"])).days
        if age > stale_days:
            stale.append({"id": item["id"], "days_since_validation": age})

    proposals = []
    for item in active:
        if (
            item["category"] == "workflow"
            and len(item["evidence"]) >= 3
            and not item.get("linked_skill")
        ):
            proposals.append(
                {
                    "id": item["id"],
                    "suggested_skill": item["preference_key"].replace("_", "-"),
                    "reason": "At least three evidence items describe a recurring workflow.",
                }
            )
    return {
        "conflicts": [list(pair) for pair in sorted(conflict_pairs)],
        "stale": stale,
        "skill_proposals": proposals,
    }


def review_registry(data: dict[str, Any]) -> dict[str, Any]:
    analysis = analyze_registry(data, 180)
    stale_ids = {item["id"] for item in analysis["stale"]}
    candidates = []
    for item in sorted(data["preferences"], key=lambda item: (-item["confidence"], item["id"])):
        if item["confirmation_status"] != "proposed" or item["confidence"] <= REVIEW_CONFIDENCE_THRESHOLD:
            continue
        latest = max(item["evidence"], key=lambda entry: entry["observed_at"])
        summary = " ".join(latest["detail"].split())
        if len(summary) > 100:
            summary = summary[:99] + "…"
        conflicts = sorted({
            other for pair in analysis["conflicts"] if item["id"] in pair
            for other in pair if other != item["id"]
        })
        candidates.append({
            "id": item["id"],
            "description": item["description"],
            "value": item["value"],
            "confidence": item["confidence"],
            "confirmation_status": item["confirmation_status"],
            "evidence_summary": summary,
            "scope": item["scope"],
            "last_validated": item["last_validated"],
            "conflicts_with": conflicts,
            "stale": item["id"] in stale_ids,
        })
    return {
        "version": registry_version(data),
        "policy": {"confidence_gt": REVIEW_CONFIDENCE_THRESHOLD, "status": "proposed", "confirmation": "user", "stale_days": 180},
        "candidates": candidates,
    }


def review_text(review: dict[str, Any]) -> str:
    if not review["candidates"]:
        return f"暂无置信度超过 {REVIEW_CONFIDENCE_THRESHOLD} 的待确认偏好。"
    lines = [f"高置信度待确认清单（置信度 > {REVIEW_CONFIDENCE_THRESHOLD}；人工确认）", ""]
    for item in review["candidates"]:
        notices = []
        if item["conflicts_with"]:
            notices.append("冲突：" + ", ".join(item["conflicts_with"]) + "，请先解决再确认")
        if item["stale"]:
            notices.append("已超过 180 天未验证")
        lines.extend([
            f"{item['id']} — {item['description']}",
            f"置信度：{item['confidence']} | 状态：{item['confirmation_status']}",
            f"证据摘要：{item['evidence_summary']}",
            f"适用范围：{item['scope']} | 最近验证：{item['last_validated']}",
            "提示：" + ("；".join(notices) or "未发现冲突或过期提示"),
            "",
        ])
    lines.append(f"账本版本：{review['version']}")
    return "\n".join(lines)


def review_decisions(data: dict[str, Any], decisions: Any, expected_version: str) -> tuple[dict[str, Any], list[str]]:
    """Validate the entire user-selected batch before applying any changes."""
    if registry_version(data) != expected_version:
        raise ValueError("账本已变化，请刷新清单后重新选择。")
    if not isinstance(decisions, list) or not decisions:
        raise ValueError("decisions must be a non-empty JSON array")
    if contains_secret(decisions):
        raise ValueError("possible secret detected; review decisions were not saved")
    eligible = {item["id"]: item for item in review_registry(data)["candidates"]}
    seen = set()
    normalized = []
    for decision in decisions:
        if not isinstance(decision, dict) or set(decision) - {"id", "action", "scope"}:
            raise ValueError("Each decision must contain only id, action, and optional scope")
        record_id = decision.get("id")
        if not isinstance(record_id, str) or record_id not in eligible:
            raise ValueError(f"Not a current review candidate: {record_id}")
        if record_id in seen:
            raise ValueError(f"Duplicate decision: {record_id}")
        seen.add(record_id)
        action = decision.get("action")
        if action is None and "scope" in decision:
            action = "adjust_scope"
        elif not isinstance(action, str) or action not in {"confirm", "reject", "defer"}:
            raise ValueError(f"Invalid review action for {record_id}")
        scope = decision.get("scope")
        if "scope" in decision and (not isinstance(scope, str) or not scope.strip()):
            raise ValueError(f"scope must be a non-empty string for {record_id}")
        if action == "defer" and "scope" in decision:
            raise ValueError("A deferred record cannot change scope; omit action for a scope-only change")
        if action == "confirm" and eligible[record_id]["conflicts_with"]:
            raise ValueError(f"{record_id} has unresolved conflicts; resolve them and refresh the list first")
        normalized.append((record_id, action, scope))

    updated = copy.deepcopy(data)
    records = {item["id"]: item for item in updated["preferences"]}
    changed = []
    timestamp = datetime.now(timezone.utc).isoformat()
    for record_id, action, scope in normalized:
        if action == "defer":
            continue
        item = records[record_id]
        before = {"confirmation_status": item["confirmation_status"], "scope": item["scope"]}
        if scope is not None:
            item["scope"] = scope
        if action == "confirm":
            item["confirmation_status"] = "confirmed"
            item["confirmation_method"] = "user"
            item["confirmed_at"] = timestamp
        elif action == "reject":
            item["confirmation_status"] = "rejected"
        after = {"confirmation_status": item["confirmation_status"], "scope": item["scope"]}
        if before == after:
            continue
        changed.append(record_id)
        updated["history"].append({
            "date": timestamp[:10], "at": timestamp, "action": "review", "method": "user",
            "record_id": record_id, "before": before, "after": after,
            "detail": f"{record_id}: user selected {action}; status {before['confirmation_status']} -> {after['confirmation_status']}; scope {before['scope']} -> {after['scope']}.",
        })
    errors = validate_registry(updated)
    if errors:
        raise ValueError("\n".join(errors))
    return updated, changed


def evidence_text(item: dict[str, Any]) -> str:
    parts = []
    for entry in item["evidence"]:
        project = f"，项目：{entry['source_project']}" if entry.get("source_project") else ""
        parts.append(
            f"{entry['source']}（{entry['source_type']}，{entry['observed_at']}{project}）：{entry['detail']}"
        )
    return "<br>".join(parts)


def render_item(item: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"### {item['id']} — {item['description']}",
            "",
            f"- **偏好描述**：{item['description']}",
            f"- **证据来源**：{evidence_text(item)}",
            f"- **置信度**：{item['confidence']:.2f}",
            f"- **适用范围**：{item['scope']}",
            f"- **最近验证日期**：{item['last_validated']}",
            f"- **确认状态**：{item['confirmation_status']}",
            "",
        ]
    )


def replace_generated(path: Path, body: str) -> None:
    text = path.read_text(encoding="utf-8")
    start = "<!-- generated:start -->"
    end = "<!-- generated:end -->"
    if start not in text or end not in text:
        raise ValueError(f"Missing generated markers in {path}")
    prefix, remainder = text.split(start, 1)
    _, suffix = remainder.split(end, 1)
    atomic_write_text(path, f"{prefix}{start}\n{body.rstrip()}\n{end}{suffix}")


def render_reports(root: Path, data: dict[str, Any], stale_days: int) -> None:
    docs = root / "docs/preferences"
    groups = {
        "USER_PROFILE.md": {"communication"},
        "CODING_PREFERENCES.md": {"coding", "architecture", "testing"},
        "WORKFLOW_PATTERNS.md": {"documentation", "workflow", "scope", "safety"},
    }
    for filename, categories in groups.items():
        items = [item for item in data["preferences"] if item["category"] in categories]
        body = "\n".join(render_item(item) for item in items)
        if not body:
            body = "当前没有足够证据形成该类别的偏好记录。"
        replace_generated(docs / filename, body)

    analysis = analyze_registry(data, stale_days)
    history_lines = ["## 变更记录", ""]
    for entry in data.get("history", []):
        history_lines.append(f"- {entry['date']} — `{entry['action']}`：{entry['detail']}")
    history_lines.extend(["", "## 冲突检测", ""])
    if analysis["conflicts"]:
        history_lines.extend(f"- {' ↔ '.join(pair)}" for pair in analysis["conflicts"])
    else:
        history_lines.append("- 本次未发现活动偏好之间的冲突。")
    history_lines.extend(["", "## 过期检查", ""])
    if analysis["stale"]:
        history_lines.extend(
            f"- {item['id']}：已 {item['days_since_validation']} 天未验证。"
            for item in analysis["stale"]
        )
    else:
        history_lines.append(f"- 以 {stale_days} 天为阈值，本次没有过期偏好。")
    history_lines.extend(["", "## 新 Skill 建议", ""])
    if analysis["skill_proposals"]:
        history_lines.extend(
            f"- {item['id']}：建议评估 `{item['suggested_skill']}`。{item['reason']}"
            for item in analysis["skill_proposals"]
        )
    else:
        history_lines.append("- 当前没有满足自动提议门槛且尚未覆盖的重复流程。")
    replace_generated(docs / "DECISION_HISTORY.md", "\n".join(history_lines))


def render_sources(root: Path, data: dict[str, Any]) -> None:
    """Render the active global authorization records into SOURCES.md."""
    path = root / "SOURCES.md"
    if path.exists():
        text = path.read_text(encoding="utf-8")
    else:
        text = (
            "# Authorized Global Sources\n\n"
            "<!-- generated:start -->\n<!-- generated:end -->\n\n"
            "## Review policy\n\n"
            "- Review this file before each global refresh.\n"
            "- Never list credentials or secrets.\n"
        )
    start = "<!-- generated:start -->"
    end = "<!-- generated:end -->"
    if start not in text or end not in text:
        text = text.rstrip() + f"\n\n{start}\n{end}\n"
    records = [
        item for item in data.get("authorized_sources", []) if item.get("status") == "active"
    ]
    lines = ["## Active authorizations", ""]
    if not records:
        lines.append("No active authorization records.")
    for item in records:
        conversations = ", ".join(item.get("conversation_ids", [])) or "none"
        git = "yes" if item.get("include_git_history") else "no"
        lines.append(
            f"- `{item['id']}` **{item['label']}** — scope: {item['scope']}; "
            f"project: {item.get('project_label') or 'none'}; conversations: {conversations}; "
            f"Git history: {git}; authorized: {item['authorized_at']}"
        )
    prefix, remainder = text.split(start, 1)
    _, suffix = remainder.split(end, 1)
    body = "\n".join(lines)
    atomic_write_text(path, f"{prefix}{start}\n{body}\n{end}{suffix}")


def add_evidence_from_args(args: argparse.Namespace) -> dict[str, str]:
    evidence = {
        "source_type": args.evidence_type,
        "source": args.evidence_source,
        "observed_at": args.observed_at,
        "detail": args.evidence_detail,
    }
    if args.source_project:
        evidence["source_project"] = args.source_project
    return evidence


def add_record(data: dict[str, Any], args: argparse.Namespace) -> None:
    if any(item["id"] == args.id for item in data["preferences"]):
        raise ValueError(f"Preference already exists: {args.id}")
    item = {
        "id": args.id,
        "category": args.category,
        "preference_key": args.key,
        "value": args.value,
        "description": args.description,
        "evidence": [add_evidence_from_args(args)],
        "confidence": args.confidence,
        "scope": args.scope,
        "last_validated": args.observed_at,
        "confirmation_status": args.status,
        "conflicts_with": [],
        "linked_skill": None,
    }
    data["preferences"].append(item)
    data["history"].append(
        {"date": args.observed_at, "action": "add", "detail": f"Added {args.id}."}
    )


def update_record(data: dict[str, Any], args: argparse.Namespace) -> None:
    item = next((entry for entry in data["preferences"] if entry["id"] == args.id), None)
    if item is None:
        raise ValueError(f"Unknown preference: {args.id}")
    for argument, field in [
        ("description", "description"),
        ("value", "value"),
        ("confidence", "confidence"),
        ("scope", "scope"),
        ("status", "confirmation_status"),
        ("linked_skill", "linked_skill"),
    ]:
        value = getattr(args, argument)
        if value is not None:
            item[field] = value
    if args.evidence_source:
        item["evidence"].append(add_evidence_from_args(args))
    if args.evidence_source:
        item["last_validated"] = args.observed_at
    data["history"].append(
        {"date": args.observed_at, "action": "update", "detail": f"Updated {args.id}."}
    )


def authorize_record(data: dict[str, Any], args: argparse.Namespace) -> None:
    if not args.global_store:
        raise ValueError("authorize is available only with --global-store")
    if not args.conversation_id and not args.project_label:
        raise ValueError("authorization requires a conversation ID or project label")
    if contains_secret(vars(args)):
        raise ValueError("possible secret detected; authorization was not saved")
    same = [
        item
        for item in data.get("authorized_sources", [])
        if item.get("label") == args.label
        and item.get("project_label") == args.project_label
        and item.get("conversation_ids", []) == args.conversation_id
    ]
    if same:
        same[0].update(
            {
                "scope": args.scope,
                "include_git_history": args.include_git_history,
                "authorized_at": args.authorized_at,
                "authorization_note": args.note,
                "status": "active",
            }
        )
        action = "reauthorize"
        record_id = same[0]["id"]
    else:
        record_id = f"AUTH-{len(data.get('authorized_sources', [])) + 1:03d}"
        data.setdefault("authorized_sources", []).append(
            {
                "id": record_id,
                "label": args.label,
                "scope": args.scope,
                "project_label": args.project_label,
                "conversation_ids": args.conversation_id,
                "include_git_history": args.include_git_history,
                "authorized_at": args.authorized_at,
                "authorization_note": args.note,
                "status": "active",
            }
        )
        action = "authorize"
    data["history"].append(
        {
            "date": args.authorized_at,
            "action": action,
            "detail": f"{record_id}: {args.label} ({args.scope}).",
        }
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Project root (default: current directory)")
    parser.add_argument(
        "--global-store",
        action="store_true",
        help="Use the shared per-user preference store instead of the current project",
    )
    parser.add_argument(
        "--registry", default="docs/preferences/preferences.json", help="Registry path within root"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("validate")
    review = subparsers.add_parser("review", help="Show high-confidence proposed preferences on request")
    review.add_argument("--format", choices=["text", "json"], default="text")
    decide = subparsers.add_parser("review-decide", help="Apply an explicitly user-selected review batch")
    decide.add_argument("--decisions", type=Path, required=True, help="Local JSON array of user decisions")
    decide.add_argument("--expected-version", required=True, help="Full version returned by review")
    analyze = subparsers.add_parser("analyze")
    analyze.add_argument("--stale-days", type=int, default=180)
    render = subparsers.add_parser("render")
    render.add_argument("--stale-days", type=int, default=180)

    authorize = subparsers.add_parser("authorize")
    authorize.add_argument("--label", required=True)
    authorize.add_argument("--scope", required=True)
    authorize.add_argument("--project-label")
    authorize.add_argument("--conversation-id", action="append", default=[])
    authorize.add_argument("--include-git-history", action="store_true")
    authorize.add_argument("--note", default="")
    authorize.add_argument("--authorized-at", default=date.today().isoformat())

    add = subparsers.add_parser("add")
    add.add_argument("--id", required=True)
    add.add_argument("--category", choices=sorted(VALID_CATEGORIES), required=True)
    add.add_argument("--key", required=True)
    add.add_argument("--value", required=True)
    add.add_argument("--description", required=True)
    add.add_argument("--confidence", type=float, required=True)
    add.add_argument("--scope", required=True)
    add.add_argument("--status", choices=sorted(VALID_STATUSES), default="proposed")
    add.add_argument("--evidence-type", required=True)
    add.add_argument("--evidence-source", required=True)
    add.add_argument("--evidence-detail", required=True)
    add.add_argument("--observed-at", default=date.today().isoformat())
    add.add_argument("--source-project")

    update = subparsers.add_parser("update")
    update.add_argument("--id", required=True)
    update.add_argument("--description")
    update.add_argument("--value")
    update.add_argument("--confidence", type=float)
    update.add_argument("--scope")
    update.add_argument("--status", choices=sorted(VALID_STATUSES))
    update.add_argument("--linked-skill")
    update.add_argument("--evidence-type")
    update.add_argument("--evidence-source")
    update.add_argument("--evidence-detail")
    update.add_argument("--observed-at", default=date.today().isoformat())
    update.add_argument("--source-project")
    return parser


def run_command(args: argparse.Namespace, root: Path, registry: Path) -> int:
    data = load_registry(registry)
    errors = validate_registry(data)
    if errors:
        raise ValueError("\n".join(errors))

    if args.command == "review":
        review = review_registry(data)
        print(json.dumps(review, ensure_ascii=False, indent=2) if args.format == "json" else review_text(review))
        return 0
    if args.command == "review-decide":
        decisions = json.loads(args.decisions.expanduser().read_text(encoding="utf-8"))
        updated, changed = review_decisions(data, decisions, args.expected_version)
        if changed:
            atomic_write_json(registry, updated)
        print(json.dumps({"changed": changed, "version": registry_version(updated)}, ensure_ascii=False))
        return 0

    if args.command == "validate":
        errors = validate_registry(data)
        if errors:
            print("\n".join(f"ERROR: {error}" for error in errors))
            return 1
        print(f"OK: {len(data['preferences'])} preference records are valid")
        return 0
    if args.command == "analyze":
        errors = validate_registry(data)
        if errors:
            print("\n".join(f"ERROR: {error}" for error in errors))
            return 1
        print(json.dumps(analyze_registry(data, args.stale_days), ensure_ascii=False, indent=2))
        return 0
    if args.command == "render":
        errors = validate_registry(data)
        if errors:
            print("\n".join(f"ERROR: {error}" for error in errors))
            return 1
        render_reports(root, data, args.stale_days)
        if args.global_store:
            render_sources(root, data)
        print("OK: rendered four preference reports")
        return 0
    if args.command == "authorize":
        authorize_record(data, args)
        errors = validate_registry(data)
        if errors:
            print("\n".join(f"ERROR: {error}" for error in errors))
            return 1
        atomic_write_json(registry, data)
        if args.global_store:
            render_sources(root, data)
        print(f"OK: authorization saved in {registry}")
        return 0
    if args.command == "add":
        add_record(data, args)
    elif args.command == "update":
        if bool(args.evidence_source) != bool(args.evidence_type and args.evidence_detail):
            raise ValueError(
                "Updating evidence requires --evidence-type, --evidence-source, and --evidence-detail"
            )
        update_record(data, args)

    errors = validate_registry(data)
    if errors:
        print("\n".join(f"ERROR: {error}" for error in errors))
        return 1
    atomic_write_json(registry, data)
    print(f"OK: saved {registry}")
    return 0


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.global_store:
            root = global_store_root()
            registry = root / "preferences.json"
            if not getattr(args, "source_project", None):
                args.source_project = Path.cwd().name
        else:
            root = Path(args.root).resolve()
            registry = safe_path(root, args.registry)
        if args.command in {"add", "update", "authorize", "review-decide", "render"}:
            with registry_lock(registry):
                return run_command(args, root, registry)
        return run_command(args, root, registry)
    except (OSError, ValueError, TimeoutError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
