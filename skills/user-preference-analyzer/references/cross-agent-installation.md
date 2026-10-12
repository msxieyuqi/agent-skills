# Cross-agent installation and use

This Skill uses the portable Agent Skills layout: one directory named `user-preference-analyzer`, containing `SKILL.md`, `scripts/`, and `references/`. Keep the frontmatter `name` and folder name identical. The Codex-only `agents/openai.yaml` is optional metadata; other agents can ignore it.

## Supported global discovery locations

| Agent | Global Skill directory | How to install or refresh | Typical invocation |
|---|---|---|---|
| Codex | `~/.codex/skills/user-preference-analyzer/` (or `$CODEX_HOME/skills/`) | Run the installer with `--agent codex`. | `$user-preference-analyzer ...` |
| Zed | `~/.agents/skills/user-preference-analyzer/` | Run with `--agent zed`, then refresh AI Skills if needed. | `/user-preference-analyzer ...` or `@user-preference-analyzer ...` |
| ZCode | `~/.zcode/skills/user-preference-analyzer/` | Run with `--agent zcode`, then Settings → Skills → Refresh and enable it. ZCode can also import the Codex Skill as a copy or symlink and target Global. | `$user-preference-analyzer ...` or `/user-preference-analyzer ...` |
| DeepSeek Harness | `~/.dsh/skills/user-preference-analyzer/` and shared `~/.agents/skills/` | Run with `--agent deepseek-harness`. Its filesystem provider scans both the DSH home and shared Agent Skills home by default. | Invoke the `user-preference-analyzer` skill through the harness skill catalog/tool or its configured `/name` shortcut. |

Zed and DeepSeek Harness both read the shared `~/.agents/skills/` root. Codex and ZCode use their own user-level roots, so install each if those tools are expected to discover it. DeepSeek Harness may use `DSH_HOME` or `DSH_AGENTS_HOME` overrides; the installer honors these environment variables.

## Install from this Skill package

From the directory that contains the Skill package:

```sh
python3 scripts/install_skill.py --agent all
```

Choose one destination when needed:

```sh
python3 scripts/install_skill.py --agent zcode
python3 scripts/install_skill.py --agent deepseek-harness
python3 scripts/install_skill.py --agent zed
python3 scripts/install_skill.py --agent codex
```

The installer only writes this Skill's destination folder. It creates a dated backup before replacing an existing install. Use `--dry-run` to preview paths and `--source PATH` when running the installer from outside this Skill folder.

If you already have this Skill under Codex and use ZCode, ZCode's Settings → Skills → Import can import from the Codex directory. Choose Global and either Copy or Symlink, then enable the imported Skill. Copy keeps an independent version; Symlink follows later source edits while the source path remains available.

## Global preference ledger

All agents on the same machine should use the same ledger:

```text
$CODEX_HOME/user-preferences/
└── preferences.json
```

When `CODEX_HOME` is unset, the default is `~/.codex/user-preferences/`. Do not create separate ledgers under `.agents`, `.zcode`, or `.dsh`; per-tool ledgers would diverge. Each analysis agent must be able to read and write the configured shared ledger, and must use the installed Skill's `scripts/preference_tool.py`.

On a new machine, copy the ledger and `SOURCES.md` only through an explicitly authorized local transfer. Do not upload private conversations to install a Skill. Skill installation moves reusable instructions and scripts; it does not move preference data.

## Runtime behavior and limitations

- The skill folder is portable, but invocation syntax and global directories vary by harness.
- The helper script requires Python 3 and local filesystem access to the shared ledger.
- The Skill cannot grant a harness filesystem permission it does not already have. If the agent cannot access the shared ledger, use that harness's approved local-filesystem configuration or generate project-local outputs.
- Some harnesses snapshot the skill catalog when a session starts. If a newly installed Skill does not appear, refresh the Skills UI or open a new session.
- DeepSeek Harness's `skill-filesystem` provider searches its documented local roots and supports `SKILL.md` bundles; its project and user roots can be customized.
- Zed's global Skills apply to Zed Agent; external agents and terminal threads may require their own installation.

## Official references

