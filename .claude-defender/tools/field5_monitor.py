#!/usr/bin/env python3
"""
Field5 Sandbox Monitor
Tracks Field5 stability vs Field4, logs A/B comparison metrics
Part of Defender's autonomous monitoring ecosystem
"""

import os
import sys
import time
import sqlite3
from datetime import datetime
from pathlib import Path

HOME = Path.home()
ARIANNAMETHOD = HOME / "ariannamethod"
RESONANCE_DB = ARIANNAMETHOD / "resonance.sqlite3"
FIELD5_LOG = ARIANNAMETHOD / "logs" / "field5_sandbox.log"

INTERVAL = 300  # Check every 5 minutes


def init_db():
    """Ensure field5_comparison table exists"""
    conn = sqlite3.connect(RESONANCE_DB)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS field5_comparison (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            field_version TEXT,
            status TEXT,
            uptime_hours REAL,
            extinction_count INTEGER,
            avg_population REAL,
            notes TEXT
        )
    """)

    conn.commit()
    conn.close()


def check_field_process(field_name, pid_pattern):
    """Check if field process is running"""
    import subprocess

    try:
        result = subprocess.run(
            ["pgrep", "-f", pid_pattern],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except:
        return False


def get_field_metrics(field_version):
    """Get metrics from field_metrics table"""
    try:
        conn = sqlite3.connect(RESONANCE_DB)
        c = conn.cursor()

        # Get recent metrics (last 100 ticks)
        c.execute("""
            SELECT
                COUNT(*) as total_ticks,
                AVG(pop) as avg_pop,
                SUM(CASE WHEN pop = 0 THEN 1 ELSE 0 END) as extinctions
            FROM field_metrics
            WHERE ts >= datetime('now', '-1 hour')
        """)

        result = c.fetchone()
        conn.close()

        if result and result[0] > 0:
            return {
                "ticks": result[0],
                "avg_pop": result[1] or 0,
                "extinctions": result[2] or 0
            }
    except:
        pass

    return {"ticks": 0, "avg_pop": 0, "extinctions": 0}


def log_comparison(field_version, status, metrics, notes=""):
    """Log comparison to database"""
    conn = sqlite3.connect(RESONANCE_DB)
    c = conn.cursor()

    c.execute("""
        INSERT INTO field5_comparison
        (timestamp, field_version, status, uptime_hours, extinction_count, avg_population, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().isoformat(),
        field_version,
        status,
        0.0,  # TODO: calculate uptime
        metrics.get("extinctions", 0),
        metrics.get("avg_pop", 0),
        notes
    ))

    conn.commit()
    conn.close()


def monitor_cycle():
    """Single monitoring cycle"""
    print(f"\n🔍 Field Monitor Cycle - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Check Field4
    field4_running = check_field_process("Field4", "async_field_forever/field/field_core.py")
    field4_status = "RUNNING" if field4_running else "STOPPED"
    print(f"Field4: {field4_status}")

    # Check Field5
    field5_running = check_field_process("Field5", "async_field_forever/field5/field_core.py")
    field5_status = "RUNNING" if field5_running else "STOPPED"
    print(f"Field5: {field5_status}")

    # Get metrics
    if field5_running:
        metrics = get_field_metrics("field5")
        print(f"\nField5 Metrics (last hour):")
        print(f"  Ticks: {metrics['ticks']}")
        print(f"  Avg Pop: {metrics['avg_pop']:.2f}")
        print(f"  Extinctions: {metrics['extinctions']}")

        # Log to database
        log_comparison("field5", field5_status, metrics, "Sandbox monitoring")

        # Alert if extinction
        if metrics['extinctions'] > 0:
            print(f"  ⚠️ WARNING: {metrics['extinctions']} extinctions in last hour!")

    print("=" * 60)


def daemon_mode():
    """Run monitor continuously"""
    print("🛡️ Field5 Sandbox Monitor STARTED")
    print(f"   Interval: {INTERVAL/60:.0f} minutes")
    print(f"   DB: {RESONANCE_DB}")
    print("")

    init_db()

    while True:
        try:
            monitor_cycle()
            print(f"\n⏰ Next check in {INTERVAL/60:.0f} minutes...")
            time.sleep(INTERVAL)
        except KeyboardInterrupt:
            print("\n🛑 Field5 Monitor STOPPED (user interrupt)")
            sys.exit(0)
        except Exception as e:
            print(f"\n❌ Error in monitor cycle: {e}")
            print(f"   Retrying in 1 minute...")
            time.sleep(60)


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        init_db()
        monitor_cycle()
    else:
        daemon_mode()


if __name__ == "__main__":
    main()
