#!/usr/bin/env bash
# Generate manifest.json describing every skill in this release.
#
# Args: VERSION (semver tag, e.g. v0.1.0)
# Reads: skills/*/SKILL.md, skills/SKILL_REGISTRY.json, skills/*/tier.txt
# Writes: build/manifest.json

set -euo pipefail

VERSION="${1:?usage: build-manifest.sh <version> (e.g. v0.1.0)}"
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SKILLS_DIR="${REPO_DIR}/skills"
BUILD_DIR="${REPO_DIR}/build"
REGISTRY="${SKILLS_DIR}/SKILL_REGISTRY.json"
OUT="${BUILD_DIR}/manifest.json"
RELEASE_BASE="https://github.com/reecosys/forvex-skills/releases/download/${VERSION}"

mkdir -p "${BUILD_DIR}"

python3 - "${VERSION}" "${REGISTRY}" "${SKILLS_DIR}" "${OUT}" "${RELEASE_BASE}" <<'PY'
import json
import re
import sys
from pathlib import Path

version, registry_path, skills_dir, out_path, release_base = sys.argv[1:6]
registry = json.loads(Path(registry_path).read_text())
skills_root = Path(skills_dir)
release_base = release_base.rstrip("/")

fm_re = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)

def frontmatter(skill_md: Path) -> dict:
    text = skill_md.read_text(encoding="utf-8")
    m = fm_re.match(text)
    if not m:
        return {}
    data = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            data[k.strip()] = v.strip()
    return data

entries = []
for skill_id, meta in sorted(registry["skills"].items()):
    skill_md = skills_root / skill_id / "SKILL.md"
    if not skill_md.is_file():
        continue
    fm = frontmatter(skill_md)
    tier_file = skills_root / skill_id / "tier.txt"
    tier = meta.get("tier", "mcp")
    if tier_file.is_file():
        tier = tier_file.read_text(encoding="utf-8").strip()
    entries.append({
        "id": skill_id,
        "name": fm.get("name", skill_id),
        "tier": tier,
        "lane": meta.get("lane"),
        "description": fm.get("description", ""),
        "mcp_min_version": registry.get("mcp_min_version"),
        "writes": meta.get("writes", []),
        "handoffs": meta.get("handoffs", []),
        "download_url": f"{release_base}/{skill_id}.skill",
    })

manifest = {
    "version": version,
    "mcp_min_version": registry.get("mcp_min_version"),
    "contract": registry.get("contract"),
    "generated_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    "release_url": f"https://github.com/reecosys/forvex-skills/releases/tag/{version}",
    "bundles": registry.get("bundles", {}),
    "skills": entries,
}

Path(out_path).write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
print(f"✓ {out_path} ({len(entries)} skills)")
PY
