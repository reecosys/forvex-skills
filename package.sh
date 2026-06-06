#!/usr/bin/env bash
# Package skill folders into .skill files (zip archives Claude.ai recognizes).
#
# Usage:
#   ./package.sh                   # package every skill
#   ./package.sh forvex-mao        # package a single skill
#
# Output: build/<skill-name>.skill
#
# Upload via Claude.ai → Settings → Capabilities → Skills → Upload.

set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILLS_DIR="${REPO_DIR}/skills"
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

    if [[ ! -f "${src}/SKILL.md" ]]; then
        echo "✗ ${skill}: SKILL.md not found at ${src}/SKILL.md" >&2
        return 1
    fi

    rm -f "${out}"
    (cd "${SKILLS_DIR}" && zip -qr "${out}" "${skill}" -x "*.DS_Store" -x "*/tier.txt")
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
