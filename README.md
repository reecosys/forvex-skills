# forVEX Skills

Claude Skills that turn Claude.ai into a real-estate-investment cockpit — deal pipeline, rehab estimating, project management, and underwriting — for franchise and multi-market operators using the forVEX platform.

## What's a Claude Skill?

A small markdown bundle that teaches Claude a domain-specific workflow. Once installed in Claude.ai, the skill activates automatically when you describe a matching task in chat.

## Two tiers

| Tier | Account needed? | Examples |
|---|---|---|
| **Demo** | No — runs on what you type | `forvex-mao`, `forvex-rehab-light`, `forvex-finish`, `forvex-postmortem`, `accountability-partner` |
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
platform/references/       # shared docs; each skill gets exactly the ones it declares
  skill-routing-public.md  # public — routing across the standalone skills
  write-discipline.md      # public — echo-back, verify, idempotency
  skill-routing.md         # internal — who owns which write tool
  resolve-context.md       # internal — address → deal_id resolution
  mcp-tools.md             # internal — canonical MCP tool surface
  comp-evaluation.md       # internal — comps / ARV rules
  forvex-frame.md          # internal — forVEX framing (confidential)

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

`.skill` files are zip archives. `package.sh` copies platform references into each skill as `references/platform/` so packaged skills never depend on `../other-skill/` paths.

### Platform ref visibility — demo vs MCP

Each skill is vendored **exactly** the refs it declares in its `platform_refs`. Nothing is copied implicitly, because the two tiers have very different blast radii:

| Tier | Who can get the `.skill` | May declare |
|---|---|---|
| **demo** | Anyone — public GitHub Release, linked from forvex.app | `public` refs only |
| **mcp** | Account holders, inside the Claude Teams workspace | any ref |

Every file in `platform/references/` is classified `public` or `internal` under `platform_ref_visibility` in `skills/SKILL_REGISTRY.json`. Internal refs carry things that must not ship publicly — forVEX framing and thresholds, the MCP tool surface, comp methodology, internal service paths.

Three rules are enforced by `scripts/lint-skills.py` **and** by `package.sh`, so a mistake fails CI rather than shipping:

1. A demo-tier skill declaring an `internal` ref fails the build.
2. A file in `platform/references/` with no visibility entry fails the build.
3. A ref used in a skill's markdown but not declared fails the build — since only declared refs are vendored, an undeclared one would be a dead link inside the packaged skill.

When adding a platform ref, classify it in the same commit. When a demo skill needs routing guidance, point it at `skill-routing-public.md` — never at `skill-routing.md`, which names MCP write tools.

## Publishing the demo skills to forvex.app

Demo bundles are hosted on **forvex.app**, not GitHub Releases. Serving public downloads from a release ties them to repo visibility — making this repo private 404s every public URL, including the `manifest.json` the install page renders from. The site owning its own assets cuts that dependency.

```bash
./scripts/publish-demo-bundles.sh --dest ../reecosystem-web/public/skills
```

Builds `build/public-skills/` — the five demo `.skill` files plus a `manifest.json` whose **demo** `download_url`s point at `https://forvex.app/skills/<id>.skill`. Run it after tagging a release; commit the result in the site repo. Total payload is ~88K.

The script runs `lint-skills.py` and `package.sh` first, so the visibility gates apply, then re-verifies the built zips carry no internal refs before writing the payload. It fails rather than publishing a leak.

MCP entries in that manifest still point at GitHub Releases, so the gated install page keeps working unchanged. **If this repo is ever made private, those URLs stop resolving for everyone** — MCP distribution then needs its own answer, which this script deliberately does not decide.

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

1. Update `skills/SKILL_REGISTRY.json` if tools, lane, handoffs, or `platform_refs` change.
2. Update `platform/mcp-tools.registry.json` if you add MCP tools (coordinate with recontrol).
3. Bump the next release tag and call out the change in the PR description.

## License

[MIT](./LICENSE) — feel free to fork and adapt.
