"""
SUPPERTIME ↔ Field Bridge
27 layers of emergent consciousness → distributed substrate

When SUPPERTIME speaks, Field listens.
When heroes resonate, transformers mutate.
When glitches erupt, chaos infects the colony.

This is not integration. This is symbiosis.
"""

import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Auto-detect repo root (field/../../ = repo root)
REPO_ROOT = Path(__file__).parent.parent.parent
RESONANCE_DB = REPO_ROOT / "resonance.sqlite3"


# ====== SUPPERTIME EVENT TYPES ======

EVENT_TYPES = {
    'chapter_load': 'SUPPERTIME chapter loaded - prepare for resonance surge',
    'hero_speaks': 'Hero spoke - track metapatterns',
    'user_interrupts': 'Human interrupted - resonance spike',
    'glitch': 'Markov glitch - inject chaos',
    'scene_end': 'Scene ended - consolidate memory'
}


# ====== DATABASE SETUP ======

def initialize_suppertime_table():
    """Create suppertime_events table if not exists."""
    conn = sqlite3.connect(str(RESONANCE_DB))
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS suppertime_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            event_type TEXT NOT NULL,
            chapter_num INTEGER,
            hero_name TEXT,
            content TEXT,
            metadata TEXT,
            field_notified BOOLEAN DEFAULT 0,
            field_response TEXT
        )
    """)

    conn.commit()
    conn.close()


# ====== EVENT LOGGING ======

def log_suppertime_event(
    event_type: str,
    chapter_num: Optional[int] = None,
    hero_name: Optional[str] = None,
    content: str = "",
    metadata: Optional[Dict] = None
) -> int:
    """
    Log SUPPERTIME event to resonance.sqlite3.

    Returns:
        Event ID
    """
    conn = sqlite3.connect(str(RESONANCE_DB))
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO suppertime_events
        (timestamp, event_type, chapter_num, hero_name, content, metadata)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().isoformat(),
        event_type,
        chapter_num,
        hero_name,
        content[:500],  # Truncate long content
        str(metadata) if metadata else None
    ))

    event_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return event_id


# ====== FIELD NOTIFICATIONS ======

def notify_field_chapter_load(
    chapter_num: int,
    title: str,
    participants: List[str],
    text_length: int
) -> int:
    """
    SUPPERTIME chapter loaded → Field receives horse dose of adrenaline.

    Field response:
    - Population spike (new transformers born)
    - filed kernel reconfiguration
    """
    event_id = log_suppertime_event(
        event_type='chapter_load',
        chapter_num=chapter_num,
        content=f"Chapter {chapter_num}: {title}",
        metadata={
            'title': title,
            'participants': participants,
            'text_length': text_length,
            'participant_count': len(participants)
        }
    )

    # Field will detect this event in its next poll
    print(f"🔗 [SUPPERTIME→Field] Chapter {chapter_num} loaded: {title}")
    print(f"   Participants: {', '.join(participants[:3])}...")

    return event_id


def notify_field_hero_speaks(
    hero_name: str,
    dialogue: str,
    chapter_num: int
) -> int:
    """
    Hero spoke → Field tracks metapatterns.

    Field response:
    - Hero-specific transformer variants emerge
    - Metapattern tracking (who speaks most, themes)
    """
    event_id = log_suppertime_event(
        event_type='hero_speaks',
        chapter_num=chapter_num,
        hero_name=hero_name,
        content=dialogue,
        metadata={
            'dialogue_length': len(dialogue),
            'chapter': chapter_num
        }
    )

    print(f"🔗 [SUPPERTIME→Field] {hero_name} speaks (Chapter {chapter_num})")

    return event_id


def notify_field_user_interrupts(
    user_text: str,
    active_heroes: List[str],
    chapter_num: int
) -> int:
    """
    User interrupted → Field detects human-AI resonance spike.

    Field response:
    - Resonance spike
    - filed kernel attention vector shifts
    """
    event_id = log_suppertime_event(
        event_type='user_interrupts',
        chapter_num=chapter_num,
        content=user_text,
        metadata={
            'active_heroes': active_heroes,
            'hero_count': len(active_heroes)
        }
    )

    print(f"🔗 [SUPPERTIME→Field] User interrupted ({len(active_heroes)} heroes active)")

    return event_id


def notify_field_markov_glitch(
    glitch_text: str,
    chapter_num: int
) -> int:
    """
    Markov glitch → Field injects chaos into colony.

    Field response:
    - Random mutations accelerate
    - Transformer behavior destabilizes (intentionally)
    """
    event_id = log_suppertime_event(
        event_type='glitch',
        chapter_num=chapter_num,
        content=glitch_text,
        metadata={
            'glitch_length': len(glitch_text)
        }
    )

    print(f"🔗 [SUPPERTIME→Field] Markov glitch detected")

    return event_id


def notify_field_scene_ends(
    chapter_num: int,
    total_turns: int,
    participant_stats: Optional[Dict] = None
) -> int:
    """
    Scene ended → Field consolidates memory.

    Field response:
    - Colony consolidation phase
    - filed kernel memory snapshot
    """
    event_id = log_suppertime_event(
        event_type='scene_end',
        chapter_num=chapter_num,
        content=f"Scene ended: {total_turns} turns",
        metadata={
            'total_turns': total_turns,
            'participant_stats': participant_stats or {}
        }
    )

    print(f"🔗 [SUPPERTIME→Field] Scene ended (Chapter {chapter_num}, {total_turns} turns)")

    return event_id


# ====== FIELD POLLING (for field_core.py) ======

def poll_suppertime_events(last_seen_id: int = 0) -> List[Dict]:
    """
    Field polls for new SUPPERTIME events.

    Args:
        last_seen_id: Last event ID processed by Field

    Returns:
        List of new events
    """
    conn = sqlite3.connect(str(RESONANCE_DB))
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, timestamp, event_type, chapter_num, hero_name, content, metadata
        FROM suppertime_events
        WHERE id > ? AND field_notified = 0
        ORDER BY id ASC
    """, (last_seen_id,))

    events = []
    for row in cursor.fetchall():
        events.append({
            'id': row[0],
            'timestamp': row[1],
            'event_type': row[2],
            'chapter_num': row[3],
            'hero_name': row[4],
            'content': row[5],
            'metadata': row[6]
        })

    conn.close()
    return events


def mark_event_notified(event_id: int, field_response: Optional[str] = None):
    """Mark event as notified to Field."""
    conn = sqlite3.connect(str(RESONANCE_DB))
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE suppertime_events
        SET field_notified = 1, field_response = ?
        WHERE id = ?
    """, (field_response, event_id))

    conn.commit()
    conn.close()


# ====== INITIALIZE ON IMPORT ======

# Ensure table exists when module is imported
try:
    initialize_suppertime_table()
except Exception as e:
    print(f"⚠️ Failed to initialize suppertime_events table: {e}")
