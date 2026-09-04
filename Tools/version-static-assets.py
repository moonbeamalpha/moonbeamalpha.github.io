#!/usr/bin/env python3
"""Content-version local stylesheet and script URLs across static HTML."""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSET_RE = re.compile(r'(?P<prefix>\b(?:href|src)=")(?P<url>/[^"?#]+\.(?:css|js))(?P<version>\?v=[0-9a-f]{12})?(?P<suffix>")')


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]


def render(path: Path, text: str) -> str:
    def replace(match: re.Match[str]) -> str:
        asset = ROOT / match.group("url").lstrip("/")
        if not asset.is_file():
            raise AssertionError(f"{path.relative_to(ROOT)}: missing local asset {match.group('url')}")
        return f"{match.group('prefix')}{match.group('url')}?v={digest(asset)}{match.group('suffix')}"
    return ASSET_RE.sub(replace, text)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    stale: list[str] = []
    for path in sorted(ROOT.rglob("*.html")):
        if ".git" in path.parts:
            continue
        current = path.read_text()
        expected = render(path, current)
        if current == expected:
            continue
        if args.check:
            stale.append(str(path.relative_to(ROOT)))
        else:
            path.write_text(expected)
    if stale:
        print("Static asset versions are stale:", file=sys.stderr)
        print("\n".join(f"- {path}" for path in stale), file=sys.stderr)
        print("Run python3 Tools/version-static-assets.py", file=sys.stderr)
        return 1
    print("Static asset versions OK" if args.check else "Static asset versions updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
