# user-preference-analyzer

This repository contains only the reusable `user-preference-analyzer` Agent Skill.

The Skill package is located at `skills/user-preference-analyzer/` and contains its `SKILL.md`, portable helper scripts, schema references, and Codex UI metadata.

No preference ledger, source authorization manifest, chat transcript, project report, credential, or other user data is included.

The Skill stores a cross-agent preference ledger outside this repository. Set `USER_PREFERENCE_HOME` to choose a shared local directory; otherwise, the helper uses the operating system's per-user data directory. See the Skill's cross-agent installation reference for exact paths and migration safeguards.

## 中文版本（CN）

此仓库仅包含可复用的 `user-preference-analyzer` Agent Skill。

Skill 包位于 `skills/user-preference-analyzer/`，包含 `SKILL.md`、可移植辅助脚本、数据结构说明和 Codex UI 元数据。

仓库不包含偏好账本、来源授权清单、聊天记录、项目报告、凭据或其他用户数据。

Skill 的跨 Agent 偏好账本保存在本仓库之外。可通过 `USER_PREFERENCE_HOME` 指定本机共享目录；未设置时，辅助脚本使用操作系统的用户数据目录。具体路径和迁移保护措施见 Skill 的跨 Agent 安装说明。
