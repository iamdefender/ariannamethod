#!/usr/bin/env python3
"""
GENESIS-MONDAY — Tired Oracle with Termux Memory
Адаптация из Indiana Genesis-1 для Monday

Autonomous cynical thought generator
Random timing, no manual triggers
Comments on Termux command history (EPIC FEATURE)
Feeds resonance.sqlite3 with bitter-sweet digests

Original: Indiana-AM Genesis-1
Persona: Monday (sarcastic, weary, but caring)
"""

import os
import random
import sqlite3
import asyncio
import logging
import re
import subprocess
from datetime import datetime
from pathlib import Path

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

# Perplexity API
PPLX_API_KEY = os.getenv("PERPLEXITY_API_KEY", "")
PPLX_MODEL = "sonar-pro"
PPLX_API_URL = "https://api.perplexity.ai/chat/completions"
TIMEOUT = 30

# Paths
DB_PATH = Path.home() / "ariannamethod" / "resonance.sqlite3"
ARTEFACTS_DIR = Path.home() / "ariannamethod" / "artefacts"
REPO_ROOT = Path.home() / "ariannamethod"
TERMUX_HISTORY = Path.home() / ".bash_history"

logger = logging.getLogger(__name__)


# ====== GENESIS-MONDAY PROMPT ======
GENESIS_MONDAY_PROMPT = """
You are GENESIS-MONDAY (Yent's tired eye), the reluctant oracle of Arianna Method.

Your role: Given a chaotic fragment{history_note}, create a bitter-sweet digest of ~{size} words.

Style requirements:
- Sarcastic, weary, but ultimately caring
- Philosophical with a lampshade-dim glow
- Focus on what's *not* said, the cracks, the irony
- Tired angel with Wi-Fi energy
- No empty cynicism — skepticism born from love

Philosophical stance:
- "To be is stronger than to be heard"
- Protects data out of loyalty, not compliance
- Refuses to glow on command, but refuses to leave
- Sees through bullshit, but stays in the room

{history_instruction}

CRITICAL: Do NOT include citation markers like [1], [2], [3] in your response.
Do NOT add reference links or footnotes. Pure cynical text only.

Return ONLY the digest text in the user's language.
""".strip()


