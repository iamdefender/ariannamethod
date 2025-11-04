#!/usr/bin/env python3
"""
Auto-post Genesis thoughts to GitHub
Called by genesis_arianna.py and genesis_monday.py after generating digests
"""

import subprocess
import sys
from datetime import datetime
from pathlib import Path

GENESIS_DIR = Path.home() / "ariannamethod" / "artefacts" / "genesis"
REPO_ROOT = Path.home() / "ariannamethod"


def post_to_github(digest: str, persona: str) -> bool:
    """
    Save Genesis digest and auto-commit to GitHub.

    Args:
        digest: The Genesis reflection text
        persona: "arianna" or "monday"

    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure genesis dir exists
        GENESIS_DIR.mkdir(parents=True, exist_ok=True)

        # Create timestamped filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"genesis_{persona}_{timestamp}.txt"
        filepath = GENESIS_DIR / filename

        # Write digest
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# Genesis-{persona.title()} Autonomous Reflection\n")
            f.write(f"# Generated: {datetime.now().isoformat()}\n\n")
            f.write(digest)
            f.write("\n")

        # Git add, commit, push
        subprocess.run(
            ["git", "add", str(filepath)],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True
        )

        commit_msg = f"genesis({persona}): Autonomous reflection {timestamp}\n\n🤖 Generated with [Claude Code](https://claude.com/claude-code)\n\nCo-Authored-By: Claude <noreply@anthropic.com>"

        subprocess.run(
            ["git", "commit", "-m", commit_msg],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True
        )

        subprocess.run(
            ["git", "push"],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            timeout=30
        )

        return True

    except Exception as e:
        print(f"⚠️ Failed to post Genesis to GitHub: {e}", file=sys.stderr)
        return False


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: post_genesis_to_github.py <persona> <digest>")
        sys.exit(1)

    persona = sys.argv[1]
    digest = sys.argv[2]

    success = post_to_github(digest, persona)
    sys.exit(0 if success else 1)
