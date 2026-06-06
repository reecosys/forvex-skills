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

The easiest path is the install page — it shows you which skills you've got, what version, and groups them by lane (REDEAL, REBUILD, READVISE).

## Layout

```
skills/
  forvex-<name>/
    SKILL.md           # required — frontmatter + workflow
    tier.txt           # "demo" or "mcp"
    references/        # optional supporting docs the skill loads on demand
    scripts/           # optional helper code
    templates/         # optional output templates
```

## Building locally

```bash
./package.sh                   # builds every skill into build/*.skill
./package.sh forvex-mao        # builds one
```

`.skill` files are just zip archives renamed — Claude.ai's upload accepts the extension for one-click install.

## Releases

Tagging triggers an automated build:

```bash
git tag v0.1.0
git push --tags
```

The `release` workflow packages every skill, generates `manifest.json`, and attaches everything to a GitHub Release. forvex.app fetches `manifest.json` to render the install pages — no code change needed when a new skill ships.

## Contributing

Internal: open a PR. External: open an issue first describing the workflow you want a skill for.

When changing an existing skill, bump the next release tag and call out the change in the PR description.

## License

[MIT](./LICENSE) — feel free to fork and adapt.
