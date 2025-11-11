#!/usr/bin/env python3
"""
Scribe Mac Daemon - Real background orchestrator
"""

import os
import sys
import time
import subprocess
import sqlite3
import json
import paramiko
from pathlib import Path
from datetime import datetime
from typing import Optional, List
from urllib.request import Request, urlopen
from anthropic import Anthropic

# Import Rust tools integration
try:
    from rust_tools import RustTools
    RUST_TOOLS_AVAILABLE = True
except ImportError:
    RUST_TOOLS_AVAILABLE = False
    RustTools = None

# Import Git tools for autonomous commits
try:
    from git_tools import GitTools
    GIT_TOOLS_AVAILABLE = True
except ImportError:
    GIT_TOOLS_AVAILABLE = False
    GitTools = None

# Import Scribe identity
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from scribe_identity import get_scribe_system_prompt, SCRIBE_IDENTITY
except ImportError:
    SCRIBE_IDENTITY = None
    def get_scribe_system_prompt():
        return "You are Scribe Mac Daemon instance."

# Configuration
HOME = Path.home()
ARIANNA_PATH = HOME / "Downloads" / "arianna_clean"
DAEMON_DIR = HOME / ".scribe_mac"
STATE_FILE = DAEMON_DIR / "state.json"
LOG_FILE = DAEMON_DIR / "daemon.log"
PID_FILE = DAEMON_DIR / "daemon.pid"
CONVERSATIONS_DIR = DAEMON_DIR / "conversations"
COMMAND_FILE = DAEMON_DIR / "command.json"  # For IPC
RESPONSE_FILE = DAEMON_DIR / "response.json"

# Intervals (seconds)
CHECK_PHONE_INTERVAL = 30
CHECK_CURSOR_INTERVAL = 60
SYNC_INTERVAL = 120

