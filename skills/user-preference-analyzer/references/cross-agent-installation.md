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
