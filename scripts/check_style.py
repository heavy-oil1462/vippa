#!/usr/bin/env python3
"""Writing style gate for every tracked text file.

The project's writing rules (CLAUDE.md) forbid icons and emoji, bold and
em dashes or double dashes in docs, comments, commit messages and PR
text. This gate catches them in the repo's own files:

  FAIL  an em dash, en dash or emoji anywhere in a text file
  FAIL  bold (**text**) or a spaced double dash ( -- ) in Markdown
        prose, code fences and inline code excluded

Exit 1 on FAIL, 0 otherwise.

Usage:
    scripts/check_style.py [file ...]   # default: every git-tracked text file
"""

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEXT = {".md", ".py", ".scad", ".yml", ".yaml", ".json", ".txt", ".toml", ".nix"}
SKIP = {"LICENSE"}
DASHES = re.compile(f"[{chr(0x2013)}{chr(0x2014)}]")
EMOJI = re.compile(f"[{chr(0x2600)}-{chr(0x27bf)}{chr(0x2b00)}-{chr(0x2bff)}"
                   f"{chr(0x1f000)}-{chr(0x1faff)}{chr(0xfe0f)}]")
BOLD = re.compile(r"\*\*\S")
DOUBLE_DASH = re.compile(r"\s--\s")
INLINE_CODE = re.compile(r"`[^`]*`")


def tracked():
    out = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"],
                         cwd=ROOT, capture_output=True, text=True, check=True).stdout
    return [ROOT / f for f in out.splitlines()]


def problems(path: Path):
    md = path.suffix == ".md"
    fence = False
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if DASHES.search(line):
            yield n, "em or en dash"
        if EMOJI.search(line):
            yield n, "emoji or icon"
        if not md:
            continue
        if line.lstrip().startswith("```"):
            fence = not fence
            continue
        prose = "" if fence else INLINE_CODE.sub("", line)
        if BOLD.search(prose):
            yield n, "bold"
        if DOUBLE_DASH.search(prose):
            yield n, "double dash"


def main(argv):
    files = [Path(a).resolve() for a in argv[1:]] or tracked()
    files = [f for f in files if f.is_file() and f.suffix in TEXT and f.name not in SKIP]
    bad = 0
    for f in files:
        for n, what in problems(f):
            shown = f.relative_to(ROOT) if f.is_relative_to(ROOT) else f
            print(f"[FAIL] {shown}:{n}: {what}")
            bad += 1
    if bad:
        print(f"\n{bad} style problem(s). See Writing style in CLAUDE.md.")
        return 1
    print(f"ok: {len(files)} text files, writing style clean")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
