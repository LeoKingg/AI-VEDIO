#!/usr/bin/env python3
"""Initialize a new V3.0 AI short-drama project from projects/_template/ with presets & manifest."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import List, Optional

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = ROOT / "projects" / "_template"
PRESETS_DIR = ROOT / "presets"


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Initialize a new V3.0 AI-VEDIO project scaffold.")
    parser.add_argument("--name", required=True, help="Project slug (e.g., midnight-bus)")
    parser.add_argument("--genre", default="realistic_drama", help="Genre preset name under presets/genre_<name>.md")
    parser.add_argument("--platform", default="douyin_letterbox", help="Platform preset under presets/platform_<name>.md")
    parser.add_argument("--model", default="2.5", choices=["2.5", "2.0"], help="Primary Seedance model (default: 2.5)")
    parser.add_argument("--dry-run", action="store_true", help="Validate presets & print plan without writing files")
    args = parser.parse_args(argv)

    genre_file = PRESETS_DIR / f"genre_{args.genre}.md"
    platform_file = PRESETS_DIR / f"platform_{args.platform}.md"
    if not genre_file.is_file():
        print(f"Error: genre preset not found: {genre_file}", file=sys.stderr)
        return 2
    if not platform_file.is_file():
        print(f"Error: platform preset not found: {platform_file}", file=sys.stderr)
        return 2
    if not TEMPLATE_DIR.is_dir():
        print(f"Error: template directory not found: {TEMPLATE_DIR}", file=sys.stderr)
        return 2

    target_dir = ROOT / "projects" / args.name
    if target_dir.exists() and not args.dry_run:
        print(f"Error: target project already exists: {target_dir}", file=sys.stderr)
        return 2

    if args.dry_run:
        print(
            f"[DRY-RUN OK] Would initialize {target_dir} | model=Seedance {args.model} | "
            f"genre={genre_file.name} | platform={platform_file.name}"
        )
        return 0

    shutil.copytree(TEMPLATE_DIR, target_dir)
    manifest_path = target_dir / "manifest.json"
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["project_id"] = args.name
        manifest["primary_model"] = args.model
        manifest["genre_preset"] = f"presets/{genre_file.name}"
        manifest["platform_preset"] = f"presets/{platform_file.name}"
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(
        f"[OK] Initialized {target_dir} (model=Seedance {args.model}, genre={args.genre}, platform={args.platform})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
