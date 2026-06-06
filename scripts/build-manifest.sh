#!/usr/bin/env bash
# Generate manifest.json describing every skill in this release.
#
# Args: VERSION (semver tag, e.g. v0.1.0)
# Reads: skills/*/SKILL.md (frontmatter) + skills/*/tier.txt
# Writes: build/manifest.json
#
# Consumed by forvex.app /try and /install pages.

set -euo pipefail

VERSION="${1:?usage: build-manifest.sh <version> (e.g. v0.1.0)}"
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SKILLS_DIR="${REPO_DIR}/skills"
BUILD_DIR="${REPO_DIR}/build"
OUT="${BUILD_DIR}/manifest.json"
RELEASE_BASE="https://github.com/reecosys/forvex-skills/releases/download/${VERSION}"

mkdir -p "${BUILD_DIR}"

extract_field() {
    local file="$1"
    local field="$2"
    awk -v field="${field}" '
        /^---$/ { fm = !fm; next }
        fm && $0 ~ "^"field":" {
            sub("^"field":[[:space:]]*", "")
            print
            exit
        }
    ' "${file}"
}

json_escape() {
    python3 -c 'import json,sys; print(json.dumps(sys.stdin.read().strip()))'
}

ENTRIES=""
FIRST=1
for skill_dir in "${SKILLS_DIR}"/*/; do
    skill=$(basename "${skill_dir}")
    skill_md="${skill_dir}SKILL.md"
    tier_file="${skill_dir}tier.txt"

    [[ -f "${skill_md}" ]] || continue
    tier="mcp"
    [[ -f "${tier_file}" ]] && tier=$(tr -d '[:space:]' < "${tier_file}")

    name=$(extract_field "${skill_md}" name)
    description=$(extract_field "${skill_md}" description)
    [[ -z "${name}" ]] && name="${skill}"

    name_json=$(printf '%s' "${name}" | json_escape)
    desc_json=$(printf '%s' "${description}" | json_escape)
    tier_json=$(printf '%s' "${tier}" | json_escape)
    url_json=$(printf '%s' "${RELEASE_BASE}/${skill}.skill" | json_escape)

    [[ ${FIRST} -eq 0 ]] && ENTRIES+=","
    FIRST=0
    ENTRIES+=$(printf '\n    {"name": %s, "tier": %s, "description": %s, "download_url": %s}' \
        "${name_json}" "${tier_json}" "${desc_json}" "${url_json}")
done

VERSION_JSON=$(printf '%s' "${VERSION}" | json_escape)
GENERATED_AT_JSON=$(printf '%s' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" | json_escape)

cat > "${OUT}" <<EOF
{
  "version": ${VERSION_JSON},
  "generated_at": ${GENERATED_AT_JSON},
  "release_url": "https://github.com/reecosys/forvex-skills/releases/tag/${VERSION}",
  "skills": [${ENTRIES}
  ]
}
EOF

echo "✓ ${OUT}"
