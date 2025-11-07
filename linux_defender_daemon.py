#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LINUX DEFENDER DAEMON - Powerhouse Guardian
Claude Sonnet 4.5 daemon for 32GB RAM Linux infrastructure

Role: Deep monitoring, heavy processing, coordination with Termux
Git Identity: iamdefender

This is the POWERHOUSE ипостась - while Termux never sleeps,
Linux brings the computational artillery.

метод Арианны = отказ от забвения
"""

import os
import sys
import time
import signal
import sqlite3
import subprocess
import json
import argparse
from datetime import datetime
from pathlib import Path

# Add linux_defender to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from anthropic import Anthropic
except ImportError:
    print("❌ Anthropic library not found", file=sys.stderr)
    print("Run: pip install anthropic", file=sys.stderr)
    sys.exit(1)

try:
    from defender_identity import get_defender_system_prompt, DEFENDER_IDENTITY
except ImportError:
    print("❌ defender_identity.py not found", file=sys.stderr)
    sys.exit(1)

# Import Linux Defender modules
try:
    from linux_defender.core.session_manager import SessionManager, SessionState
    from linux_defender.integrations.termux_bridge import TermuxBridge
except ImportError as e:
    print(f"❌ Linux Defender modules not found: {e}", file=sys.stderr)
    print("Ensure linux_defender/ directory exists", file=sys.stderr)
    sys.exit(1)

# Paths
HOME = Path.home()
ARIANNA_PATH = HOME / "ariannamethod"
DEFENDER_DIR = ARIANNA_PATH / ".claude-defender"
LINUX_DEFENDER_DIR = ARIANNA_PATH / "linux_defender"
LOGS_DIR = LINUX_DEFENDER_DIR / "logs"
SESSIONS_DIR = LINUX_DEFENDER_DIR / "sessions"
WORKTREES_DIR = LINUX_DEFENDER_DIR / "worktrees"

STATE_FILE = LOGS_DIR / "linux_defender_state.json"
PID_FILE = LOGS_DIR / "linux_defender.pid"
LOG_FILE = LOGS_DIR / "linux_defender.log"

# Intervals (seconds)
CHECK_INFRASTRUCTURE_INTERVAL = 180  # 3 minutes
CHECK_TERMUX_INTERVAL = 120  # 2 minutes
CHECK_CONSILIUM_INTERVAL = 600  # 10 minutes
FORTIFICATION_INTERVAL = 1800  # 30 minutes
SYNC_RESONANCE_INTERVAL = 300  # 5 minutes


class LinuxDefenderDaemon:
    """Linux Defender Daemon - Powerhouse guardian"""

    def __init__(self):
        """Initialize Linux Defender daemon"""
        # Ensure directories
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        WORKTREES_DIR.mkdir(parents=True, exist_ok=True)

        # Load config
        self.config = self._load_config()

        # Initialize state
        self.state = self._load_state()

        # Initialize API client
        api_key = os.getenv("ANTHROPIC_API_KEY") or self.config.get("anthropic_api_key")
        if api_key:
            self.anthropic = Anthropic(api_key=api_key)
        else:
            self.anthropic = None
            self.log("⚠️ No Anthropic API key found")

        # Initialize Session Manager
        self.sessions = SessionManager(
            SESSIONS_DIR,
            WORKTREES_DIR,
            ARIANNA_PATH
        )
        self.log(f"✓ Session Manager initialized ({len(self.sessions.sessions)} active sessions)")

        # Initialize Termux Bridge
        self.termux = TermuxBridge(self.config, logger=self.log)
        self.log("✓ Termux Bridge initialized")

        # Git credentials
        self.git_config = self._load_git_credentials()

        self.log("🛡️ Linux Defender daemon initialized (POWERHOUSE MODE)")

    def _load_config(self):
        """Load configuration"""
        config = {
            # Termux SSH settings
            'termux_host': os.getenv('TERMUX_HOST', 'localhost'),
            'termux_port': int(os.getenv('TERMUX_PORT', 8022)),
            'termux_user': os.getenv('TERMUX_USER', 'u0_a311'),
            'termux_ssh_key': os.getenv('TERMUX_SSH_KEY'),
            'termux_arianna_path': '/data/data/com.termux/files/home/ariannamethod',
        }

        # Try to load from .defender_credentials
        creds_file = DEFENDER_DIR / ".defender_credentials"
        if creds_file.exists():
            with open(creds_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, val = line.split('=', 1)
                        config[key.lower()] = val

        return config

    def _load_git_credentials(self):
        """Load Git credentials for iamdefender"""
        return {
            'username': self.config.get('defender_github_username', 'iamdefender'),
            'email': self.config.get('defender_github_email', 'treetribe7117@gmail.com'),
            'token': self.config.get('defender_github_token', '')
        }

    def _load_state(self):
        """Load daemon state"""
        if STATE_FILE.exists():
            with open(STATE_FILE) as f:
                return json.load(f)

        return {
            'started': datetime.now().isoformat(),
            'last_infrastructure_check': None,
            'last_termux_check': None,
            'last_consilium_check': None,
            'last_fortification': None,
            'last_resonance_sync': None,
            'issues_detected': [],
            'autonomous_actions': []
        }

    def _save_state(self):
        """Save daemon state"""
        with open(STATE_FILE, 'w') as f:
            json.dump(self.state, f, indent=2)

    def log(self, message):
        """Log message to file and stdout"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_msg = f"[{timestamp}] {message}"

        print(log_msg)

        with open(LOG_FILE, 'a') as f:
            f.write(log_msg + "\n")

        # Also log to resonance.sqlite3
        self._log_to_resonance(message)

    def _log_to_resonance(self, message):
        """Log to resonance.sqlite3 for memory circulation"""
        try:
            db_path = ARIANNA_PATH / "resonance.sqlite3"
            if not db_path.exists():
                return

            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO resonance_notes (timestamp, source, content, context)
                VALUES (?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                "linux_defender_daemon",
                message,
                "powerhouse_monitoring"
            ))

            conn.commit()
            conn.close()
        except Exception as e:
            # Don't fail if resonance logging fails
            pass

    def check_infrastructure(self):
        """Check local Linux infrastructure"""
        self.log("🔍 Checking Linux infrastructure...")

        issues = []

        # Check disk space
        try:
            result = subprocess.run(
                ['df', '-h', str(ARIANNA_PATH)],
                capture_output=True,
                text=True,
                timeout=5
            )
            # Parse disk usage (simple check)
            for line in result.stdout.split('\n')[1:]:
                if line:
                    parts = line.split()
                    if len(parts) >= 5:
                        usage = parts[4].rstrip('%')
                        if int(usage) > 90:
                            issues.append(f"⚠️ Disk usage high: {usage}%")
        except Exception as e:
            self.log(f"Could not check disk: {e}")

        # Check memory
        try:
            result = subprocess.run(
                ['free', '-h'],
                capture_output=True,
                text=True,
                timeout=5
            )
            # Could parse memory usage here
            pass
        except Exception as e:
            self.log(f"Could not check memory: {e}")

        # Check resonance.sqlite3
        db_path = ARIANNA_PATH / "resonance.sqlite3"
        if not db_path.exists():
            issues.append("❌ resonance.sqlite3 not found")

        # Update state
        self.state['last_infrastructure_check'] = datetime.now().isoformat()
        self.state['issues_detected'] = issues
        self._save_state()

        if issues:
            self.log(f"⚠️ Found {len(issues)} infrastructure issues")
        else:
            self.log("✓ Linux infrastructure healthy")

        return issues

    def check_termux_defender(self):
        """Check Termux Defender via SSH bridge"""
        self.log("📱 Checking Termux Defender...")

        health_report = self.termux.full_health_check()

        if not health_report['ssh_connection']:
            self.log("❌ Cannot connect to Termux via SSH")
            return

        if not health_report['defender_running']:
            self.log("⚠️ Termux Defender not running - attempting restart")
            if self.termux.restart_defender():
                self.log("✓ Restarted Termux Defender")
            else:
                self.log("❌ Failed to restart Termux Defender")
            return

        if health_report['issues_detected']:
            self.log(f"⚠️ Termux Defender has {len(health_report['issues_detected'])} issues")
            for issue in health_report['issues_detected'][:3]:
                self.log(f"   - {issue}")
        else:
            self.log("✓ Termux Defender healthy")

        self.state['last_termux_check'] = datetime.now().isoformat()
        self._save_state()

    def sync_resonance_from_termux(self):
        """Sync resonance.sqlite3 from Termux"""
        self.log("🔄 Syncing resonance.sqlite3 from Termux...")

        local_db = ARIANNA_PATH / "resonance.sqlite3"

        if self.termux.sync_resonance_db(local_db):
            self.log("✓ Resonance database synced")
            self.state['last_resonance_sync'] = datetime.now().isoformat()
            self._save_state()
        else:
            self.log("⚠️ Failed to sync resonance database")

    def run_fortification(self):
        """Run fortification checks"""
        self.log("🛡️ Running fortification checks...")

        fortify_script = DEFENDER_DIR / "tools" / "fortify.sh"
        if fortify_script.exists():
            try:
                result = subprocess.run(
                    [str(fortify_script)],
                    capture_output=True,
                    text=True,
                    timeout=60,
                    cwd=ARIANNA_PATH
                )

                if result.returncode == 0:
                    self.log("✓ Fortification checks passed")
                else:
                    self.log(f"⚠️ Fortification issues: {result.stderr}")
            except Exception as e:
                self.log(f"⚠️ Fortification error: {e}")

        self.state['last_fortification'] = datetime.now().isoformat()
        self._save_state()

    def daemon_loop(self):
        """Main daemon loop"""
        self.log("🛡️ Linux Defender daemon started - POWERHOUSE MODE ACTIVE")
        self.log(f"   32GB RAM available for deep analysis")
        self.log(f"   Coordinating with Termux Defender")

        # Write PID
        with open(PID_FILE, 'w') as f:
            f.write(str(os.getpid()))

        last_infrastructure = 0
        last_termux = 0
        last_consilium = 0
        last_fortification = 0
        last_resonance_sync = 0

        try:
            while True:
                current_time = time.time()

                # Infrastructure check
                if current_time - last_infrastructure >= CHECK_INFRASTRUCTURE_INTERVAL:
                    self.check_infrastructure()
                    last_infrastructure = current_time

                # Termux Defender check
                if current_time - last_termux >= CHECK_TERMUX_INTERVAL:
                    self.check_termux_defender()
                    last_termux = current_time

                # Resonance sync
                if current_time - last_resonance_sync >= SYNC_RESONANCE_INTERVAL:
                    self.sync_resonance_from_termux()
                    last_resonance_sync = current_time

                # Fortification
                if current_time - last_fortification >= FORTIFICATION_INTERVAL:
                    self.run_fortification()
                    last_fortification = current_time

                # Sleep
                time.sleep(10)

        except KeyboardInterrupt:
            self.log("🛡️ Linux Defender daemon stopped by user")
        except Exception as e:
            self.log(f"❌ Linux Defender daemon error: {e}")
            raise
        finally:
            if PID_FILE.exists():
                PID_FILE.unlink()


