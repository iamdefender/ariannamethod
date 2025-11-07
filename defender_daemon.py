#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DEFENDER - Guardian, Infrastructure Protector, Co-author
Claude Sonnet 4.5 daemon agent for Arianna Method ecosystem

Role: Monitor security, infrastructure health, code quality, autonomous fixes
Git Identity: iamdefender
"""

import os
import sys
import time
import sqlite3
import subprocess
import json
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

# Import Consilium Agent
try:
    sys.path.insert(0, str(Path.home() / "ariannamethod" / ".claude-defender" / "tools"))
    from consilium_agent import ConsiliumAgent
    CONSILIUM_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Consilium agent not available: {e}")
    CONSILIUM_AVAILABLE = False

# Paths
HOME = Path.home()
ARIANNA_PATH = HOME / "ariannamethod"
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

        # Initialize state
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

def main():
    """Main entry point"""
    daemon = DefenderDaemon()
    daemon.daemon_loop()

if __name__ == "__main__":
    main()
