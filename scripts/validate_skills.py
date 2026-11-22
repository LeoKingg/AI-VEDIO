#!/usr/bin/env python3
"""Validate all skills under skills/ against agentskills.io specification and leak guards."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / "skills"

NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LINK_RE = re.compile(r"`((?:references|scripts|assets)/[^`\s]+)`")

# Guard against personal/external tutorial leaks entering generic skills
FORBIDDEN_LEAK_TERMS = [
    "小薇拉",
    "永恒黄昏",
    "银镜城",
    "永暮教廷",
    "K哥",
    "元启录",
    "Neo站",
    "KSRIM",
    "write_file",
    "edit_file",
]


def parse_frontmatter(text: str) -> Tuple[Dict[str, str], str, List[str]]:
    errors: List[str] = []
    if not text.startswith("---\n"):
        return {}, text, ["SKILL.md must start with YAML frontmatter '---'"]
    parts = text.split("\n---\n", 1)
    if len(parts) != 2:
        return {}, text, ["SKILL.md YAML frontmatter closing '---' not found"]
    raw_fm = parts[0][4:]
    body = parts[1]
    data: Dict[str, str] = {}
    for line in raw_fm.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            errors.append(f"Invalid frontmatter line: {line}")
            continue
        k, v = line.split(":", 1)
        data[k.strip()] = v.strip().strip('"').strip("'")
    return data, body, errors


def validate_skill(skill_dir: Path) -> List[str]:
    errors: List[str] = []
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        return [f"{skill_dir.name}: missing SKILL.md"]

    raw = skill_md.read_text(encoding="utf-8")
    lines = raw.splitlines()
    if len(lines) > 500:
        errors.append(f"{skill_dir.name}: SKILL.md has {len(lines)} lines (>500 progressive disclosure limit)")

    fm, _body, fm_errors = parse_frontmatter(raw)
    errors.extend(f"{skill_dir.name}: {e}" for e in fm_errors)

    name = fm.get("name", "")
    desc = fm.get("description", "")

    if not name:
        errors.append(f"{skill_dir.name}: missing required frontmatter 'name'")
    else:
        if len(name) > 64 or not NAME_RE.match(name):
            errors.append(f"{skill_dir.name}: invalid name '{name}' (must be lowercase a-z0-9 with single hyphens)")
        if name != skill_dir.name:
            errors.append(f"{skill_dir.name}: frontmatter name '{name}' must match directory name '{skill_dir.name}'")

    if not desc:
        errors.append(f"{skill_dir.name}: missing required frontmatter 'description'")
    elif len(desc) > 1024:
        errors.append(f"{skill_dir.name}: description exceeds 1024 chars ({len(desc)})")

    # Verify all relative resource links exist and are 1 level deep
    for rel in LINK_RE.findall(raw):
        target = skill_dir / rel
        if not target.is_file():
            errors.append(f"{skill_dir.name}: broken resource reference '{rel}'")
        if len(Path(rel).parts) > 2:
            errors.append(f"{skill_dir.name}: resource reference '{rel}' is deeper than 1 level")

    # Scan all text files inside the skill for forbidden leaks
    for f in sorted(skill_dir.rglob("*.md")):
        content = f.read_text(encoding="utf-8")
        for term in FORBIDDEN_LEAK_TERMS:
            if term in content:
                errors.append(f"{f.relative_to(ROOT)}: contains forbidden leak term '{term}'")

    return errors


def main() -> int:
    if not SKILLS_DIR.is_dir():
        print("Error: skills/ directory not found", file=sys.stderr)
        return 2

    skill_dirs = sorted(p for p in SKILLS_DIR.iterdir() if p.is_dir())
    if not skill_dirs:
        print("Error: no skills found under skills/", file=sys.stderr)
        return 2

    all_errors: List[str] = []
    for sd in skill_dirs:
        errs = validate_skill(sd)
        if errs:
            all_errors.extend(errs)
        else:
            print(f"[OK] {sd.name}")

    if all_errors:
        print("\nValidation FAILED:", file=sys.stderr)
        for e in all_errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    print(f"\nAll {len(skill_dirs)} skills passed agentskills.io compliance & leak checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
