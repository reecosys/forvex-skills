# forVEX Skills

Claude Skills that turn Claude.ai into a real-estate-investment cockpit — deal pipeline, rehab estimating, project management, and underwriting — for HomeVestors franchisees and other operators using the forVEX platform.

## What's a Claude Skill?

A small markdown bundle that teaches Claude a domain-specific workflow. Once installed in Claude.ai, the skill activates automatically when you describe a matching task in chat.

## Two tiers

| Tier | Account needed? | Examples |
|---|---|---|
| **Demo** | No — runs on what you type | `forvex-mao`, `forvex-rehab-light`, `forvex-finish`, `forvex-postmortem` |
| **MCP-connected** | Yes — forVEX account + Control MCP OAuth | `forvex-rehab-estimator`, `forvex-underwriting`, the pipeline + project skills |

Demo skills are great for first-touch — try them without signing up.
MCP skills read and write your live deal pipeline via [control.forvex.app](https://control.forvex.app).

## Install

### Demo skills (anyone)

1. Download a `.skill` file from the [latest release](https://github.com/reecosys/forvex-skills/releases/latest).
2. Open Claude.ai → Settings → Capabilities → Skills → Upload.
3. Start a new chat and try the example prompt from that skill's `SKILL.md`.

### MCP-connected skills (forVEX account holders)

1. Sign in at [forvex.app](https://www.forvex.app) and follow the onboarding to connect the **forVEX Control** MCP in Claude.ai → Settings → Connectors.
2. Visit [forvex.app/install](https://www.forvex.app/install) for the gated install page, or download `.skill` files directly from a release here.
3. Upload each `.skill` to Claude.ai as above.

The easiest path is the install page — it shows you which skills you've got, what version, and groups them by lane (REDEAL, REBUILD, READVISE). Bundle membership is defined in `skills/SKILL_REGISTRY.json`.

## Layout

```
platform/references/     # shared docs vendored into every .skill at package time
  mcp-tools.md           # canonical MCP tool surface
  resolve-context.md     # address → deal_id resolution
  write-discipline.md    # echo-back, verify, idempotency
  skill-routing.md       # who owns which write tool
  forvex-frame.md        # HV framing (confidential)
  comp-evaluation.md     # comps / ARV rules

skills/
  SKILL_REGISTRY.json    # lanes, tools, handoffs, bundles (lint-enforced)
  forvex-<name>/
    SKILL.md             # required — frontmatter + workflow
    tier.txt             # "demo" or "mcp" (manifest only; not in zip)
    references/          # skill-specific supporting docs
    scripts/             # optional helper code
    templates/           # optional output templates
```

## Building locally

```bash
./package.sh                   # builds every skill into build/*.skill
./package.sh forvex-mao        # builds one
python3 scripts/lint-skills.py # registry + cross-ref checks
```

`.skill` files are zip archives. `package.sh` copies `platform/references/` into each skill as `references/platform/` so packaged skills never depend on `../other-skill/` paths.

## Governance

Cross-skill rules (identity, MCP topology, write discipline, routing) are defined in **`reecosystem-core/docs/SKILL_SYSTEM_CONTRACT.md`**. The machine-readable registry is **`skills/SKILL_REGISTRY.json`**. MCP tool names are validated against **`platform/mcp-tools.registry.json`** (sync from `recontrol` when tools change).

## Releases

Tagging triggers lint, package, and manifest build:

```bash
git tag v0.3.0
git push --tags
```

The `release` workflow packages every skill, generates `manifest.json` (with lanes, bundles, writes, handoffs), and attaches everything to a GitHub Release. forvex.app fetches `manifest.json` to render the install pages.

## Contributing

Internal: open a PR — CI runs `scripts/lint-skills.py` and script unit tests. External: open an issue first describing the workflow you want a skill for.

When changing an existing skill:

1. Update `skills/SKILL_REGISTRY.json` if tools, lane, or handoffs change.
2. Update `platform/mcp-tools.registry.json` if you add MCP tools (coordinate with recontrol).
3. Bump the next release tag and call out the change in the PR description.

## License

[MIT](./LICENSE) — feel free to fork and adapt.
