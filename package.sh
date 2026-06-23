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
BUILD_DIR="${REPO_DIR}/build"
mkdir -p "${BUILD_DIR}"

discover_skills() {
    find "${SKILLS_DIR}" -mindepth 2 -maxdepth 2 -name SKILL.md -print0 \
        | xargs -0 -n1 dirname \
        | xargs -n1 basename
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

    if [[ -d "${PLATFORM_REFS_DIR}" ]]; then
        mkdir -p "${staging}/${skill}/references/platform"
        cp -R "${PLATFORM_REFS_DIR}/." "${staging}/${skill}/references/platform/"
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
