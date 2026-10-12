# Preference evidence schema

Use `docs/preferences/preferences.json` as the canonical registry.

This is the project-local registry. For a cross-project user-global registry, use the shared per-user location resolved by `scripts/preference_tool.py --global-store`; its `USER_PREFERENCE_HOME` override and operating-system defaults are documented in [cross-agent-installation.md](cross-agent-installation.md). Keep project-local and global registries distinct unless the user explicitly chooses one.

## Required record fields

| Field | Meaning |
|---|---|
| `id` | Stable human-readable identifier such as `WF-001`. |
| `category` | One of `communication`, `documentation`, `coding`, `architecture`, `testing`, `workflow`, `scope`, `safety`, or `decision`. |
| `preference_key` | Stable semantic key used for conflict detection. |
| `value` | Normalized value. Two active values for the same key are a conflict. |
| `description` | Human-readable preference statement. |
| `evidence` | One or more concise evidence objects. |
| `confidence` | Number from 0 to 1 describing evidence strength. |
| `scope` | Where the preference applies and important exclusions. |
| `last_validated` | ISO date `YYYY-MM-DD`. |
| `confirmation_status` | `proposed`, `confirmed`, `rejected`, or `superseded`. |
| `conflicts_with` | List of record IDs with a known semantic conflict. |
| `linked_skill` | Existing Skill name or `null`. |

Each evidence object requires `source_type`, `source`, `observed_at`, and `detail`. It may also include `source_project` for global cross-project records. Refer to a conversation by title or bounded task identifier and summarize the relevant behavior; do not copy an entire private message.

## Confidence guide

- `0.40–0.59`: a single ambiguous behavior; keep as weak context and do not operationalize.
- `0.60–0.79`: repeated behavior or one explicit task-specific instruction.
- `0.80–0.89`: repeated across independent tasks or supported by an explicit statement plus behavior.
- `0.90–1.00`: explicit, repeated, and recently validated.

Confidence never changes `proposed` to `confirmed`.

## Conflict rules

A conflict exists when:

1. two non-rejected, non-superseded records share a `preference_key` but have different `value` fields; or
2. either record lists the other in `conflicts_with`.

Do not automatically merge opposing scopes. First determine whether they are true conflicts or valid scope-specific variants. If scopes differ, refine the scopes or keys. If they overlap, request user confirmation and retain both until resolved.

## Staleness and Skill proposals

Default review age is 180 days. Stale records remain valid candidates until reviewed.

A workflow can be proposed as a Skill when it has at least three independent evidence objects, is not rejected or superseded, and has no `linked_skill`. Review whether the evidence really describes one reusable workflow before creating anything.

## 中文版本（CN）

### 偏好证据结构

使用 `docs/preferences/preferences.json` 作为规范账本。

这是项目本地账本。跨项目的用户全局账本应使用 `scripts/preference_tool.py --global-store` 解析的共享用户级位置；`USER_PREFERENCE_HOME` 覆盖项和各操作系统默认路径见 [cross-agent-installation.md](cross-agent-installation.md)。除非用户明确指定，否则不要混用项目本地账本和全局账本。

#### 必填记录字段

| 字段 | 含义 |
|---|---|
| `id` | 稳定、便于阅读的标识，例如 `WF-001`。 |
| `category` | 以下类别之一：`communication`、`documentation`、`coding`、`architecture`、`testing`、`workflow`、`scope`、`safety` 或 `decision`。 |
| `preference_key` | 用于冲突检测的稳定语义键。 |
| `value` | 规范化的取值。同一键存在两个有效取值时视为冲突。 |
| `description` | 面向人的偏好描述。 |
| `evidence` | 一个或多个简明证据对象。 |
| `confidence` | 0 到 1 之间的数值，表示证据强度。 |
| `scope` | 偏好适用范围及重要例外。 |
| `last_validated` | ISO 日期，格式为 `YYYY-MM-DD`。 |
| `confirmation_status` | `proposed`、`confirmed`、`rejected` 或 `superseded`。 |
| `conflicts_with` | 已知语义冲突的记录 ID 列表。 |
| `linked_skill` | 已有 Skill 名称，或 `null`。 |

每个证据对象必须包含 `source_type`、`source`、`observed_at` 和 `detail`。全局跨项目记录还可以包含 `source_project`。引用聊天时使用标题或范围明确的任务标识，并概述相关行为；不要复制整段私人消息。

#### 置信度参考

- `0.40–0.59`：单次且含义不明确的行为；只作为弱背景，不要据此制定操作规则。
- `0.60–0.79`：重复行为，或一条明确但仅适用于当前任务的指令。
- `0.80–0.89`：多个独立任务中重复出现，或有明确陈述和实际行为共同支持。
- `0.90–1.00`：明确表达、反复出现且近期经过验证。

置信度永远不会自动将 `proposed` 状态变为 `confirmed`。

#### 冲突规则

出现以下任一情况时，视为冲突：

1. 两条未被拒绝或取代的记录具有相同 `preference_key`，但 `value` 不同；或
2. 任一记录在 `conflicts_with` 中列出了另一条记录。

不要自动合并相互冲突的范围。先判断它们是真冲突，还是不同范围下都成立的情况。如果范围不同，应细化范围或键；如果范围重叠，应请用户确认，并在解决前保留双方记录。

#### 过期记录与 Skill 建议

默认复核周期为 180 天。过期记录仍是有效候选，直至完成复核。

当某个工作流至少有三个独立证据对象、未被拒绝或取代，且没有关联 `linked_skill` 时，可以考虑将其提议为 Skill。创建前先确认这些证据确实描述了同一个可复用流程。

