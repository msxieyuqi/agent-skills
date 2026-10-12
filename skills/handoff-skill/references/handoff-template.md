# Task Handoff: <project or task name>

> Purpose: Let an agent without this conversation verify the current state and resume the task.
> Updated: <YYYY-MM-DD>

## Instructions for the next conversation

- Read first: <project rules, entry points, and relevant state files; use relative paths>
- Verify: <workspace/code/data/external state that must be rechecked>
- Resume: Verify the current files, then continue from “Next steps”; do not assume this handoff still matches the workspace.

## Project and task goals

- Project context: <minimum background needed>
- Current task: <goal>
- Completion criteria: <checkable acceptance conditions>
- Scope boundaries: <what is explicitly out of scope; otherwise “No additional boundaries”>

## Current status

- Phase: discovery / design / implementation / verification / paused / complete
- Completed: <confirmed results>
- Remaining: <unfinished work>
- Changed files or artifacts: <relative paths, or “None”>
- Verification and results: <checks run and evidence; explicitly say “Not run” when applicable>

## Key decisions and historical outcomes

- <date> — Decision: <important decision and any still-relevant rationale>
- <date> — Outcome: <milestone or final result worth carrying forward>

Keep only decisions and outcomes that affect future work. Do not include turn-by-turn conversation or paste earlier handoffs. Write “None yet” when empty.

## Blockers and open questions

- Blockers: <issue and impact, or “None”>
- Required permission, input, or user decision: <specific request, or “None”>

## Next steps and stop condition

- Smallest next action: <one concrete action>
- Verification: <how to check the action>
- Stop condition: <when the task is complete; if paused, state what is needed to resume>

## Boundaries and evidence

- Rules to follow: <permissions, compatibility constraints, protected areas, etc.>
- Key evidence or references: <relative paths, test reports, issue/PR IDs, or external links; or “None”>

---

**Generic opening instruction for the next agent:** Read the project rules and evidence paths listed here, then check whether the current workspace still matches this handoff. Prefer current files and verifiable results when they differ from this document, and note the discrepancy. Continue from “Smallest next action” while respecting the scope and stop condition. Ask the user before making a missing high-impact decision or taking an action that requires additional permission.

## 中文版本（CN）

本节是上述英文模板的中文版本；两种语言字段含义一致。生成 `handoff.md` 时选择一种语言即可，不要把两套模板同时复制进交接文件。

# 任务交接：<项目或任务名称>

> 用途：让没有当前对话上下文的新 Agent 核验现状后继续任务。
> 更新于：<YYYY-MM-DD>

## 新对话恢复指引

- 先阅读：<项目规则、入口文档和相关状态文件；使用相对路径>
- 再核验：<必须复查的工作区/代码/数据/外部状态>
- 恢复方式：核验当前文件后，从“下一步最小动作”继续；不要假设本交接仍与当前工作区一致。

## 项目与任务目标

- 项目背景：<理解任务所需的最少背景>
- 当前任务：<目标>
- 完成标准：<可检查的验收条件>
- 范围边界：<明确不做什么；无则写“无额外边界”>

## 当前状态

- 阶段：调查 / 设计 / 实施 / 验证 / 暂停 / 完成
- 已完成：<已确认的成果>
- 尚未完成：<未完成项>
- 修改文件或产物：<相对路径；无则写“无”>
- 验证及结果：<已运行的检查和证据；未运行时明确写“未运行”>

## 关键决策与历史结果

- <日期> — 决策：<重要决定及仍有效的理由>
- <日期> — 结果：<值得保留的里程碑或最终结果>

只保留会影响后续工作的决策和结果；不记录逐轮对话，不粘贴旧版交接全文。无历史时写“暂无”。

## 阻塞与待确认

- 阻塞：<问题及影响；无则写“无”>
- 需要的权限、输入或用户决定：<具体内容；无则写“无”>

## 下一步与停止条件

- 下一步最小动作：<一个具体动作>
- 验证方式：<如何确认该动作有效>
- 停止条件：<何时视为完成；若暂停，写明恢复条件>

## 工作边界与依据

- 必须遵守的规则：<权限、兼容性约束、不可修改区域等>
- 关键证据或参考路径：<相对路径、测试报告、Issue/PR 编号或外部链接；无则写“无”>

---

**给新 Agent 的通用开场指令：**请先阅读本文件列出的项目规则和证据路径，再核对当前工作区是否仍符合交接状态。若与本文件不同，以当前文件和可验证结果为准并注明差异。随后在遵守范围和停止条件的前提下，从“下一步最小动作”继续；遇到缺失的重大决策或需要额外权限的操作时先询问用户。
