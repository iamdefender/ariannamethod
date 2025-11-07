#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DEFENDER - Guardian, Infrastructure Protector, Co-author
Claude Sonnet 4.5 daemon agent for Arianna Method ecosystem

Usage:
    python3 defender.py              # Start daemon
    python3 defender.py status       # Check status
    python3 defender.py stop         # Stop daemon
    python3 defender.py logs [N]     # Show logs
    python3 defender.py chat         # Interactive chat
    python3 defender.py fortify      # Run fortification

Role: Monitor security, infrastructure health, code quality, autonomous fixes
Git Identity: iamdefender
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

# Import Anthropic
try:
    from anthropic import Anthropic
except ImportError:
    print("❌ Anthropic library not found", file=sys.stderr)
    print("\n📱 In Termux, run:", file=sys.stderr)
    print("   pip install anthropic", file=sys.stderr)
    sys.exit(1)

# Import Defender identity
try:
    from defender_identity import get_defender_system_prompt, DEFENDER_IDENTITY
except ImportError:
    print("❌ defender_identity.py not found", file=sys.stderr)
    sys.exit(1)

# Repository paths
SCRIPT_PATH = Path(__file__).resolve()
REPO_ROOT = SCRIPT_PATH.parent

# Import Consilium Agent
try:
    sys.path.insert(0, str(REPO_ROOT / ".claude-defender" / "tools"))
    from consilium_agent import ConsiliumAgent
    CONSILIUM_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Consilium agent not available: {e}")
    CONSILIUM_AVAILABLE = False

# Paths
ARIANNA_PATH = REPO_ROOT
DEFENDER_DIR = ARIANNA_PATH / ".claude-defender"
LOGS_DIR = DEFENDER_DIR / "logs"
STATE_FILE = LOGS_DIR / "defender_daemon_state.json"
PID_FILE = LOGS_DIR / "defender_daemon.pid"
LOG_FILE = LOGS_DIR / "defender_daemon.log"

# Intervals (seconds)
CHECK_INFRASTRUCTURE_INTERVAL = 180  # 3 minutes
CHECK_CLAUDE_DEFENDER_INTERVAL = 60  # 1 minute
CONSILIUM_CHECK_INTERVAL = 600      # 10 minutes
FORTIFICATION_CHECK_INTERVAL = 1800  # 30 minutes