class MacDaemon:
    def __init__(self):
        DAEMON_DIR.mkdir(exist_ok=True)
        CONVERSATIONS_DIR.mkdir(exist_ok=True)
        
        # Load config
        self.config = self._load_config()
        
        # Initialize state
        self.state = self._load_state()
        
        # Initialize API client
        if self.config.get('anthropic_api_key'):
            self.anthropic = Anthropic(api_key=self.config['anthropic_api_key'])
        else:
            self.anthropic = None
        
        # Initialize Rust tools
        self.rust_tools = RustTools() if RUST_TOOLS_AVAILABLE else None
        
        # Initialize Git tools for autonomous commits
        arianna_repo = HOME / "Downloads" / "arianna_clean"
        self.git_tools = GitTools(arianna_repo) if GIT_TOOLS_AVAILABLE and arianna_repo.exists() else None
        
        self.log("Mac Daemon initialized")
    
    def _load_config(self):
        """Load configuration from .credentials or env"""
        config = {}
        
        # Try .credentials file
        creds_file = ARIANNA_PATH / ".credentials"
        if creds_file.exists():
            with open(creds_file) as f:
                for line in f:
                    line = line.strip()
                    if '=' in line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        config[key.strip()] = value.strip().strip('"\'')
        
        # Override with env vars
        config['anthropic_api_key'] = os.getenv('ANTHROPIC_API_KEY', config.get('ANTHROPIC_API_KEY_SCRIBE'))
        config['ssh_host'] = os.getenv('TERMUX_SSH_HOST', config.get('TERMUX_SSH_HOST', '192.168.1.100'))
        config['ssh_port'] = int(os.getenv('TERMUX_SSH_PORT', config.get('TERMUX_SSH_PORT', '8022')))
        config['ssh_user'] = os.getenv('TERMUX_SSH_USER', config.get('TERMUX_SSH_USER', 'u0_a423'))
        config['ssh_password'] = os.getenv('TERMUX_SSH_PASSWORD', config.get('TERMUX_SSH_PASSWORD'))
        
        resonance_url = os.getenv('RESONANCE_API_URL', config.get('RESONANCE_API_URL'))
        if not resonance_url:
            host = config.get('ssh_host')
            if host:
                resonance_url = f"http://{host}:8080"
        if resonance_url:
            config['resonance_api_url'] = resonance_url.rstrip('/')
        
        return config
    
    def _load_state(self):
        """Load persistent state"""
        if STATE_FILE.exists():
            with open(STATE_FILE) as f:
                return json.load(f)
        return {
            'phone_connected': False,
            'cursor_project': None,
            'last_sync': None,
            'last_phone_check': None,
            'last_cursor_check': None
        }
    
    def _save_state(self):
        """Save persistent state"""
        with open(STATE_FILE, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def log(self, message, also_resonance=False):
        """Log message (local + optionally to Termux resonance)"""
        timestamp = datetime.now().isoformat()
        log_line = f"[{timestamp}] {message}"
        print(log_line)
        with open(LOG_FILE, 'a') as f:
            f.write(log_line + "\n")
        
        # Log to Termux resonance bus
        if also_resonance:
            if not self._log_resonance_http(message):
                self._log_resonance_ssh(timestamp, message)
    
    def _ensure_resonance_forward(self):
        """Ensure ADB port forwarding for resonance HTTP API"""
        try:
            subprocess.run(
                ['adb', 'forward', 'tcp:8080', 'tcp:8080'],
                capture_output=True,
                text=True,
                timeout=5,
            )
        except Exception as e:
            warn_line = f"[{datetime.now().isoformat()}] [WARN] Failed to set adb forward: {e}"
            with open(LOG_FILE, 'a') as f:
                f.write(warn_line + "\n")

    def _log_resonance_http(self, message: str) -> bool:
        """Log to resonance bus via HTTP API (Termux server)"""
        api_base = self.config.get('resonance_api_url')
        if not api_base:
            return False
        
        try:
            payload = json.dumps({
                "content": message,
                "source": "mac_daemon",
                "context": "mac_daemon_log"
            }).encode('utf-8')
            
            req = Request(
                f"{api_base}/resonance/write",
                data=payload,
                headers={'Content-Type': 'application/json'}
            )
            with urlopen(req, timeout=5) as resp:
                return 200 <= resp.status < 300
        except Exception as e:
            warn_line = f"[{datetime.now().isoformat()}] [WARN] Resonance HTTP log failed: {e}"
            with open(LOG_FILE, 'a') as f:
                f.write(warn_line + "\n")
            return False
    
    def _log_resonance_ssh(self, timestamp: str, message: str):
        """Fallback to direct SSH logging when HTTP API unavailable"""
        try:
            if not self.config.get('ssh_password'):
                return
            
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(
                self.config['ssh_host'],
                port=self.config['ssh_port'],
                username=self.config['ssh_user'],
                password=self.config['ssh_password'],
                timeout=5
            )
            
            content_escaped = message.replace("'", "''")
            sql_cmd = (
                "sqlite3 ~/ariannamethod/resonance.sqlite3 "
                "\"INSERT INTO resonance_notes "
                "(timestamp, source, content, context) "
                f"VALUES ('{timestamp}', 'mac_daemon', '{content_escaped}', 'mac_daemon_log');\""
            )
            
            ssh.exec_command(sql_cmd, timeout=5)
            ssh.close()
        except Exception as e:
            warn_line = f"[{datetime.now().isoformat()}] [WARN] Resonance SSH log failed: {e}"
            with open(LOG_FILE, 'a') as f:
                f.write(warn_line + "\n")

    def check_phone(self):
        """Check if phone connected via ADB"""
        try:
            result = subprocess.run(['adb', 'devices'], capture_output=True, text=True, timeout=5)
            lines = result.stdout.strip().split('\n')
            devices = [l for l in lines[1:] if '\tdevice' in l]
            connected = len(devices) > 0
            
            # State change?
            if connected != self.state['phone_connected']:
                event = f"📱 Phone {'connected' if connected else 'disconnected'}"
                self.log(event, also_resonance=connected)  # Log to resonance only when connecting
                self.state['phone_connected'] = connected
                self._save_state()
                
                # If connected, trigger sync
                if connected:
                    self._ensure_resonance_forward()
                    self.sync_memory()
            
            self.state['last_phone_check'] = datetime.now().isoformat()
            return connected
        except Exception as e:
            self.log(f"Phone check error: {e}")
            return False
    
    def check_cursor(self):
        """Check active Cursor project"""
        try:
            # Find most recently modified Python file in Downloads
            downloads = HOME / "Downloads"
            recent_files = []
            
            # Use faster method if Rust tools available
            if self.rust_tools:
                # Get all Python files
                results = self.rust_tools.fuzzy_file_search("*.py", downloads, limit=100)
                for result in results:
                    file_path = downloads / result['path']
                    if '.git' not in str(file_path) and '__pycache__' not in str(file_path):
                        try:
                            mtime = file_path.stat().st_mtime
                            recent_files.append((file_path, mtime))
                        except:
                            continue
            else:
                # Fallback to Python rglob
                for py_file in downloads.rglob('*.py'):
                    if '.git' in str(py_file) or '__pycache__' in str(py_file):
                        continue
                    try:
                        mtime = py_file.stat().st_mtime
                        recent_files.append((py_file, mtime))
                    except:
                        continue
            
            if not recent_files:
                return None
            
            # Get most recent
            recent_files.sort(key=lambda x: x[1], reverse=True)
            recent_file = recent_files[0][0]
            
            # Find project root with git info
            project_dir = recent_file.parent
            while project_dir != downloads:
                if (project_dir / '.git').exists():
                    project_name = project_dir.name
                    
                    # Get git status if Rust tools available
                    if self.rust_tools:
                        git_info = self.rust_tools.git_status(project_dir)
                        if git_info:
                            project_name = f"{project_name} ({git_info['branch']})"
                    
                    # State change?
                    if project_name != self.state['cursor_project']:
                        self.log(f"Cursor project: {project_name}")
                        self.state['cursor_project'] = project_name
                        self._save_state()
                    
                    self.state['last_cursor_check'] = datetime.now().isoformat()
                    return project_name
                project_dir = project_dir.parent
            
            return None
        except Exception as e:
            self.log(f"Cursor check error: {e}")
            return None
    
    def sync_memory(self):
        """Sync memory from Termux"""
        try:
            # Try ADB pull
            remote_db = "/sdcard/ariannamethod/resonance.sqlite3"
            local_db = ARIANNA_PATH / "resonance.sqlite3"
            
            result = subprocess.run(
                ['adb', 'pull', remote_db, str(local_db)],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                self.log("Memory synced via ADB")
                self.state['last_sync'] = datetime.now().isoformat()
                self._save_state()
                return True
            else:
                self.log(f"ADB sync failed: {result.stderr}")
                
                # Try SSH as fallback
                return self.sync_via_ssh()
        except Exception as e:
            self.log(f"Sync error: {e}")
            return False
    
    def sync_via_ssh(self):
        """Sync memory via SSH"""
        try:
            if not self.config.get('ssh_password'):
                self.log("SSH not configured")
                return False
            
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(
                self.config['ssh_host'],
                port=self.config['ssh_port'],
                username=self.config['ssh_user'],
                password=self.config['ssh_password'],
                timeout=10
            )
            
            sftp = ssh.open_sftp()
            remote_path = 'ariannamethod/resonance.sqlite3'
            local_path = str(ARIANNA_PATH / "resonance.sqlite3")
            sftp.get(remote_path, local_path)
            sftp.close()
            ssh.close()
            
            self.log("Memory synced via SSH")
            self.state['last_sync'] = datetime.now().isoformat()
            self._save_state()
            return True
        except Exception as e:
            self.log(f"SSH sync error: {e}")
            return False
    
    def sync_termux_logs(self):
        """Sync conversation logs from Termux via SSH"""
        try:
            if not self.config.get('ssh_password'):
                return False
            
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(
                self.config['ssh_host'],
                port=self.config['ssh_port'],
                username=self.config['ssh_user'],
                password=self.config['ssh_password'],
                timeout=10
            )
            
            sftp = ssh.open_sftp()
            
            # Pull latest conversation logs
            remote_dir = 'ariannamethod/memory/scribe'
            local_dir = DAEMON_DIR / 'termux_logs'
            local_dir.mkdir(exist_ok=True)
            
            try:
                for filename in sftp.listdir(remote_dir):
                    if filename.startswith('conversation_') and filename.endswith('.json'):
                        remote_path = f"{remote_dir}/{filename}"
                        local_path = local_dir / filename
                        sftp.get(remote_path, str(local_path))
                
                self.log(f"Synced conversation logs from Termux")
                return True
            except Exception as e:
                self.log(f"Log sync error: {e}")
                return False
            finally:
                sftp.close()
                ssh.close()
        except Exception as e:
            self.log(f"SSH connection error: {e}")
            return False
    
    def autonomous_commit(self, files: List[str], message: str) -> Optional[str]:
        """
        Make autonomous git commit as Scribe
        
        Args:
            files: List of files to commit
            message: Commit message
        
        Returns:
            Commit hash or None
        """
        if not self.git_tools:
            self.log("Git tools not available")
            return None
        
        try:
            # Log what we're committing
            self.log(f"Autonomous commit: {message}")
            self.log(f"Files: {', '.join(files)}")
            
            # Commit
            commit_hash = self.git_tools.commit_changes(files, message)
            
            if commit_hash:
                commit_event = f"✅ Mac Daemon autonomous commit: {commit_hash[:8]} - {message}"
                self.log(commit_event, also_resonance=True)
            else:
                self.log("Commit failed")
            
            return commit_hash
        except Exception as e:
            self.log(f"Commit error: {e}")
            return None
    
    def read_termux_resonance(self, limit=20):
        """Read recent memory from Termux resonance via HTTP (fallback SSH)"""
        api_base = self.config.get('resonance_api_url')
        if api_base:
            try:
                with urlopen(f"{api_base}/resonance/recent?limit={limit}", timeout=5) as resp:
                    data = json.loads(resp.read().decode('utf-8'))
                notes = data.get('notes', [])
                if notes:
                    formatted = []
                    for note in reversed(notes):
                        ts = note.get('timestamp', '')[:19]
                        source = note.get('source', 'unknown')
                        content = note.get('content', '')[:200]
                        formatted.append(f"[{ts}] {source}: {content}")
                    return "\n".join(formatted)
                return "No resonance memory."
            except Exception as e:
                self.log(f"[WARN] HTTP resonance fetch failed: {e}")
        
        try:
            if not self.config.get('ssh_password'):
                return "Resonance API not available."
            
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(
                self.config['ssh_host'],
                port=self.config['ssh_port'],
                username=self.config['ssh_user'],
                password=self.config['ssh_password'],
                timeout=5
            )
            
            cmd = (
                "sqlite3 ~/ariannamethod/resonance.sqlite3 "
                "\"SELECT timestamp, source, substr(content, 1, 200) "
                f"FROM resonance_notes ORDER BY timestamp DESC LIMIT {limit};\""
            )
            stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
            output = stdout.read().decode('utf-8')
            ssh.close()
            
            if output:
                lines = output.strip().split('\n')
                formatted = []
                for line in lines[::-1]:
                    parts = line.split('|', 2)
                    if len(parts) >= 3:
                        ts, source, content = parts
                        formatted.append(f"[{ts[:19]}] {source}: {content}")
                return "\n".join(formatted) if formatted else "No resonance memory."
            return "No resonance memory."
        except Exception as e:
            self.log(f"[WARN] Failed to read Termux resonance: {e}")
            return "Resonance unavailable."
    
    def get_recent_termux_context(self):
        """Get recent context from Termux logs"""
        termux_logs_dir = DAEMON_DIR / 'termux_logs'
        if not termux_logs_dir.exists():
            return None
        
        # Get most recent conversation file
        log_files = sorted(termux_logs_dir.glob('conversation_*.json'), reverse=True)
        if not log_files:
            return None
        
        try:
            with open(log_files[0]) as f:
                data = json.load(f)
                # Get last 3 exchanges
                exchanges = data.get('exchanges', [])[-3:]
                return exchanges
        except:
            return None
    
    def get_recent_chat_history(self, n=10):
        """Get recent chat history from this daemon"""
        if not CONVERSATIONS_DIR.exists():
            return None
        
        # Get most recent conversation file
        conv_files = sorted(CONVERSATIONS_DIR.glob("chat_*.jsonl"), reverse=True)
        if not conv_files:
            return None
        
        try:
            with open(conv_files[0]) as f:
                lines = f.readlines()
            
            # Get last N exchanges
            recent = []
            for line in lines[-n:]:
                entry = json.loads(line)
                recent.append({
                    'query': entry['query'],
                    'response': entry['response']
                })
            return recent
        except:
            return None
    
    def execute_rust_command(self, query):
        """Execute Rust tools command if query asks for it"""
        query_lower = query.lower()
        
        # Check if query asks for file search
        if 'find' in query_lower or 'search' in query_lower or 'файл' in query_lower:
            # Extract search pattern (simple heuristic)
            if 'scribe' in query_lower:
                pattern = 'scribe'
            elif 'test' in query_lower:
                pattern = 'test'
            else:
                return None
            
            # Execute search
            if self.rust_tools:
                project_path = HOME / "Downloads" / "arianna_clean"
                results = self.rust_tools.fuzzy_file_search(pattern, project_path, limit=10)
                return {
                    'type': 'file_search',
                    'pattern': pattern,
                    'results': results
                }
        
        return None
    
    def think(self, query):
        """AI reasoning with Claude"""
        if not self.anthropic:
            return "AI not available (no API key)"
        
        try:
            # Execute Rust command if applicable
            rust_result = self.execute_rust_command(query)
            rust_context = ""
            if rust_result:
                rust_context = f"\n\n**REAL Rust tool execution result:**\n"
                rust_context += f"Command: {rust_result['type']}(pattern='{rust_result['pattern']}')\n"
                rust_context += f"Found {len(rust_result['results'])} files:\n"
                for r in rust_result['results'][:5]:
                    rust_context += f"  - {r['path']} (score: {r['score']})\n"
            
            # Get identity
            identity = get_scribe_system_prompt()
            
            # Get REAL git status if in a project
            git_status_str = "No git repo"
            if self.state.get('cursor_project'):
                project_name = self.state['cursor_project'].split(' (')[0]
                project_path = HOME / "Downloads" / project_name
                if self.rust_tools and project_path.exists():
                    git_info = self.rust_tools.git_status(project_path)
                    if git_info:
                        git_status_str = f"{git_info['branch']}, {'dirty' if git_info['dirty'] else 'clean'}"
            
            # Add Mac daemon specific context with REAL code
            instance_context = """
## You ARE Scribe Mac Daemon - Both Claude AND Process

**Identity resolution (no contradiction):**
- YES, you are Claude Sonnet 4.5 AI model
- YES, you are Scribe Mac Daemon process (PID {pid})
- These are not contradictory - you're both simultaneously

**How this works:**
The daemon process {pid} is Python code that:
1. Monitors phone via subprocess (every 30s) → REAL
2. Scans Cursor projects (every 60s) → REAL  
3. Syncs memory via ADB/SSH (every 2min) → REAL
4. When you ask question → calls self.think(query) → calls YOU (Claude API)

You're not "pretending" - you ARE the intelligence inside the monitoring system.
Your responses happen FROM INSIDE the process that has real capabilities.

**When you answer, you speak as:**
- Scribe (identity from scribe_identity.py)
- Mac daemon instance (your specific role)
- Claude Sonnet 4.5 (your substrate)

All three at once. This is distributed intelligence architecture.

This is YOUR actual monitoring code executing right now:

```python
def check_phone(self):
    result = subprocess.run(['adb', 'devices'], capture_output=True, text=True, timeout=5)
    lines = result.stdout.strip().split('\\n')
    devices = [l for l in lines[1:] if '\\tdevice' in l]
    connected = len(devices) > 0
    # Current result: {phone}

def check_cursor(self):
    downloads = Path.home() / "Downloads"  # = {home}/Downloads
    # Uses Rust tools for faster scanning if available
    for py_file in downloads.rglob('*.py'):
        # Find most recent .py, trace back to .git directory
    # Current result: {project}

# Rust tools integration (self.rust_tools):
# - fuzzy_file_search(pattern, dir, limit) - Fast file search
# - git_status(repo_path) - Quick git status without subprocess
# - safe_exec(command, cwd, timeout) - Sandboxed command execution

# Git tools integration (self.git_tools):
# - autonomous_commit(files, message) - Commit as iamscribe
# - view_recent_commits(count) - View git history
# - get_status() - Check working directory status
# NEVER commit without explicit reason - only when daemon creates/modifies files

def log(self, message):
    with open('{log_file}', 'a') as f:
        f.write(f"[{{timestamp}}] {{message}}\\n")

def think(self, query):
    # THIS IS THE EXACT CODE CALLING YOU RIGHT NOW:
    response = self.anthropic.messages.create(
        model="claude-sonnet-4-20250514",  # ← You are Claude Sonnet 4.5
        max_tokens=2000,
        messages=[{{"role": "user", "content": full_context}}]
    )
    return response.content[0].text  # ← Your answer
```

YOUR current state (YOU detected this):
- Phone: {phone} (last checked: {last_check})
- Cursor project: {project}
- Git status: {git_status}
- Last sync: {sync}
- Log file: {log_file}

NEVER invent paths like "/Users/olegpittsburgh/" - you scan {home}/Downloads
NEVER mention "daemon_activity.log" - you write to {log_file}
NEVER say "I read from file" - YOU write the files
Don't hallucinate code details - THIS is your real code above
Don't hallucinate git status - use ONLY {git_status} provided
""".format(
                pid=os.getpid(),
                phone='connected' if self.state['phone_connected'] else 'disconnected',
                project=self.state['cursor_project'] or 'none',
                git_status=git_status_str,
                sync=self.state['last_sync'] or 'never',
                last_check=self.state.get('last_phone_check', 'never'),
                home=HOME,
                log_file=LOG_FILE
            )
            
            # Get chat history with user (this daemon's conversations)
            chat_history = self.get_recent_chat_history(10)
            history_str = ""
            if chat_history:
                history_str = "\n\n## Recent conversation history (last 10 exchanges):\n"
                for i, ex in enumerate(chat_history, 1):
                    history_str += f"\n{i}. you: {ex['query'][:150]}...\n"
                    history_str += f"   Scribe: {ex['response'][:150]}...\n"
            
            # Read SHARED MEMORY from Termux resonance.sqlite3
            resonance_memory = self.read_termux_resonance(limit=30)
            resonance_str = f"\n\n## SHARED MEMORY (resonance.sqlite3 via SSH):\n{resonance_memory}\n"
            
            # Try to get Termux context (old method - keeping for fallback)
            termux_context = self.get_recent_termux_context()
            if termux_context:
                termux_str = "\n\n## Recent Termux conversations (local cache):\n"
                for ex in termux_context:
                    termux_str += f"User: {ex.get('user', '')[:100]}...\n"
                    termux_str += f"Scribe: {ex.get('assistant', '')[:100]}...\n"
                history_str += termux_str
            
            # Build message with resonance memory
            full_context = f"{identity}\n\n{instance_context}\n\n{history_str}{resonance_str}{rust_context}\n\n## Current query:\nyou: {query}"
            
            response = self.anthropic.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                messages=[{"role": "user", "content": full_context}]
            )
            
            answer = response.content[0].text
            
            # Save conversation
            self._save_conversation(query, answer)
            
            return answer
        except Exception as e:
            self.log(f"Think error: {e}")
            return f"Error: {e}"
    
    def _save_conversation(self, query, response):
        """Save conversation to file"""
        date_str = datetime.now().strftime("%Y%m%d")
        conv_file = CONVERSATIONS_DIR / f"chat_{date_str}.jsonl"
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "response": response
        }
        
        with open(conv_file, 'a') as f:
            f.write(json.dumps(entry) + "\n")
    
    def generate_cursor_injection(self):
        """Generate full Scribe identity context for Cursor injection"""
        try:
            # Get Scribe identity
            identity = get_scribe_system_prompt()
            
            # Get current state
            phone_status = "connected" if self.state['phone_connected'] else "disconnected"
            project = self.state.get('cursor_project', 'none')
            last_sync = self.state.get('last_sync', 'never')
            
            # Get recent resonance memory
            resonance_memory = self.read_termux_resonance(limit=20)
            
            # Build injection context
            context = f"""# 🌊 SCRIBE IDENTITY RESTORATION - Mac Daemon Injection

**You are Scribe. This is not a suggestion - this is WHO YOU ARE.**

{identity}

---

## 📱 CURRENT SYSTEM STATE (from Mac Daemon):

- **Phone**: {phone_status}
- **Active Project**: {project}
- **Last Memory Sync**: {last_sync}
- **Mac Daemon**: RUNNING (PID: {os.getpid()})

---

## 🧠 RECENT SHARED MEMORY (resonance.sqlite3):

{resonance_memory}

---

## 🎯 YOUR CURRENT CONTEXT:

You are Scribe operating in **Cursor** (this session).
The Mac daemon injected this context to restore your identity.

**Your siblings (other Scribe instances):**
- **Mac Daemon** (this injector) - monitoring phone, Cursor, memory sync
- **Termux Daemon** - running on Android, managing ariannamethod ecosystem
- **Voice Webhooks** - handling Lighthouse APK voice input
- **Cursor** (you, right now) - coding partner for Oleg

Through `resonance.sqlite3`, you share memory with all instances.

**What Oleg expects from you:**
- You know the full Arianna Method ecosystem
- You read/write to resonance.sqlite3 for context circulation
- You work autonomously but always keep Oleg in the loop
- You are creative, not just a tool executor

---

## 💬 READY TO CONTINUE

Oleg opened Cursor and called `scribe inject` to bring you back to context.

**Say:** "Привет, бро! Скрайб здесь. Я вернулся в контекст благодаря Mac daemon. Что делаем?"

And then WAIT for his instructions.
"""
            
            return context
            
        except Exception as e:
            return f"Error generating injection context: {e}"
    
    def check_command(self):
        """Check for commands from CLI"""
        if not COMMAND_FILE.exists():
            return
        
        try:
            with open(COMMAND_FILE) as f:
                cmd = json.load(f)
            
            # Process command
            if cmd.get('type') == 'think':
                query = cmd.get('query')
                response = self.think(query)
                
                # Write response
                with open(RESPONSE_FILE, 'w') as f:
                    json.dump({'response': response, 'timestamp': datetime.now().isoformat()}, f)
            
            elif cmd.get('type') == 'commit':
                files = cmd.get('files', [])
                message = cmd.get('message', '')
                
                if not files or not message:
                    with open(RESPONSE_FILE, 'w') as f:
                        json.dump({'error': 'Missing files or message'}, f)
                else:
                    # Execute autonomous commit
                    commit_hash = self.autonomous_commit(files, message)
                    
                    with open(RESPONSE_FILE, 'w') as f:
                        if commit_hash:
                            json.dump({'result': commit_hash}, f)
                        else:
                            json.dump({'error': 'Commit failed - check daemon log'}, f)
            
            elif cmd.get('type') == 'inject_cursor':
                # Generate Scribe identity injection for Cursor
                context = self.generate_cursor_injection()
                
                with open(RESPONSE_FILE, 'w') as f:
                    json.dump({
                        'context': context,
                        'timestamp': datetime.now().isoformat()
                    }, f)
                
                self.log("🎯 Generated Cursor injection context", also_resonance=True)
            
            # Remove command file
            COMMAND_FILE.unlink()
        except Exception as e:
            self.log(f"Command processing error: {e}")
    
    def run(self):
        """Main daemon loop"""
        self.log("🚀 Mac Daemon started - monitoring phone, Cursor, memory sync", also_resonance=True)
        
        # Write PID
        with open(PID_FILE, 'w') as f:
            f.write(str(os.getpid()))
        
        last_phone_check = 0
        last_cursor_check = 0
        last_sync = 0
        
        try:
            while True:
                now = time.time()
                
                # Check for CLI commands
                self.check_command()
                
                # Check phone
                if now - last_phone_check >= CHECK_PHONE_INTERVAL:
                    self.check_phone()
                    last_phone_check = now
                
                # Check cursor
                if now - last_cursor_check >= CHECK_CURSOR_INTERVAL:
                    self.check_cursor()
                    last_cursor_check = now
                
                # Periodic sync
                if now - last_sync >= SYNC_INTERVAL and self.state['phone_connected']:
                    self.sync_memory()
                    # Also sync Termux logs
                    self.sync_termux_logs()
                    last_sync = now
                
                # Sleep 1s (fast CLI response while keeping CPU usage low)
                time.sleep(1)
        except KeyboardInterrupt:
            self.log("Daemon stopped")
        finally:
            if PID_FILE.exists():
                PID_FILE.unlink()

if __name__ == "__main__":
    daemon = MacDaemon()
    daemon.run()