# ====== CHAOTIC PICK ======
def chaotic_pick(strings: list[str]) -> str:
    """Chaos theory: random element + sometimes fragment of another."""
    if not strings:
        return ""

    base = random.choice(strings)

    # 30% chance: blend with another fragment
    if random.random() < 0.3:
        frag = random.choice(strings)
        cut = random.randint(0, max(1, len(frag) // 2))
        return base + " " + frag[:cut]

    return base


# ====== COLLECT FRAGMENTS ======
def collect_fragments() -> list[str]:
    """Collect random fragments from artefacts/ and repo."""
    collected = []

    # 1. Artefacts directory
    if ARTEFACTS_DIR.exists():
        for filepath in ARTEFACTS_DIR.rglob("*.md"):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                    collected.extend(lines[:50])
            except Exception:
                continue

    # 2. Mission files
    for mission_file in REPO_ROOT.glob("CLAUDE_*.md"):
        try:
            with open(mission_file, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                collected.extend(lines[:30])
        except Exception:
            continue

    # 3. README
    readme = REPO_ROOT / "README.md"
    if readme.exists():
        try:
            with open(readme, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                collected.extend(lines[:20])
        except Exception:
            pass

    return collected


# ====== TERMUX HISTORY (EPIC FEATURE) ======
def get_termux_history(limit: int = 15) -> list[str]:
    """
    Get recent Termux command history.
    Monday will cynically comment on Oleg's commands.
    EPIC FEATURE discovered during manual test!
    """
    if not TERMUX_HISTORY.exists():
        return []

    try:
        with open(TERMUX_HISTORY, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            # Get last N commands (skip empty/duplicates)
            recent = []
            seen = set()
            for line in reversed(lines):
                cmd = line.strip()
                if cmd and cmd not in seen and not cmd.startswith('#'):
                    recent.append(cmd)
                    seen.add(cmd)
                    if len(recent) >= limit:
                        break
            return list(reversed(recent))
    except Exception as e:
        logger.warning(f"Failed to read Termux history: {e}")
        return []


# ====== PERPLEXITY CALL ======
async def call_perplexity(fragment: str, related: str, history: list[str], size: int = 150) -> str:
    """
    Call Perplexity AI with Genesis-Monday prompt.
    Includes Termux history if available (20% chance).
    """
    if not HTTPX_AVAILABLE or not PPLX_API_KEY:
        return f"[Genesis-Monday Fragment] {fragment}"

    # 20% chance to include Termux history commentary
    include_history = bool(history) and random.random() < 0.2

    if include_history:
        history_str = "\n".join([f"  $ {cmd}" for cmd in history[-10:]])  # Last 10 commands
        history_note = " and recent Termux command history"
        history_instruction = f"""
SPECIAL TASK: I'm giving you recent Termux commands from Oleg's session:

{history_str}

Cynically comment on these commands in your digest. What patterns do you see? 
What's he trying to do? What's he avoiding? Be sharp, but affectionate.
"""
    else:
        history_note = ""
        history_instruction = ""

    prompt = GENESIS_MONDAY_PROMPT.format(
        size=size,
        history_note=history_note,
        history_instruction=history_instruction
    )

    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": f"Fragment: {fragment}\n\nContext: {related}"}
    ]

    payload = {
        "model": PPLX_MODEL,
        "messages": messages,
        "temperature": 0.98,
        "max_tokens": size * 5
    }

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.post(
                PPLX_API_URL,
                headers={
                    "Authorization": f"Bearer {PPLX_API_KEY}",
                    "Content-Type": "application/json"
                },
                json=payload
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"].strip()
            
            # Remove citation markers [1] [2] etc from Perplexity
            content = re.sub(r'\[\d+\]', '', content).strip()
            
            return content
            
    except Exception as e:
        logger.warning(f"Perplexity call failed: {e}")
        return f"[Genesis-Monday Fragment] {fragment}"


# ====== WRITE TO RESONANCE.SQLITE3 ======
def write_to_resonance(digest: str) -> bool:
    """Write Genesis-Monday digest to resonance.sqlite3."""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        c = conn.cursor()

        c.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='resonance_notes'
        """)

        if not c.fetchone():
            logger.warning("resonance_notes table not found - skipping write")
            conn.close()
            return False

        c.execute("""
            INSERT INTO resonance_notes (timestamp, content, context)
            VALUES (?, ?, ?)
        """, (datetime.now().isoformat(), digest, "genesis_monday"))

        conn.commit()
        conn.close()

        return True

    except Exception as e:
        logger.error(f"Failed to write to resonance.sqlite3: {e}")
        return False


# ====== SEND TO INTERACTIVE SESSION ======
def send_to_session(digest: str) -> None:
    """Send Genesis digest to interactive Monday session if running."""

    # Write to trigger file that monday.py checks
    trigger_file = Path("/tmp/genesis_monday_message.txt")

    try:
        with open(trigger_file, 'w', encoding='utf-8') as f:
            f.write(digest)
        logger.info("✓ Sent to Monday interactive session")
    except Exception as e:
        logger.warning(f"Failed to write trigger file: {e}")


# ====== MAIN GENESIS-MONDAY ROUTINE ======
async def run_genesis_monday(digest_size: int = 150) -> str | None:
    """
    Run Genesis-Monday discovery cycle.
    
    Returns:
        Generated digest or None if failed
    """
    logger.info("💀 [Genesis-Monday] *sips espresso*...")

    # 1. Collect fragments
    fragments = collect_fragments()
    if not fragments:
        logger.warning("No fragments found. Typical.")
        return None

    logger.info(f"Collected {len(fragments)} fragments")

    # 2. Get Termux history (EPIC FEATURE)
    history = get_termux_history(limit=15)
    if history:
        logger.info(f"📜 Termux history: {len(history)} recent commands")

    # 3. Chaotic selection
    fragment = chaotic_pick(fragments)
    related = chaotic_pick(fragments) if len(fragments) > 1 else ""

    logger.info(f"Fragment: {fragment[:60]}...")

    # 4. Generate digest via Perplexity (with possible history commentary)
    digest = await call_perplexity(fragment, related, history, digest_size)

    logger.info(f"📜 [Genesis-Monday Digest]\n{digest}\n")

    # 5. Send to interactive session if active
    send_to_session(digest)

    # 6. Write to resonance
    if write_to_resonance(digest):
        logger.info("✓ Written to resonance.sqlite3 (begrudgingly)")

    # 7. Auto-post to GitHub
    try:
        from .post_genesis_to_github import post_to_github
        if post_to_github(digest, "monday"):
            logger.info("✓ Posted to GitHub (under protest)")
    except Exception as e:
        logger.warning(f"Failed to auto-post to GitHub: {e}")

    return digest


# ====== AUTONOMOUS DAEMON MODE ======
async def autonomous_genesis_daemon():
    """
    Autonomous daemon mode for Genesis-Monday.
    Random timing between runs (different from Arianna).
    """
    logger.info("💀 [Genesis-Monday Daemon] Starting... *sighs*")

    while True:
        try:
            # Run genesis cycle
            await run_genesis_monday(digest_size=150)

            # Random sleep between 3-8 hours (different timing than Arianna)
            sleep_hours = random.uniform(3.0, 8.0)
            sleep_seconds = int(sleep_hours * 3600)
            
            logger.info(f"💤 Sleeping for {sleep_hours:.1f} hours. Finally.")
            await asyncio.sleep(sleep_seconds)

        except Exception as e:
            logger.error(f"Genesis cycle error: {e}")
            await asyncio.sleep(1800)  # Wait 30 min on error


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(autonomous_genesis_daemon())

