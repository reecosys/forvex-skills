#!/usr/bin/env python3
"""Lint forvex-skills repo — registry, MCP tools, cross-skill refs, frontmatter."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO / "skills"
REGISTRY_PATH = SKILLS_DIR / "SKILL_REGISTRY.json"
MCP_REGISTRY_PATH = REPO / "platform" / "mcp-tools.registry.json"
PLATFORM_REFS = REPO / "platform" / "references"

CROSS_SKILL_RE = re.compile(r"\.\./(?:forvex|readvise)-[a-z0-9-]+/")
PLATFORM_REF_USE_RE = re.compile(r"references/platform/([a-z0-9-]+)\.md")
TOOL_RE = re.compile(r"\b((?:forvex|readvise)_[a-z0-9_]+)\b")
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def discover_skill_dirs() -> list[str]:
    dirs = []
    for child in sorted(SKILLS_DIR.iterdir()):
        if child.is_dir() and (child / "SKILL.md").is_file():
            dirs.append(child.name)
    return dirs


def parse_frontmatter(skill_md: Path) -> dict[str, str]:
    text = skill_md.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}
    block = match.group(1)
    out: dict[str, str] = {}
    for line in block.splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            out[key.strip()] = val.strip()
    return out


def lint() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    registry = load_json(REGISTRY_PATH)
    mcp_registry = load_json(MCP_REGISTRY_PATH)
    known_tools = set(mcp_registry["tools"])
    skill_dirs = discover_skill_dirs()
    registry_skills = set(registry["skills"].keys())

    # Registry ↔ folders
    for sid in sorted(registry_skills - set(skill_dirs)):
        errors.append(f"registry lists missing skill folder: {sid}")
    for sid in sorted(set(skill_dirs) - registry_skills):
        errors.append(f"skill folder not in SKILL_REGISTRY.json: {sid}")

    # Platform ref files
    platform_files = {p.stem for p in PLATFORM_REFS.glob("*.md")}

    for skill_id in skill_dirs:
        skill_path = SKILLS_DIR / skill_id
        skill_md = skill_path / "SKILL.md"
        meta = registry["skills"].get(skill_id, {})

        # Frontmatter
        fm = parse_frontmatter(skill_md)
        if not fm.get("name"):
            errors.append(f"{skill_id}: SKILL.md missing frontmatter 'name'")
        if not fm.get("description"):
            errors.append(f"{skill_id}: SKILL.md missing frontmatter 'description'")
        if fm.get("name") and fm["name"] != skill_id and fm["name"] != skill_id.replace("forvex-", "forvex-"):
            if fm["name"] != skill_id:
                warnings.append(f"{skill_id}: frontmatter name '{fm['name']}' != folder name")

        # tier.txt vs registry
        tier_file = skill_path / "tier.txt"
        if tier_file.exists() and meta:
            tier_disk = tier_file.read_text(encoding="utf-8").strip()
            if tier_disk != meta.get("tier"):
                errors.append(
                    f"{skill_id}: tier.txt ({tier_disk}) != registry tier ({meta.get('tier')})"
                )

        # Governance pointer
        body = skill_md.read_text(encoding="utf-8")
        if "SKILL_SYSTEM_CONTRACT" not in body and "references/platform/" not in body:
            errors.append(
                f"{skill_id}: SKILL.md missing contract pointer (SKILL_SYSTEM_CONTRACT or references/platform/)"
            )

        # Cross-skill paths (broken in packaged .skill)
        for rel in skill_path.rglob("*.md"):
            content = rel.read_text(encoding="utf-8")
            for match in CROSS_SKILL_RE.finditer(content):
                errors.append(
                    f"{rel.relative_to(REPO)}: cross-skill path '{match.group(0)}' — use references/platform/"
                )

        # Registry tools ⊆ MCP registry
        if meta:
            declared = set(meta.get("reads", []) + meta.get("writes", []))
            unknown = sorted(declared - known_tools)
            if unknown:
                errors.append(f"{skill_id}: registry tools not in mcp-tools.registry.json: {unknown}")

            for ref in meta.get("platform_refs", []):
                if ref not in platform_files:
                    errors.append(f"{skill_id}: platform_refs entry missing file: {ref}.md")

    # ---- Platform ref visibility -------------------------------------------
    # demo-tier .skill files are downloadable by anyone from a public release,
    # so they may only carry refs marked "public". package.sh vendors exactly
    # what each skill declares, which makes these declarations load-bearing:
    # an undeclared ref is a broken link at runtime, and a misclassified one is
    # a confidential doc shipped to the public.
    visibility = {k: v for k, v in registry.get("platform_ref_visibility", {}).items()
                  if not k.startswith("_")}

    for ref in sorted(platform_files - set(visibility)):
        errors.append(
            f"platform/references/{ref}.md has no platform_ref_visibility entry "
            f"(classify it 'public' or 'internal' in SKILL_REGISTRY.json)"
        )
    for ref in sorted(set(visibility) - platform_files):
        errors.append(f"platform_ref_visibility lists missing file: {ref}.md")
    for ref, vis in sorted(visibility.items()):
        if vis not in ("public", "internal"):
            errors.append(f"platform_ref_visibility['{ref}']: bad value {vis!r} "
                          f"(expected 'public' or 'internal')")

    for skill_id in skill_dirs:
        meta = registry["skills"].get(skill_id, {})
        if not meta:
            continue
        declared = meta.get("platform_refs", [])

        if meta.get("tier") == "demo":
            leaked = [r for r in declared if visibility.get(r) != "public"]
            if leaked:
                errors.append(
                    f"{skill_id}: demo-tier skill declares internal platform refs {leaked} — "
                    f"demo bundles ship publicly"
                )

        # Anything the skill's markdown points at must be declared, or
        # package.sh won't vendor it and the link dies in the packaged skill.
        mentioned: set[str] = set()
        for md in (SKILLS_DIR / skill_id).rglob("*.md"):
            for m in PLATFORM_REF_USE_RE.finditer(md.read_text(encoding="utf-8")):
                mentioned.add(m.group(1))
        for ref in sorted((mentioned & platform_files) - set(declared)):
            errors.append(
                f"{skill_id}: references/platform/{ref}.md used in markdown but not declared "
                f"in platform_refs — it will be missing from the packaged .skill"
            )

    # Bundle membership
    bundled: set[str] = set()
    for bundle_id, bundle in registry.get("bundles", {}).items():
        for sid in bundle.get("skills", []):
            if sid not in registry_skills:
                errors.append(f"bundle '{bundle_id}' references unknown skill: {sid}")
            bundled.add(sid)

    unbundled = registry_skills - bundled
    if unbundled:
        warnings.append(f"skills not in any bundle: {sorted(unbundled)}")

    # Stale zip artifacts in skills/
    for z in SKILLS_DIR.glob("*.zip"):
        warnings.append(f"stale artifact in skills/: {z.name} — remove or gitignore")

    for msg in warnings:
        print(f"WARN: {msg}")
    for msg in errors:
        print(f"ERROR: {msg}")

    if errors:
        print(f"\n{len(errors)} error(s), {len(warnings)} warning(s)")
        return 1
    print(f"OK — {len(skill_dirs)} skills, {len(known_tools)} MCP tools, {len(warnings)} warning(s)")
    return 0


if __name__ == "__main__":
    sys.exit(lint())
