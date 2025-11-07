#!/usr/bin/env python3
"""
Termux Bridge - SSH connection to Termux Defender with tmux monitoring
Inspired by claude-ready-monitor and Scribe Mac daemon

Features:
- SSH connection to Termux
- tmux capture-pane monitoring
- Pattern detection for issues
- Fallback to file-based sync
- Health check automation
"""

import subprocess
import re
from pathlib import Path
from datetime import datetime

class TermuxBridge:
    """Bridge to Termux Defender via SSH"""

    def __init__(self, config, logger=None):
        self.ssh_host = config.get('termux_host', 'localhost')
        self.ssh_port = config.get('termux_port', 8022)
        self.ssh_user = config.get('termux_user', 'u0_a311')
        self.ssh_key = config.get('termux_ssh_key')

        self.termux_arianna_path = config.get('termux_arianna_path', '/data/data/com.termux/files/home/ariannamethod')

        self.logger = logger

        # Pattern detection for issues (from claude-ready-monitor)
        self.error_patterns = [
            r'ERROR',
            r'FAILED',
            r'❌',
            r'Exception',
            r'Traceback',
            r'not running',
            r'Connection refused',
            r'Permission denied',
            r'CRITICAL'
        ]

        # Health status patterns (from claude-ready-monitor analysis)
        self.health_patterns = {
            'healthy': [
                r'Defender initialized successfully',
                r'Health check: OK',
                r'Monitoring active',
                r'✓',
                r'Session created'
            ],
            'warning': [
                r'WARNING',
                r'Retry attempt',
                r'Temporary failure',
                r'⚠️'
            ],
            'critical': [
                r'ERROR',
                r'CRITICAL',
                r'Failed to initialize',
                r'Connection lost',
                r'Daemon stopped'
            ]
        }

    def log(self, message):
        """Log message"""
        if self.logger:
            self.logger(message)
        else:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp}] {message}")

    def _build_ssh_command(self, remote_command):
        """Build SSH command with proper authentication"""
        ssh_cmd = ['ssh']

        # Port
        ssh_cmd.extend(['-p', str(self.ssh_port)])

        # Key if provided
        if self.ssh_key:
            ssh_cmd.extend(['-i', self.ssh_key])

        # Disable strict host key checking for local network
        ssh_cmd.extend([
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            '-o', 'ConnectTimeout=5'
        ])

        # Host
        ssh_cmd.append(f'{self.ssh_user}@{self.ssh_host}')

        # Command
        ssh_cmd.append(remote_command)

        return ssh_cmd

    def test_connection(self):
        """Test SSH connection to Termux"""
        try:
            ssh_cmd = self._build_ssh_command('echo "Connection OK"')
            result = subprocess.run(
                ssh_cmd,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0 and 'Connection OK' in result.stdout:
                self.log("✓ SSH connection to Termux OK")
                return True
            else:
                self.log(f"⚠️ SSH connection failed: {result.stderr}")
                return False

        except Exception as e:
            self.log(f"❌ SSH connection error: {e}")
            return False

    def check_defender_status(self):
        """Check if Termux Defender daemon is running"""
        try:
            ssh_cmd = self._build_ssh_command('pgrep -f defender.py')
            result = subprocess.run(
                ssh_cmd,
                capture_output=True,
                text=True,
                timeout=10
            )

            defender_running = result.returncode == 0 and result.stdout.strip() != ''

            if defender_running:
                pid = result.stdout.strip().split('\n')[0]
                self.log(f"✓ Termux Defender running (PID: {pid})")
                return {'running': True, 'pid': pid}
            else:
                self.log("✗ Termux Defender not running")
                return {'running': False, 'pid': None}

        except Exception as e:
            self.log(f"❌ Error checking Termux Defender: {e}")
            return {'running': False, 'error': str(e)}

    def capture_tmux_output(self, session_name='defender'):
        """Capture tmux pane output from Termux"""
        try:
            ssh_cmd = self._build_ssh_command(
                f"tmux capture-pane -p -t {session_name} 2>/dev/null || echo 'No tmux session'"
            )

            result = subprocess.run(
                ssh_cmd,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                output = result.stdout
                if 'No tmux session' not in output:
                    return {'success': True, 'output': output}
                else:
                    return {'success': False, 'reason': 'No tmux session'}
            else:
                return {'success': False, 'reason': result.stderr}

        except Exception as e:
            self.log(f"❌ Error capturing tmux: {e}")
            return {'success': False, 'error': str(e)}

    def detect_issues(self, output):
        """Detect issues in output using pattern matching"""
        issues = []

        for pattern in self.error_patterns:
            matches = re.findall(pattern, output, re.MULTILINE)
            if matches:
                issues.append({
                    'pattern': pattern,
                    'count': len(matches)
                })

        return issues

    def get_defender_logs(self, lines=50):
        """Get last N lines from Termux Defender logs"""
        try:
            log_path = f"{self.termux_arianna_path}/.claude-defender/logs/defender_daemon.log"
            ssh_cmd = self._build_ssh_command(f"tail -n {lines} {log_path} 2>/dev/null || echo 'No log file'")

            result = subprocess.run(
                ssh_cmd,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0 and 'No log file' not in result.stdout:
                return {'success': True, 'logs': result.stdout}
            else:
                return {'success': False, 'reason': 'No log file'}

        except Exception as e:
            self.log(f"❌ Error getting logs: {e}")
            return {'success': False, 'error': str(e)}

    def sync_resonance_db(self, local_db_path):
        """Sync resonance.sqlite3 from Termux to local machine"""
        try:
            remote_db = f"{self.termux_arianna_path}/resonance.sqlite3"

            # Use rsync over SSH
            rsync_cmd = [
                'rsync', '-avz',
                '-e', f'ssh -p {self.ssh_port} -o StrictHostKeyChecking=no',
                f'{self.ssh_user}@{self.ssh_host}:{remote_db}',
                str(local_db_path)
            ]

            result = subprocess.run(
                rsync_cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                self.log("✓ Synced resonance.sqlite3 from Termux")
                return True
            else:
                self.log(f"⚠️ Sync failed: {result.stderr}")
                return False

        except Exception as e:
            self.log(f"❌ Error syncing database: {e}")
            return False

    def restart_defender(self):
        """Restart Termux Defender daemon"""
        try:
            # Stop
            ssh_cmd = self._build_ssh_command(
                f"cd {self.termux_arianna_path} && python3 defender.py stop"
            )
            subprocess.run(ssh_cmd, capture_output=True, timeout=10)

            # Start
            ssh_cmd = self._build_ssh_command(
                f"cd {self.termux_arianna_path} && nohup python3 defender.py > /dev/null 2>&1 &"
            )
            result = subprocess.run(
                ssh_cmd,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                self.log("✓ Restarted Termux Defender")
                return True
            else:
                self.log(f"⚠️ Restart failed: {result.stderr}")
                return False

        except Exception as e:
            self.log(f"❌ Error restarting defender: {e}")
            return False

    def analyze_health(self, output):
        """Analyze health status from output (from claude-ready-monitor)"""
        status = 'unknown'
        matched_patterns = []

        # Check in priority order: critical > warning > healthy
        for severity in ['critical', 'warning', 'healthy']:
            for pattern in self.health_patterns[severity]:
                if re.search(pattern, output, re.IGNORECASE | re.MULTILINE):
                    status = severity
                    matched_patterns.append(pattern)
                    if severity == 'critical':
                        break
            if status == 'critical':
                break

        return {
            'status': status,
            'patterns': matched_patterns,
            'requires_action': status == 'critical',
            'requires_restart': status == 'critical'
        }

    def full_health_check(self):
        """Complete health check of Termux Defender"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'ssh_connection': False,
            'defender_running': False,
            'issues_detected': [],
            'recommendations': []
        }

        # Test SSH
        report['ssh_connection'] = self.test_connection()
        if not report['ssh_connection']:
            report['recommendations'].append('Fix SSH connection to Termux')
            return report

        # Check Defender status
        status = self.check_defender_status()
        report['defender_running'] = status.get('running', False)
        if not report['defender_running']:
            report['recommendations'].append('Start Termux Defender daemon')
            return report

        # Capture recent output
        tmux_result = self.capture_tmux_output()
        if tmux_result['success']:
            issues = self.detect_issues(tmux_result['output'])
            report['issues_detected'] = issues

            if issues:
                report['recommendations'].append('Check Termux Defender logs for errors')

        # Get recent logs
        logs_result = self.get_defender_logs(lines=20)
        if logs_result['success']:
            log_issues = self.detect_issues(logs_result['logs'])
            report['issues_detected'].extend(log_issues)

        if not report['issues_detected']:
            report['recommendations'].append('Termux Defender healthy')

        return report
