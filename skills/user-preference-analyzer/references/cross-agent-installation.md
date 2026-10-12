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
<shared per-user data directory>/user-preferences/
└── preferences.json
```

`USER_PREFERENCE_HOME` can explicitly set the ledger directory on any operating system; it must point to the same directory for every Agent. If unset, the helper uses these defaults:

| Operating system | Default directory |
|---|---|
| macOS | `~/Library/Application Support/user-preferences/` |
| Windows | `%LOCALAPPDATA%\user-preferences\` |
| Linux / other Unix | `${XDG_DATA_HOME:-~/.local/share}/user-preferences/` |

The registry is `preferences.json`; `SOURCES.md` and generated reports live beside it. `CODEX_HOME` controls Codex Skill discovery only and is not used to locate the shared ledger. Do not create separate ledgers under `.agents`, `.zcode`, `.dsh`, or another Agent's home; per-tool ledgers would diverge. Each analysis Agent must have local read/write permission to the resolved shared directory and must use the installed Skill's `scripts/preference_tool.py`.

On a first setup, initialize the shared store only when the user requests setup. If a legacy `~/.codex/user-preferences/` exists and differs from the resolved path, ask before migrating it; never silently copy it or create a parallel ledger. A custom shared path can be selected by setting `USER_PREFERENCE_HOME` consistently in each Agent's environment.

On a new machine, copy the ledger and `SOURCES.md` only through an explicitly authorized local transfer. Do not upload private conversations to install a Skill. Skill installation moves reusable instructions and scripts; it does not move preference data.

## Runtime behavior and limitations

- The skill folder is portable, but invocation syntax and global directories vary by harness.
- The helper script requires Python 3 and local filesystem access to the shared ledger.
- The Skill cannot grant a harness filesystem permission it does not already have. If the agent cannot access the shared ledger, use that harness's approved local-filesystem configuration or generate project-local outputs.
- Some harnesses snapshot the skill catalog when a session starts. If a newly installed Skill does not appear, refresh the Skills UI or open a new session.
- DeepSeek Harness's `skill-filesystem` provider searches its documented local roots and supports `SKILL.md` bundles; its project and user roots can be customized.
- Zed's global Skills apply to Zed Agent; external agents and terminal threads may require their own installation.

## Manual review

In any installed Agent, ask: “查看置信度超过 0.9 的待确认偏好”. The Agent displays a concise list only on request, without a supporting-project list. Reply with record IDs, for example: “确认 PF-001；拒绝 PF-002；PF-003 仅限当前项目；PF-004 暂缓”. A scope-only change does not confirm the record.

From the installed Skill directory, inspect a project ledger or the shared global ledger:

```sh
python3 scripts/preference_tool.py --root /path/to/project review
python3 scripts/preference_tool.py --global-store review --format json
```

`review` defaults to readable text. JSON returns `version`, `policy`, and `candidates`. Each candidate contains ID, description, value, confidence, proposed status, evidence summary (at most 100 characters), scope, last validation date, active conflict IDs, and a stale flag. The filter is strictly `> 0.9`, not `>= 0.9`; records are sorted by confidence descending, then ID. Staleness uses 180 days. This command does not write the ledger.

The Agent retains the version of the list actually shown and writes only the user's choices to a local temporary JSON file. Example input (illustrative IDs and scopes):

```json
[
  {"id": "PF-001", "action": "confirm"},
  {"id": "PF-002", "action": "reject"},
  {"id": "PF-003", "scope": "Only the current project: Example Project"},
  {"id": "PF-004", "action": "defer"}
]
```

Omitting `action` while supplying `scope` changes scope only. `confirm` may also include a new scope if the user explicitly requested both. `defer` cannot include a scope change. Submit with the full returned version (replace the example version and file path):

```sh
python3 scripts/preference_tool.py --global-store review-decide \
  --decisions /path/to/local/review-decisions.json \
  --expected-version 'FULL_VERSION_FROM_THE_SHOWN_LIST'
```

For a project ledger, replace `--global-store` with `--root /path/to/project`. The response contains changed IDs and the resulting version. Unselected records stay unchanged; defer-only batches do not write anything. Confirmation writes user provenance and time without refreshing evidence dates. Unknown/duplicate IDs, invalid choices, or attempts to confirm conflicted records reject the entire batch. Resolve conflicts explicitly, then refresh the list before confirmation. If the ledger changed since display, show a fresh list and ask for new choices; never silently reuse the old choices against a new version.

All mutating commands use a shared `.preferences.json.lock` beside the ledger and atomic file replacement, waiting at most five seconds. Refresh old Skill installs before concurrent use; older scripts do not honor this lock. If a process was forcibly terminated and left a lock, verify no writer is running before removing that exact stale lock. Review does not create report files or run automatically after analysis. Decision files, registry snapshots, and test ledgers are local runtime data and must not be uploaded with the Skill.

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
<同一用户的数据目录>/user-preferences/
└── preferences.json
```

任何操作系统都可以通过 `USER_PREFERENCE_HOME` 显式指定账本目录；所有 Agent 必须解析到同一个目录。未设置时，辅助脚本使用以下默认值：