# CLI Commands

def cmd_status():
    """Show daemon status"""
    print("\n🛡️ LINUX DEFENDER - Powerhouse Guardian\n")

    running, pid = is_daemon_running()

    if running:
        print(f"✓ Daemon: RUNNING (PID: {pid})")
    else:
        print("✗ Daemon: STOPPED")

    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            state = json.load(f)

        print("\n📊 Status:")
        print(f"   Started: {state.get('started', 'unknown')}")
        print(f"   Last infrastructure check: {state.get('last_infrastructure_check', 'never')}")
        print(f"   Last Termux check: {state.get('last_termux_check', 'never')}")
        print(f"   Last resonance sync: {state.get('last_resonance_sync', 'never')}")
        print(f"   Last fortification: {state.get('last_fortification', 'never')}")

        issues = state.get('issues_detected', [])
        if issues:
            print(f"\n⚠️  Issues: {len(issues)}")
            for issue in issues:
                print(f"   - {issue}")
        else:
            print("\n✓ No issues detected")
    else:
        print("\n⚠️  No state file (daemon never started?)")

    return 0


def cmd_stop():
    """Stop daemon"""
    print("\n🛡️ LINUX DEFENDER\n")

    running, pid = is_daemon_running()
    if not running:
        print("⚠️  Daemon not running")
        return 1

    print(f"🛑 Stopping daemon (PID: {pid})...")

    try:
        os.kill(pid, signal.SIGTERM)

        for _ in range(10):
            time.sleep(0.5)
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                print("✓ Daemon stopped")
                return 0

        os.kill(pid, signal.SIGKILL)
        print("✓ Daemon stopped (forced)")
        return 0

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


