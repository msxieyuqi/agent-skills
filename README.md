# agent-skills

This repository contains reusable, portable Agent Skills:

- `skills/user-preference-analyzer/` — analyze authorized evidence and maintain evidence-backed user preferences.
- `skills/handoff-skill/` — create a concise, cross-agent `handoff.md` for resuming a task in a new conversation.

Each Skill package contains its `SKILL.md` and any supporting resources. Product-specific metadata is optional and may be ignored by other Agent Skills hosts.

No preference ledger, source authorization manifest, chat transcript, project report, credential, or other user data is included.

The user-preference-analyzer stores its cross-agent preference ledger outside this repository. Set `USER_PREFERENCE_HOME` to choose a shared local directory; otherwise, its helper uses the operating system's per-user data directory. See that Skill's cross-agent installation reference for exact paths and migration safeguards.

The user-preference-analyzer also supports on-request review of proposed preferences with confidence greater than `0.9`, followed by an explicitly user-selected batch decision. See its [manual review guide](skills/user-preference-analyzer/references/cross-agent-installation.md#manual-review). It does not automatically confirm inferred preferences.

## 中文版本（CN）

本仓库包含可复用、可移植的 Agent Skills：

- `skills/user-preference-analyzer/` — 分析已授权的证据，并维护有依据的用户偏好。
- `skills/handoff-skill/` — 创建精简、跨 Agent 的 `handoff.md`，帮助新对话续接任务。

每个 Skill 包含 `SKILL.md` 及其所需的配套资源。产品专属元数据是可选的，其他 Agent Skills 宿主可以忽略。

仓库不包含偏好账本、来源授权清单、聊天记录、项目报告、凭据或其他用户数据。

`user-preference-analyzer` 的跨 Agent 偏好账本保存在本仓库之外。可通过 `USER_PREFERENCE_HOME` 指定本机共享目录；未设置时，其辅助工具使用操作系统的用户数据目录。具体路径和迁移保护措施见该 Skill 的跨 Agent 安装说明。

`user-preference-analyzer` 支持按需查看置信度超过 `0.9` 的待确认偏好，再按照用户选择批量审核。调用方式见[人工审核说明](skills/user-preference-analyzer/references/cross-agent-installation.md#manual-review)；推断出的偏好不会自动确认。
