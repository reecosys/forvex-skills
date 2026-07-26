#!/usr/bin/env bash
# Build the drop-in payload for hosting the demo skills on forvex.app.
#
# Demo .skill files are downloadable by anyone. Serving them from GitHub
# Releases ties public distribution to repo visibility — make this repo
# private and every public download URL 404s, including the manifest the
# install page renders from. Hosting the demo bundles on forvex.app cuts that
# dependency: the site owns its own assets.
#
# Emits build/public-skills/:
#   <skill>.skill   — one per demo-tier skill
#   manifest.json   — full manifest, with DEMO download_url rewritten to
#                     ${BASE_URL}/<skill>.skill; mcp entries keep their
#                     GitHub URLs (see note below)
#
# Usage:
#   ./scripts/publish-demo-bundles.sh
#   ./scripts/publish-demo-bundles.sh --version v0.3.0
#   ./scripts/publish-demo-bundles.sh --base-url https://www.forvex.app/skills
#   ./scripts/publish-demo-bundles.sh --dest ../reecosystem-web/public/skills
#
# NOTE ON MCP ENTRIES: they still point at GitHub Releases, so the gated
# install page keeps working unchanged today. If this repo is ever made
# private those URLs stop resolving for everyone, and MCP distribution needs
# its own answer — that is a separate decision, deliberately not made here.

set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BUILD_DIR="${REPO_DIR}/build"
OUT_DIR="${BUILD_DIR}/public-skills"
REGISTRY="${REPO_DIR}/skills/SKILL_REGISTRY.json"

BASE_URL="https://www.forvex.app/skills"
VERSION=""
DEST=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --base-url) BASE_URL="${2:?--base-url needs a value}"; shift 2 ;;
        --version)  VERSION="${2:?--version needs a value}";   shift 2 ;;
        --dest)     DEST="${2:?--dest needs a value}";         shift 2 ;;
        -h|--help)  sed -n '2,25p' "$0"; exit 0 ;;
        *) echo "unknown arg: $1" >&2; exit 2 ;;
    esac
done

BASE_URL="${BASE_URL%/}"

if [[ -z "${VERSION}" ]]; then
    VERSION="$(git -C "${REPO_DIR}" describe --tags --abbrev=0 2>/dev/null || echo "v0.0.0")"
fi

echo "→ version   ${VERSION}"
echo "→ base url  ${BASE_URL}"

# Gates first: never publish a bundle that failed the visibility rules.
python3 "${REPO_DIR}/scripts/lint-skills.py" >/dev/null
echo "→ lint      OK"

DEMO_SKILLS="$(python3 -c '
import json, sys
reg = json.load(open(sys.argv[1]))
print("\n".join(sorted(s for s, m in reg["skills"].items() if m.get("tier") == "demo")))
' "${REGISTRY}")"

rm -rf "${OUT_DIR}"
mkdir -p "${OUT_DIR}"

# package.sh enforces the demo/internal ref split and fails the build on a
# violation, so this cannot ship an internal ref even if the registry drifts.
while IFS= read -r skill; do
    [[ -z "${skill}" ]] && continue
    "${REPO_DIR}/package.sh" "${skill}" >/dev/null
    cp "${BUILD_DIR}/${skill}.skill" "${OUT_DIR}/"
done <<< "${DEMO_SKILLS}"

"${REPO_DIR}/scripts/build-manifest.sh" "${VERSION}" >/dev/null

python3 - "${BUILD_DIR}/manifest.json" "${OUT_DIR}/manifest.json" "${BASE_URL}" <<'PY'
import json, sys
src, out, base = sys.argv[1], sys.argv[2], sys.argv[3]
manifest = json.load(open(src))

rewritten = 0
for entry in manifest["skills"]:
    if entry.get("tier") == "demo":
        entry["download_url"] = f"{base}/{entry['id']}.skill"
        rewritten += 1

manifest["demo_asset_host"] = base
json.dump(manifest, open(out, "w"), indent=2)
open(out, "a").write("\n")
print(f"→ manifest  {len(manifest['skills'])} skills, {rewritten} demo URLs -> {base}")
PY

# Belt and braces: prove no internal ref made it into the payload.
python3 - "${OUT_DIR}" "${REGISTRY}" <<'PY'
import json, sys, zipfile
from pathlib import Path
out_dir, registry_path = Path(sys.argv[1]), sys.argv[2]
vis = {k: v for k, v in json.load(open(registry_path))["platform_ref_visibility"].items()
       if not k.startswith("_")}
leaks = []
for f in sorted(out_dir.glob("*.skill")):
    for name in zipfile.ZipFile(f).namelist():
        if "/references/platform/" in name and name.endswith(".md"):
            ref = name.split("/")[-1][:-3]
            if vis.get(ref) != "public":
                leaks.append(f"{f.name}: {ref}")
if leaks:
    sys.exit("✗ INTERNAL REFS IN PUBLIC PAYLOAD:\n  " + "\n  ".join(leaks))
print(f"→ verified  {len(list(out_dir.glob('*.skill')))} bundles, no internal refs")
PY

if [[ -n "${DEST}" ]]; then
    mkdir -p "${DEST}"
    cp "${OUT_DIR}"/*.skill "${OUT_DIR}/manifest.json" "${DEST}/"
    echo "→ copied to ${DEST}"
fi

echo ""
echo "Payload: ${OUT_DIR}"
ls -1sh "${OUT_DIR}" | tail -n +2 | sed 's/^/  /'
