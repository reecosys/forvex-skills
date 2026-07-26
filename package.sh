#!/usr/bin/env bash
# Package skill folders into .skill files (zip archives Claude.ai recognizes).
#
# Usage:
#   ./package.sh                   # package every skill
#   ./package.sh forvex-mao        # package a single skill
#
# Output: build/<skill-name>.skill
#
# Platform references from platform/references/ are vendored into each skill as
# references/platform/ before zipping (fixes cross-skill ../ paths at runtime).

set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILLS_DIR="${REPO_DIR}/skills"
PLATFORM_REFS_DIR="${REPO_DIR}/platform/references"
REGISTRY="${SKILLS_DIR}/SKILL_REGISTRY.json"
BUILD_DIR="${REPO_DIR}/build"
mkdir -p "${BUILD_DIR}"

discover_skills() {
    find "${SKILLS_DIR}" -mindepth 2 -maxdepth 2 -name SKILL.md -print0 \
        | xargs -0 -n1 dirname \
        | xargs -n1 basename
}

# Which platform refs go into this skill's zip.
#
# Every skill — both tiers — gets EXACTLY the refs it declares in
# SKILL_REGISTRY.json. Nothing is vendored implicitly.
#
# demo-tier .skill files are downloadable by anyone from a public GitHub
# Release, so a demo skill may only declare refs marked "public" in
# platform_ref_visibility. Internal refs (forvex-frame's HV framing, the MCP
# tool surface, comp methodology, resolve-context) never leave the Teams
# workspace. This function hard-fails the build rather than silently dropping
# a ref — a quiet drop would ship a skill whose governance doc is missing.
platform_refs_for() {
    local skill="$1"
    python3 - "$skill" "$REGISTRY" <<'PY'
import json, sys
skill, registry_path = sys.argv[1], sys.argv[2]
registry = json.load(open(registry_path))
meta = registry["skills"].get(skill)
if meta is None:
    sys.exit(f"{skill}: not in SKILL_REGISTRY.json")

visibility = {k: v for k, v in registry.get("platform_ref_visibility", {}).items()
              if not k.startswith("_")}
refs = meta.get("platform_refs", [])
tier = meta.get("tier", "mcp")

unclassified = [r for r in refs if r not in visibility]
if unclassified:
    sys.exit(f"{skill}: platform refs missing a platform_ref_visibility entry: {unclassified}")

if tier == "demo":
    leaked = [r for r in refs if visibility[r] != "public"]
    if leaked:
        sys.exit(f"{skill}: demo-tier skill declares INTERNAL platform refs {leaked} — "
                 f"demo bundles are publicly downloadable and must declare public refs only")

print("\n".join(refs))
PY
}

package_one() {
    local skill="$1"
    local src="${SKILLS_DIR}/${skill}"
    local out="${BUILD_DIR}/${skill}.skill"
    local staging
    staging="$(mktemp -d)"

    if [[ ! -f "${src}/SKILL.md" ]]; then
        echo "✗ ${skill}: SKILL.md not found at ${src}/SKILL.md" >&2
        rm -rf "${staging}"
        return 1
    fi

    cp -R "${src}/" "${staging}/${skill}/"

    local refs
    if ! refs="$(platform_refs_for "${skill}")"; then
        echo "✗ ${skill}: platform ref check failed (see above)" >&2
        rm -rf "${staging}"
        return 1
    fi

    if [[ -n "${refs}" ]]; then
        mkdir -p "${staging}/${skill}/references/platform"
        while IFS= read -r ref; do
            [[ -z "${ref}" ]] && continue
            if [[ ! -f "${PLATFORM_REFS_DIR}/${ref}.md" ]]; then
                echo "✗ ${skill}: declared platform ref not found: ${ref}.md" >&2
                rm -rf "${staging}"
                return 1
            fi
            cp "${PLATFORM_REFS_DIR}/${ref}.md" "${staging}/${skill}/references/platform/"
        done <<< "${refs}"
    fi

    rm -f "${out}"
    (cd "${staging}" && zip -qr "${out}" "${skill}" -x "*.DS_Store" -x "*/tier.txt")
    rm -rf "${staging}"

    local size
    size=$(du -h "${out}" | cut -f1)
    echo "✓ ${out} (${size})"
}

if [[ $# -gt 0 ]]; then
    for skill in "$@"; do
        package_one "${skill}"
    done
else
    while IFS= read -r skill; do
        package_one "${skill}"
    done < <(discover_skills)
fi

echo ""
echo "Done. Outputs in build/. Upload via Claude.ai → Settings → Capabilities → Skills."