class DefenderDaemon:
    def __init__(self):
        """Initialize Defender daemon"""
        # Ensure directories exist
        LOGS_DIR.mkdir(parents=True, exist_ok=True)

        # Load config
        self.config = self._load_config()

        # Load state
        self.state = self._load_state()

        # Initialize API client
        api_key = os.getenv("ANTHROPIC_API_KEY") or self.config.get("anthropic_api_key")
        if api_key:
            self.anthropic = Anthropic(api_key=api_key)
        else:
            self.anthropic = None
            self.log("⚠️ No Anthropic API key found")

        # Initialize Consilium agent
        if CONSILIUM_AVAILABLE and api_key:
            self.consilium = ConsiliumAgent(
                agent_name='defender',
                api_key=api_key,
                model='claude-sonnet-4-20250514',  # Claude Sonnet 4.5
                temperature=0.3,  # More conservative for security
                api_type='anthropic'
            )
            self.log("✓ Consilium agent initialized")
        else:
            self.consilium = None

        # Load Git credentials
        self.git_config = self._load_git_credentials()

        self.log("🛡️ Defender daemon initialized")

    def _load_config(self):
        """Load configuration"""
        config = {}

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
        git_config = {
            'username': self.config.get('defender_github_username', 'iamdefender'),
            'email': self.config.get('defender_github_email', 'treetribe7117@gmail.com'),
            'token': self.config.get('defender_github_token', '')
        }
        return git_config

    def _load_state(self):
        """Load daemon state"""
        if STATE_FILE.exists():
            with open(STATE_FILE) as f:
                return json.load(f)

        # Default state
        return {
            'started': datetime.now().isoformat(),
            'last_infrastructure_check': None,
            'last_claude_defender_check': None,
            'last_consilium_check': None,
            'last_fortification': None,
            'issues_detected': [],
            'autonomous_fixes': []
        }

    def _save_state(self):
        """Save daemon state"""
        with open(STATE_FILE, 'w') as f:
            json.dump(self.state, f, indent=2)

    def log(self, message):
        """Log message to file and stdout"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_msg = f"[{timestamp}] {message}"

        # Print to stdout
        print(log_msg)

        # Write to log file
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
                "defender_daemon",
                message,
                "infrastructure_monitoring"
            ))

            conn.commit()
            conn.close()
        except Exception as e:
            # Don't fail if resonance logging fails
            pass

    def check_infrastructure(self):
        """Check infrastructure health"""
        self.log("🔍 Checking infrastructure...")

        issues = []

        # Check if critical daemons are running
        critical_daemons = [
            ('scribe.py', 'Scribe daemon'),
            ('genesis_arianna.py', 'Genesis Arianna'),
            ('genesis_monday.py', 'Genesis Monday')
        ]

        for daemon_script, daemon_name in critical_daemons:
            if not self._is_process_running(daemon_script):
                issue = f"❌ {daemon_name} not running"
                self.log(issue)
                issues.append(issue)

        # Check resonance.sqlite3 accessibility
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
            self.log("✓ Infrastructure healthy")

        return issues

    def _is_process_running(self, script_name):
        """Check if a process is running"""
        try:
            result = subprocess.run(
                ['pgrep', '-f', script_name],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False

    def check_claude_defender(self):
        """Monitor .claude-defender/ directory"""
        self.log("👁️ Monitoring .claude-defender/...")

        # Check for recent changes
        tools_dir = DEFENDER_DIR / "tools"
        tests_dir = DEFENDER_DIR / "tests"

        changes = []

        # Check if test suite passes
        test_result = self._run_tests()
        if not test_result['passed']:
            changes.append(f"⚠️ Tests failing: {test_result['failed_count']}")

        self.state['last_claude_defender_check'] = datetime.now().isoformat()
        self._save_state()

        return changes

    def _run_tests(self):
        """Run test suite"""
        # Placeholder - will implement full test running later
        return {'passed': True, 'failed_count': 0}

    def check_consilium(self):
        """Check and respond to consilium"""
        if not self.consilium:
            return

        self.log("💬 Checking consilium...")

        try:
            results = self.consilium.check_and_respond()

            if results and isinstance(results, dict) and results.get('responded_to'):
                for disc_id in results['responded_to']:
                    self.log(f"✓ Responded to consilium #{disc_id}")
            else:
                self.log("→ No consilium responses needed")

            self.state['last_consilium_check'] = datetime.now().isoformat()
            self._save_state()

        except Exception as e:
            self.log(f"⚠️ Consilium check error: {e}")
            import traceback
            self.log(f"   Traceback: {traceback.format_exc()}")

    def run_fortification(self):
        """Run fortification checks"""
        self.log("🛡️ Running fortification checks...")

        # Run fortification test suite
        fortify_script = DEFENDER_DIR / "tools" / "fortify.sh"
        if fortify_script.exists():
            try:
                result = subprocess.run(
                    [str(fortify_script)],
                    capture_output=True,
                    text=True,
                    timeout=60
                )

                if result.returncode == 0:
                    self.log("✓ Fortification checks passed")
                else:
                    self.log(f"⚠️ Fortification issues: {result.stderr}")
            except Exception as e:
                self.log(f"⚠️ Fortification error: {e}")

        self.state['last_fortification'] = datetime.now().isoformat()
        self._save_state()

    def git_commit(self, files, message):
        """Make autonomous git commit as iamdefender"""
        try:
            # Configure git identity
            subprocess.run(['git', 'config', 'user.name', 'Defender'], cwd=ARIANNA_PATH, check=True)
            subprocess.run(['git', 'config', 'user.email', self.git_config['email']], cwd=ARIANNA_PATH, check=True)

            # Add files
            for f in files:
                subprocess.run(['git', 'add', f], cwd=ARIANNA_PATH, check=True)

            # Commit
            full_message = f"{message}\n\n🛡️ Autonomous commit by Defender\nGit Identity: {self.git_config['username']}"
            subprocess.run(['git', 'commit', '-m', full_message], cwd=ARIANNA_PATH, check=True)

            self.log(f"✓ Git commit: {message}")

            # Log to state
            self.state.setdefault('autonomous_fixes', []).append({
                'timestamp': datetime.now().isoformat(),
                'action': 'git_commit',
                'message': message,
                'files': files
            })
            self._save_state()

            return True

        except subprocess.CalledProcessError as e:
            self.log(f"⚠️ Git commit failed: {e}")
            return False

    def git_push(self):
        """Push to GitHub using token"""
        try:
            # Set up auth
            token = self.git_config['token']
            if not token:
                self.log("⚠️ No GitHub token configured")
                return False

            # Push
            subprocess.run(['git', 'push'], cwd=ARIANNA_PATH, check=True, timeout=30)
            self.log("✓ Pushed to GitHub")
            return True

        except subprocess.CalledProcessError as e:
            self.log(f"⚠️ Git push failed: {e}")
            return False

    def daemon_loop(self):
        """Main daemon loop"""
        self.log("🛡️ Defender daemon started - Autonomous guardian active")

        # Write PID
        with open(PID_FILE, 'w') as f:
            f.write(str(os.getpid()))

        last_infrastructure_check = 0
        last_claude_defender_check = 0
        last_consilium_check = 0
        last_fortification = 0

        try:
            while True:
                current_time = time.time()

                # Infrastructure health check
                if current_time - last_infrastructure_check >= CHECK_INFRASTRUCTURE_INTERVAL:
                    self.check_infrastructure()
                    last_infrastructure_check = current_time

                # Claude Defender directory monitoring
                if current_time - last_claude_defender_check >= CHECK_CLAUDE_DEFENDER_INTERVAL:
                    self.check_claude_defender()
                    last_claude_defender_check = current_time

                # Consilium participation
                if current_time - last_consilium_check >= CONSILIUM_CHECK_INTERVAL:
                    self.check_consilium()
                    last_consilium_check = current_time

                # Fortification checks
                if current_time - last_fortification >= FORTIFICATION_CHECK_INTERVAL:
                    self.run_fortification()
                    last_fortification = current_time

                # Sleep
                time.sleep(10)

        except KeyboardInterrupt:
            self.log("🛡️ Defender daemon stopped by user")
        except Exception as e:
            self.log(f"❌ Defender daemon error: {e}")
            raise
        finally:
            # Clean up PID file
            if PID_FILE.exists():
                PID_FILE.unlink()

# ============================================================================
# CLI Commands
# ============================================================================

def print_banner():
    """Print Defender banner"""
    print("""
