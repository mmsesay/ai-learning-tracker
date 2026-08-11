"""Ensure demo_workspace/sample-app is a tiny git repo (for git_summary demos).

Safe to run repeatedly. Does not touch anything outside demo_workspace/.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "demo_workspace" / "sample-app"


def _run(cwd: Path, *args: str) -> None:
    subprocess.run(args, cwd=cwd, check=True, capture_output=True, text=True)


def main() -> int:
    if not SAMPLE.is_dir():
        print(f"Missing {SAMPLE}", file=sys.stderr)
        return 1

    git_dir = SAMPLE / ".git"
    if not git_dir.exists():
        _run(SAMPLE, "git", "init")
        _run(SAMPLE, "git", "config", "user.email", "devassist-demo@example.com")
        _run(SAMPLE, "git", "config", "user.name", "DevAssist Demo")
        _run(SAMPLE, "git", "add", ".")
        _run(SAMPLE, "git", "commit", "-m", "Initial demo commit")
        print(f"Initialized git repo in {SAMPLE}")
    else:
        print(f"Git repo already present: {SAMPLE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
