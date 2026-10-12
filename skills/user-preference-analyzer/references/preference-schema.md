# Preference evidence schema

Use `docs/preferences/preferences.json` as the canonical registry.

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