| 操作系统 | 默认目录 |
|---|---|
| macOS | `~/Library/Application Support/user-preferences/` |
| Windows | `%LOCALAPPDATA%\user-preferences\` |
| Linux / 其他 Unix | `${XDG_DATA_HOME:-~/.local/share}/user-preferences/` |

账本文件为 `preferences.json`；`SOURCES.md` 和生成的报告与它放在同一目录。`CODEX_HOME` 仅控制 Codex Skill 的发现位置，不用于定位共享账本。不要在 `.agents`、`.zcode`、`.dsh` 或其他 Agent 的专属目录创建账本副本，否则数据会分叉。每个分析 Agent 都必须具备对解析后共享目录的本地读写权限，并调用已安装 Skill 中的 `scripts/preference_tool.py`。

首次设置时，只有用户明确要求初始化才创建共享账本。如果存在旧版 `~/.codex/user-preferences/` 且它与解析出的目录不同，迁移前必须询问；不得静默复制或创建并行账本。可以通过在每个 Agent 的运行环境中一致地设置 `USER_PREFERENCE_HOME` 来指定自定义共享路径。

在新设备上，只有经过明确授权的本地传输才可以复制账本和 `SOURCES.md`。安装 Skill 时不要上传私人聊天。Skill 安装传输的是可复用说明和脚本，不传输偏好数据。

#### 运行条件与限制

- Skill 目录格式可移植，但不同 Harness 的调用语法和全局目录可能不同。
- 辅助脚本需要 Python 3 和对共享账本的本地文件访问权限。
- Skill 无法授予 Harness 原本不具备的文件访问权限。如果 Agent 无法访问共享账本，应使用该 Harness 获准的本地文件配置，或生成项目本地结果。
- 有些 Harness 会在会话启动时缓存 Skill 目录。如果新安装的 Skill 未出现，请刷新 Skills 界面或新开会话。
- DeepSeek Harness 的 `skill-filesystem` 提供方会搜索其文档说明的本地路径，并支持包含 `SKILL.md` 的目录包；项目级和用户级路径都可以自定义。
- Zed 的全局 Skills 对 Zed Agent 生效；外部 Agent 和终端会话可能需要单独安装。

#### 人工审核

在任意已安装的 Agent 中说：“查看置信度超过 0.9 的待确认偏好”。Agent 只在你请求时返回精简清单，不列出支持证据的项目。可以回复：“确认 PF-001；拒绝 PF-002；PF-003 仅限当前项目；PF-004 暂缓”。仅修改范围不代表确认。

从已安装 Skill 的目录运行以下命令，分别查看项目账本或共享全局账本：

```sh
python3 scripts/preference_tool.py --root /path/to/project review
python3 scripts/preference_tool.py --global-store review --format json
```

`review` 默认输出便于阅读的文字；JSON 返回 `version`、`policy` 和 `candidates`。每条候选包含编号、描述、取值、置信度、待确认状态、最多 100 字的证据摘要、范围、验证日期、有效冲突编号和过期提示。筛选是严格 `> 0.9`，不是 `>= 0.9`；按置信度降序、编号升序排列，超过 180 天未验证时提示留意。这个命令不修改账本。

Agent 保存你实际看到的清单版本，只把你选中的操作写到本机临时 JSON 文件。以下编号和范围仅作示例：

```json
[
  {"id": "PF-001", "action": "confirm"},
  {"id": "PF-002", "action": "reject"},
  {"id": "PF-003", "scope": "仅当前项目：示例项目"},
  {"id": "PF-004", "action": "defer"}
]
```

只提供 `scope` 而省略 `action`，表示仅修改范围。用户明确要求同时确认和改范围时，`confirm` 也可附带 `scope`；暂缓 `defer` 不能同时改范围。使用清单返回的完整版本提交，替换示例中的版本和文件路径：

```sh
python3 scripts/preference_tool.py --global-store review-decide \
  --decisions /path/to/local/review-decisions.json \
  --expected-version 'FULL_VERSION_FROM_THE_SHOWN_LIST'
```

项目账本把 `--global-store` 换成 `--root /path/to/project`。命令返回已修改的编号和新版本。没选的保持原样；全部暂缓时不写入。确认只记下你的选择和时间，不把证据日期改成今天。编号写错、重复选择、操作不合法或确认尚有冲突的记录时，整批先不保存。先明确解决冲突，再刷新清单确认。若其他 Agent 改过账本，应重新展示清单让你选择，不能把旧选择偷偷套用到新内容上。

所有写入命令使用账本旁的 `.preferences.json.lock` 排队，再一次性保存，最多等待五秒。并发使用前先刷新旧安装，否则旧脚本不会参与排队。如果进程被强制结束后留下锁文件，确认没有写入任务运行后再移除那一个残留锁。审核不创建报告文件，也不在日常分析后自动运行。选择文件、账本快照和测试账本是本机运行数据，不随 Skill 上传。

#### 官方参考

- [Codex Skill 格式和安装路径](https://developers.openai.com/codex/skills)
- [Zed Skills](https://zed.dev/docs/ai/skills)
- [ZCode Skills](https://zcode.z.ai/en/docs/skill)
- [DeepSeek Harness 文件系统 Skill 提供方](https://github.com/deepseek-ai/deepseek-harness/tree/master/packages/skill/skill-filesystem)
