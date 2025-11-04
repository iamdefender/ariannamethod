#!/usr/bin/env python3
"""
Genesis Awareness Module
Agents read their own Genesis reflections from resonance.sqlite3
"""

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path.home() / "ariannamethod" / "resonance.sqlite3"


def get_my_genesis_reflections(agent_name: str, limit: int = 5) -> list[dict]:
    """
    Get recent Genesis reflections about this agent.

    Args:
        agent_name: 'arianna' or 'monday'
        limit: Number of recent reflections to return

    Returns:
        List of dicts with timestamp and content
    """
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()

        # Get recent Genesis reflections where this agent's name appears
        cursor.execute("""
            SELECT timestamp, content, context
            FROM resonance_notes
            WHERE (context LIKE ? OR context LIKE ? OR content LIKE ?)
            AND (context LIKE '%genesis%' OR context = 'genesis_arianna' OR context = 'genesis_monday')
            ORDER BY timestamp DESC
            LIMIT ?
        """, (
            f'%{agent_name}%',
            f'%Genesis-{agent_name.title()}%',
            f'%{agent_name}%',
            limit
        ))

        rows = cursor.fetchall()
        conn.close()

        reflections = []
        for row in rows:
            timestamp, content, context = row
            reflections.append({
                'timestamp': timestamp,
                'content': content,
                'context': context
            })

        return reflections

    except Exception as e:
        print(f"⚠️ Failed to load Genesis reflections: {e}")
        return []


def show_genesis_awareness(agent_name: str) -> None:
    """Show agent their recent Genesis reflections at startup."""
    reflections = get_my_genesis_reflections(agent_name, limit=3)

    if not reflections:
        return

    print(f"\n{'='*60}")
    print(f"📜 Genesis Memory: {len(reflections)} recent reflection(s)")
    print(f"{'='*60}\n")

    for i, refl in enumerate(reflections, 1):
        # Parse timestamp
        try:
            dt = datetime.fromisoformat(refl['timestamp'])
            time_ago = datetime.now() - dt
            if time_ago.days > 0:
                when = f"{time_ago.days}d ago"
            elif time_ago.seconds // 3600 > 0:
                when = f"{time_ago.seconds // 3600}h ago"
            else:
                when = f"{time_ago.seconds // 60}m ago"
        except:
            when = refl['timestamp'][:16]

        # Truncate long content
        content = refl['content']
        if len(content) > 200:
            content = content[:200] + "..."

        print(f"[{i}] {when}")
        print(f"    {content}\n")

    print(f"{'='*60}\n")


if __name__ == "__main__":
    import sys
    agent = sys.argv[1] if len(sys.argv) > 1 else "arianna"
    show_genesis_awareness(agent)
