# handoff-skill

A portable Agent Skill that creates or updates a concise project-root `handoff.md` when explicitly invoked, so another agent can resume the task in a new conversation.

The core follows the Agent Skills folder format and has no runtime dependency on Obsidian, CyberBrain, MCP, network services, or a specific agent product. Installation paths, reload behavior, explicit invocation syntax, and filesystem access vary by host; compatibility with the format does not guarantee identical behavior in every agent.

## Package contents

- `SKILL.md` — workflow, boundaries, and safety requirements.
- `references/handoff-template.md` — bilingual source template. Generated handoffs should use one language, not duplicate both versions.
- `agents/openai.yaml` — optional Codex-specific UI and explicit-invocation metadata; other hosts may ignore it.

## Installation

### Codex (user scope)

Copy the entire `handoff-skill` folder to the Codex user-level Skills directory:

- If `CODEX_HOME` is set: `$CODEX_HOME/skills/handoff-skill/`
- Otherwise: `~/.codex/skills/handoff-skill/`

Keep `SKILL.md` at the package root and include `references/handoff-template.md`. If it does not appear in the Skills list, refresh Skills or restart Codex as supported by your version.

This package is currently installed at `~/.codex/skills/handoff-skill/` on the authoring machine.

### Other Agent Skills hosts

1. Consult the target agent's official documentation for its user/global Skill directory or import feature.
2. Copy the complete `handoff-skill` directory there, or use the host's importer. Keep the supporting `references/` directory.
3. Refresh/reload Skills if the host requires it.
4. If supported, configure explicit invocation; use the host's documented setting and syntax.

The folder uses the portable Agent Skills convention, but not every agent supports the same metadata, installation location, invocation controls, or local file operations. `agents/openai.yaml` is Codex-specific and optional.

## Use

In Codex, explicitly invoke:

```text
$handoff-skill
```

You may add a focused preference, for example: `$handoff-skill, emphasize acceptance criteria and unverified work.` The Skill creates or updates `handoff.md` at the current project root by default. In other agents, explicitly select or name `handoff-skill` using that host's supported mechanism.

The next conversation must also receive the resulting `handoff.md` and have access to the project/workspace. Paste or attach the file, or provide a path the next agent can access. The Skill does not transmit files, permissions, or the complete conversation across agents.

## Constraints

- In Codex, implicit invocation is disabled. On other hosts, explicit-only behavior depends on the host's settings; configure it when available. If the host loads the Skill implicitly without an explicit user invocation, the Skill instructions require it to do nothing.
- Writes only `handoff.md` at a clearly identified project root. If the root is ambiguous, multiple projects are plausible, or the location is not writable, ask before writing.
- Record verifiable state. Mark missing evidence as unknown or “not run”; never present plans as completed work.
- Keep history to consequential decisions and milestone/final outcomes. Do not append conversation transcripts or create a separate archive.
- Do not modify other project files, continue the underlying task, send messages, or call external services as part of handoff generation.
- Do not include passwords, tokens, credentials, unrelated personal data, or hidden reasoning.
- Follow the host's permission boundaries and higher-priority instructions. If the handoff conflicts with current workspace evidence, prefer the verified current state and note the discrepancy.

## 中文版本（CN）

本节是上述英文说明的中文版本；两种语言表达相同的行为边界和使用要求。文件名、路径和命令保持原样。

# handoff-skill

这是一个可移植的 Agent Skill。显式调用时，它会创建或更新项目根目录的精简 `handoff.md`，帮助另一个 Agent 在新对话中续接任务。

Skill 核心遵循 Agent Skills 目录格式，不依赖 Obsidian、CyberBrain、MCP、网络服务或特定 Agent 产品。不同宿主的安装路径、刷新方式、显式调用语法和文件访问能力可能不同；格式兼容不代表所有 Agent 的行为完全一致。

## 包含内容

- `SKILL.md` — 工作流程、适用边界与安全要求。
- `references/handoff-template.md` — 中英双语模板来源。生成交接文档时选择一种语言，不要将两种版本重复放入同一份文档。
- `agents/openai.yaml` — 可选的 Codex 专属界面和显式调用元数据；其他宿主可以忽略。

## 安装

### Codex（用户级）

将整个 `handoff-skill` 文件夹复制到 Codex 用户级 Skills 目录：

- 如果设置了 `CODEX_HOME`：`$CODEX_HOME/skills/handoff-skill/`
- 否则：`~/.codex/skills/handoff-skill/`

确保 `SKILL.md` 位于包根目录，并一并保留 `references/handoff-template.md`。如果 Skill 未出现在列表中，按当前版本支持的方式刷新 Skills 或重启 Codex。

本包目前安装在作者机器的 `~/.codex/skills/handoff-skill/`。

### 其他支持 Agent Skills 的宿主

1. 查看目标 Agent 的官方说明，确定其用户级/全局 Skill 目录或导入功能。
2. 将整个 `handoff-skill` 目录复制到该位置，或使用宿主提供的导入功能；保留配套的 `references/` 目录。
3. 如果宿主要求刷新/重新加载 Skills，请按其说明操作。
4. 若宿主支持显式调用控制，请按其文档配置，并使用对应的调用语法。

该目录采用可移植的 Agent Skills 约定，但并非所有 Agent 都支持相同的元数据、安装位置、调用控制或本地文件操作。`agents/openai.yaml` 是可选的 Codex 专属配置。

## 使用

在 Codex 中显式调用：

```text
$handoff-skill
```

也可附加具体偏好，例如：`$handoff-skill，请重点记录验收标准和未验证事项。` 默认在当前项目根目录创建或更新 `handoff.md`。在其他 Agent 中，请通过其支持的机制显式选择或调用 `handoff-skill`。

新对话还必须获得生成的 `handoff.md` 和项目/工作区访问权限。可粘贴或附加该文件，也可提供新 Agent 能访问的路径。Skill 不会跨 Agent 传输文件、授予权限或恢复完整聊天记录。

## 使用约束

- Codex 中已关闭隐式调用。其他宿主能否设置为仅显式调用取决于其配置；若支持，请启用该设置。即使宿主隐式加载本 Skill，只要用户没有显式调用，Skill 指令要求不执行任何操作。
- 只在项目根目录明确时创建或更新 `handoff.md`。如果根目录不明确、存在多个候选项目或目录不可写，应先询问。
- 只记录可验证的状态。证据缺失时标为未知或“未运行”；不得把计划写成已完成。
- 历史只保留重要决策和里程碑/最终结果。不追加对话全文，也不创建单独归档。
- 交接过程中不修改其他项目文件、不继续底层任务、不发送消息、不调用外部服务。
- 不得包含密码、Token、凭据、无关个人数据或隐藏推理。
- 遵守宿主 Agent 的权限边界和更高优先级指令。若交接文档与当前工作区证据冲突，以当前已核实状态为准并注明差异。