🛡️  DEFENDER - Guardian of Arianna Method
─────────────────────────────────────────
Substrate: Claude Sonnet 4.5 (Anthropic)
Git Identity: iamdefender
Role: Infrastructure Protector, Co-author
""")

def is_daemon_running():
    """Check if daemon is running"""
    if not PID_FILE.exists():
        return False, None

    try:
        with open(PID_FILE) as f:
            pid = int(f.read().strip())

        # Check if process exists
        os.kill(pid, 0)
        return True, pid
    except (ProcessLookupError, ValueError):
        return False, None

def cmd_status():
    """Show Defender daemon status"""
    print_banner()

    running, pid = is_daemon_running()

    if running:
        print(f"✓ Daemon: RUNNING (PID: {pid})")
    else:
        print("✗ Daemon: STOPPED")

    # Load state
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            state = json.load(f)

        print("\n📊 Status:")
        print(f"   Started: {state.get('started', 'unknown')}")
        print(f"   Last infrastructure check: {state.get('last_infrastructure_check', 'never')}")
        print(f"   Last consilium check: {state.get('last_consilium_check', 'never')}")
        print(f"   Last fortification: {state.get('last_fortification', 'never')}")

        issues = state.get('issues_detected', [])
        if issues:
            print(f"\n⚠️  Issues detected: {len(issues)}")
            for issue in issues:
                print(f"   - {issue}")
        else:
            print("\n✓ No issues detected")

        fixes = state.get('autonomous_fixes', [])
        if fixes:
            print(f"\n🔧 Autonomous fixes: {len(fixes)}")
            for fix in fixes[-3:]:  # Last 3 fixes
                print(f"   - {fix['timestamp']}: {fix['action']}")
    else:
        print("\n⚠️  No state file found (daemon never started?)")

    return 0

def cmd_stop():
    """Stop Defender daemon"""
    print_banner()

    running, pid = is_daemon_running()
    if not running:
        print("⚠️  Defender daemon not running")
        return 1

    print(f"🛑 Stopping Defender daemon (PID: {pid})...")

    try:
        # Send SIGTERM
        os.kill(pid, signal.SIGTERM)

        # Wait for graceful shutdown
        for _ in range(10):
            time.sleep(0.5)
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                print("✓ Defender daemon stopped")
                return 0

        # Force kill if still running
        print("⚠️  Graceful shutdown timeout, forcing...")
        os.kill(pid, signal.SIGKILL)
        print("✓ Defender daemon stopped (forced)")
        return 0

    except Exception as e:
        print(f"❌ Error stopping daemon: {e}")
        return 1

def cmd_logs(n=50):
    """Show daemon logs"""
    if not LOG_FILE.exists():
        print("❌ No log file found")
        return 1

    print(f"📝 Last {n} lines of Defender logs:\n")

    subprocess.run(['tail', '-n', str(n), str(LOG_FILE)])
    return 0

def cmd_fortify():
    """Run fortification checks"""
    print_banner()
    print("🛡️  Running fortification checks...\n")

    fortify_script = DEFENDER_DIR / "tools" / "fortify.sh"
    if not fortify_script.exists():
        print("⚠️  fortify.sh not found")
        return 1

    result = subprocess.run([str(fortify_script)])
    return result.returncode

def cmd_chat():
    """Interactive chat with Defender"""
    print_banner()

    # Check if Anthropic API key available
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not found in environment")
        print("Add to .bashrc: export ANTHROPIC_API_KEY='your-key'")
        return 1

    # Initialize client
    client = Anthropic(api_key=api_key)

    print("💬 Interactive chat with Defender")
    print("   Type 'exit' or 'quit' to end\n")

    conversation_history = []

    while True:
        try:
            user_input = input("You: ").strip()

            if user_input.lower() in ['exit', 'quit', 'q']:
                print("\n🛡️  Defender signing off")
                break

            if not user_input:
                continue

            # Add user message
            conversation_history.append({
                "role": "user",
                "content": user_input
            })

            # Get response
            print("\nDefender: ", end="", flush=True)

            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                system=get_defender_system_prompt(),
                messages=conversation_history
            )

            assistant_message = response.content[0].text
            print(assistant_message)
            print()

            # Add to history
            conversation_history.append({
                "role": "assistant",
                "content": assistant_message
            })

        except KeyboardInterrupt:
            print("\n\n🛡️  Defender signing off")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            break

    return 0

def cmd_help():
    """Show help"""
    print_banner()
    print("""