- [Codex Skill format and install paths](https://developers.openai.com/codex/skills)
- [Zed Skills](https://zed.dev/docs/ai/skills)
- [ZCode Skills](https://zcode.z.ai/en/docs/skill)
- [DeepSeek Harness filesystem Skill provider](https://github.com/deepseek-ai/deepseek-harness/tree/master/packages/skill/skill-filesystem)

## 中文版本（CN）

### 跨 Agent 安装与使用

本 Skill 使用可移植的 Agent Skills 目录布局：一个名为 `user-preference-analyzer` 的目录，内含 `SKILL.md`、`scripts/` 和 `references/`。frontmatter 中的 `name` 必须与目录名一致。仅供 Codex 使用的 `agents/openai.yaml` 是可选元数据，其他 Agent 可以忽略。

#### 支持的全局发现位置

| Agent | 全局 Skill 目录 | 安装或刷新方式 | 常见调用方式 |
|---|---|---|---|
| Codex | `~/.codex/skills/user-preference-analyzer/`（或 `$CODEX_HOME/skills/`） | 使用安装器的 `--agent codex`。 | `$user-preference-analyzer ...` |
| Zed | `~/.agents/skills/user-preference-analyzer/` | 使用 `--agent zed` 安装；必要时刷新 AI Skills。 | `/user-preference-analyzer ...` 或 `@user-preference-analyzer ...` |
| ZCode | `~/.zcode/skills/user-preference-analyzer/` | 使用 `--agent zcode` 安装，然后进入 Settings → Skills → Refresh 并启用。ZCode 也可将 Codex Skill 作为副本或符号链接导入，并选择 Global。 | `$user-preference-analyzer ...` 或 `/user-preference-analyzer ...` |
| DeepSeek Harness | `~/.dsh/skills/user-preference-analyzer/` 和共享的 `~/.agents/skills/` | 使用 `--agent deepseek-harness` 安装。其文件系统提供方默认会扫描 DSH 主目录和共享 Agent Skills 目录。 | 通过 Harness 的 Skill 目录/工具，或已配置的 `/name` 快捷方式调用。 |

Zed 与 DeepSeek Harness 都读取共享的 `~/.agents/skills/` 根目录。Codex 和 ZCode 使用各自的用户级根目录；如果希望这些工具发现该 Skill，请分别安装。DeepSeek Harness 可能通过 `DSH_HOME` 或 `DSH_AGENTS_HOME` 覆盖默认路径，安装器会遵循这些环境变量。

#### 从 Skill 包安装

在包含 Skill 包的目录中运行：

```sh
python3 scripts/install_skill.py --agent all
```

需要时可指定单个目标：

```sh
python3 scripts/install_skill.py --agent zcode
python3 scripts/install_skill.py --agent deepseek-harness
python3 scripts/install_skill.py --agent zed
python3 scripts/install_skill.py --agent codex
```

安装器只写入该 Skill 的目标目录。替换已有安装前会创建带日期的备份。可使用 `--dry-run` 预览路径；从 Skill 目录外运行时，使用 `--source PATH` 指定来源。

如果你已在 Codex 中安装本 Skill，且希望在 ZCode 中使用，可在 ZCode 的 Settings → Skills → Import 中从 Codex 目录导入。选择 Global，并选择 Copy 或 Symlink，然后启用。Copy 会创建独立副本；Symlink 会跟随源目录后续的更改，但要求源路径始终可用。

#### 全局偏好账本

同一台机器上的所有 Agent 应使用同一个账本：

```text
$CODEX_HOME/user-preferences/
└── preferences.json
```

若未设置 `CODEX_HOME`，默认路径为 `~/.codex/user-preferences/`。不要在 `.agents`、`.zcode` 或 `.dsh` 下创建各自的账本副本，否则不同 Agent 的数据会分叉。每个分析 Agent 都必须具备访问已配置共享账本的本地权限，并调用已安装 Skill 中的 `scripts/preference_tool.py`。

在新设备上，只有经过明确授权的本地传输才可以复制账本和 `SOURCES.md`。安装 Skill 时不要上传私人聊天。Skill 安装传输的是可复用说明和脚本，不传输偏好数据。

#### 运行条件与限制

- Skill 目录格式可移植，但不同 Harness 的调用语法和全局目录可能不同。
- 辅助脚本需要 Python 3 和对共享账本的本地文件访问权限。
- Skill 无法授予 Harness 原本不具备的文件访问权限。如果 Agent 无法访问共享账本，应使用该 Harness 获准的本地文件配置，或生成项目本地结果。
- 有些 Harness 会在会话启动时缓存 Skill 目录。如果新安装的 Skill 未出现，请刷新 Skills 界面或新开会话。
- DeepSeek Harness 的 `skill-filesystem` 提供方会搜索其文档说明的本地路径，并支持包含 `SKILL.md` 的目录包；项目级和用户级路径都可以自定义。
- Zed 的全局 Skills 对 Zed Agent 生效；外部 Agent 和终端会话可能需要单独安装。

#### 官方参考

- [Codex Skill 格式和安装路径](https://developers.openai.com/codex/skills)
- [Zed Skills](https://zed.dev/docs/ai/skills)
- [ZCode Skills](https://zcode.z.ai/en/docs/skill)
- [DeepSeek Harness 文件系统 Skill 提供方](https://github.com/deepseek-ai/deepseek-harness/tree/master/packages/skill/skill-filesystem)
