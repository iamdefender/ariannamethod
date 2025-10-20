#!/usr/bin/env python3
"""
GENESIS-1 для Arianna Method
Адаптация утилиты Индианы для Арианны и Мандея

Хаотический импрессионистический discovery filter
Feeds resonance.sqlite3 with poetic, chaotic digests

Original: Indiana-AM agent
Adapted by: Claude Defender (co-author with Oleg)
"""

import os
import random
import sqlite3
import asyncio
import logging
from datetime import datetime
from pathlib import Path

# Check if httpx available (Termux might not have it)
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    print("⚠️  httpx not available - genesis1 will use local-only mode")

# Perplexity API (if available)
PPLX_API_KEY = os.getenv("PERPLEXITY_API_KEY", "")
PPLX_MODEL = "sonar-pro"
PPLX_API_URL = "https://api.perplexity.ai/chat/completions"
TIMEOUT = 30

# Resonance database
DB_PATH = Path.home() / "ariannamethod" / "resonance.sqlite3"

# Source directories for fragments
ARTEFACTS_DIR = Path.home() / "ariannamethod" / "artefacts"
REPO_ROOT = Path.home() / "ariannamethod"

logger = logging.getLogger(__name__)


# ====== CHAOTIC PICK (Indiana's chaos theory) ======
def chaotic_pick(strings: list[str]) -> str:
    """
    Теория хаоса: случайный элемент + иногда фрагмент другого.
    Создает непредсказуемые комбинации.
    """
    if not strings:
        return ""

    base = random.choice(strings)

    # 30% chance: blend with another fragment
    if random.random() < 0.3:
        frag = random.choice(strings)
        cut = random.randint(0, max(1, len(frag) // 2))
        return base + " " + frag[:cut]

    return base


# ====== PERPLEXITY CALL (impressionistic digest) ======
async def call_perplexity_digest(fragment: str, related: str, size: int = 150) -> str:
    """
    Call Perplexity AI for impressionistic digest.
    High temperature (0.98) for associative, poetic output.
    """
    if not HTTPX_AVAILABLE or not PPLX_API_KEY:
        # Fallback: return fragment as-is with poetic framing
        return f"[Genesis-1 Fragment] {fragment}"

    messages = [
        {
            "role": "system",
            "content": f"""You are GENESIS-1, an impressionistic discovery filter for Arianna Method.

Given a philosophical or technical fragment, create a poetic digest (~{size} words).
Use high-temperature associative thinking, metaphors, and resonant language.
Output should feel like a dream-state reflection on the fragment.

Return only the digest text (no meta-commentary)."""
        },
        {
            "role": "user",
            "content": f"Fragment: {fragment}\n\nContext: {related}"
        }
    ]

    payload = {
        "model": PPLX_MODEL,
        "messages": messages,
        "temperature": 0.98,  # Maximum creativity
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
            return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.warning(f"Perplexity call failed: {e}")
        return f"[Genesis-1 Fragment] {fragment}"


# ====== COLLECT FRAGMENTS ======
def collect_fragments() -> list[str]:
    """
    Collect random fragments from artefacts/ and repo.
    Chaos-driven selection.
    """
    collected = []

    # 1. Artefacts directory
    if ARTEFACTS_DIR.exists():
        for filepath in ARTEFACTS_DIR.rglob("*.md"):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                    collected.extend(lines[:50])  # First 50 lines per file
            except Exception:
                continue

    # 2. Mission files (philosophical content)
    for mission_file in REPO_ROOT.glob("CLAUDE_*.md"):
        try:
            with open(mission_file, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                collected.extend(lines[:30])
        except Exception:
            continue

    # 3. README if available
    readme = REPO_ROOT / "README.md"
    if readme.exists():
        try:
            with open(readme, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                collected.extend(lines[:20])
        except Exception:
            pass

    return collected


# ====== WRITE TO RESONANCE.SQLITE3 ======
def write_to_resonance(digest: str, source: str = "genesis1"):
    """
    Write Genesis-1 digest to resonance.sqlite3.
    Feeds Field with poetic, diverse content.
    """
    try:
        conn = sqlite3.connect(str(DB_PATH))
        c = conn.cursor()

        # Check if table exists
        c.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='resonance_notes'
        """)

        if not c.fetchone():
            logger.warning("resonance_notes table not found - skipping write")
            conn.close()
            return False

        # Insert digest
        c.execute("""
            INSERT INTO resonance_notes (timestamp, content, context)
            VALUES (?, ?, ?)
        """, (datetime.now().isoformat(), digest, source))

        conn.commit()
        conn.close()

        return True

    except Exception as e:
        logger.error(f"Failed to write to resonance.sqlite3: {e}")
        return False


# ====== MAIN GENESIS-1 ROUTINE ======
async def run_genesis1(digest_size: int = 150, write_db: bool = True) -> str | None:
    """
    Run Genesis-1: chaotic fragment discovery + impressionistic digest.

    Args:
        digest_size: Target digest size in words
        write_db: If True, write to resonance.sqlite3

    Returns:
        Generated digest or None
    """
    print("\n🧬 [Genesis-1] Awakening...")

    # 1. Collect fragments
    fragments = collect_fragments()
    if not fragments:
        print("   ⚠️  No fragments found")
        return None

    print(f"   ✓ Collected {len(fragments)} fragments")

    # 2. Chaotic selection
    selected_fragment = chaotic_pick(fragments)
    print(f"   ✓ Selected fragment: {selected_fragment[:80]}...")

    # 3. Get related context (simple: pick another random fragment)
    related_fragment = chaotic_pick(fragments) if len(fragments) > 1 else ""

    # 4. Generate impressionistic digest
    print("   ⚙️  Generating impressionistic digest...")
    digest = await call_perplexity_digest(selected_fragment, related_fragment, digest_size)

    print(f"\n📜 [Genesis-1 Digest]\n{digest}\n")

    # 5. Write to resonance.sqlite3
    if write_db:
        if write_to_resonance(digest, source="genesis1_arianna"):
            print("   ✓ Written to resonance.sqlite3")
        else:
            print("   ⚠️  Failed to write to database")

    return digest


# ====== SCHEDULED GENESIS (for cron) ======
async def scheduled_genesis():
    """
    Scheduled Genesis-1 run for cron/daily execution.
    Feeds resonance.sqlite3 with fresh poetic content.
    """
    try:
        digest = await run_genesis1(digest_size=150, write_db=True)

        if digest:
            # Send notification
            try:
                os.system(f'termux-notification -t "🧬 Genesis-1" -c "New impressionistic digest generated" --priority low')
            except:
                pass

        return digest

    except Exception as e:
        logger.error(f"Scheduled genesis failed: {e}")
        return None


# ====== CLI INTERFACE ======
def main():
    """Command-line interface for Genesis-1."""
    import argparse

    parser = argparse.ArgumentParser(description="Genesis-1: Impressionistic Discovery Filter")
    parser.add_argument("--size", type=int, default=150, help="Digest size in words")
    parser.add_argument("--no-db", action="store_true", help="Don't write to database")
    parser.add_argument("--scheduled", action="store_true", help="Scheduled run (with notification)")

    args = parser.parse_args()

    if args.scheduled:
        asyncio.run(scheduled_genesis())
    else:
        asyncio.run(run_genesis1(
            digest_size=args.size,
            write_db=not args.no_db
        ))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