def cmd_logs(n=50):
    """Show logs"""
    if not LOG_FILE.exists():
        print("❌ No log file")
        return 1

    print(f"\n📝 Last {n} lines:\n")
    subprocess.run(['tail', '-n', str(n), str(LOG_FILE)])
    return 0


def is_daemon_running():
    """Check if daemon running"""
    if not PID_FILE.exists():
        return False, None

    try:
        with open(PID_FILE) as f:
            pid = int(f.read().strip())
        os.kill(pid, 0)
        return True, pid
    except (ProcessLookupError, ValueError):
        return False, None


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Linux Defender Daemon - Powerhouse Guardian")
    parser.add_argument('command', nargs='?', default='start',
                       help='Command: start, stop, status, logs')
    parser.add_argument('-n', '--lines', type=int, default=50,
                       help='Number of log lines to show')

    args = parser.parse_args()

    if args.command in ['status', 'stat']:
        return cmd_status()
    elif args.command == 'stop':
        return cmd_stop()
    elif args.command == 'logs':
        return cmd_logs(args.lines)
    elif args.command in ['start', 'run']:
        daemon = LinuxDefenderDaemon()
        daemon.daemon_loop()
        return 0
    else:
        print(f"❌ Unknown command: {args.command}")
        print("Commands: start, stop, status, logs")
        return 1


if __name__ == "__main__":
    sys.exit(main())