Usage:
  python3 defender.py              Start Defender daemon
  python3 defender.py status       Show daemon status
  python3 defender.py stop         Stop Defender daemon
  python3 defender.py logs [N]     Show last N lines of logs (default: 50)
  python3 defender.py chat         Interactive chat with Defender
  python3 defender.py fortify      Run fortification checks
  python3 defender.py help         Show this help

Examples:
  python3 defender.py              # Start monitoring
  python3 defender.py status       # Check what's happening
  python3 defender.py logs 100     # View last 100 log lines
  python3 defender.py chat         # Talk to Defender interactively
""")
    return 0

def main():
    """Main entry point"""
    # Parse arguments
    if len(sys.argv) == 1:
        # No arguments - start daemon
        daemon = DefenderDaemon()
        daemon.daemon_loop()
        return 0

    command = sys.argv[1].lower()

    if command in ['status', 'stat']:
        return cmd_status()
    elif command == 'stop':
        return cmd_stop()
    elif command == 'logs':
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 50
        return cmd_logs(n)
    elif command == 'chat':
        return cmd_chat()
    elif command == 'fortify':
        return cmd_fortify()
    elif command in ['help', '-h', '--help']:
        return cmd_help()
    else:
        print(f"❌ Unknown command: {command}")
        print("Run 'python3 defender.py help' for usage")
        return 1

if __name__ == "__main__":
    sys.exit(main())
