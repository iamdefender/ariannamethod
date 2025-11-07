#!/usr/bin/env python3
"""
Session Manager - Isolated sessions for parallel task execution
Inspired by claude-agent-daemon Rust implementation

Each session gets:
- Dedicated working directory
- Git worktree for isolated operations
- State machine tracking
- Separate log file
"""

import os
import uuid
import json
import subprocess
from pathlib import Path
from datetime import datetime
from enum import Enum

class SessionState(Enum):
    """Session state machine"""
    ACTIVE = "active"
    AWAITING_REVIEW = "awaiting_review"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class DefenderSession:
    """Isolated session for parallel operations"""

    def __init__(self, task_id, task_type, sessions_dir, worktrees_dir, base_repo):
        self.id = task_id
        self.task_type = task_type
        self.state = SessionState.ACTIVE
        self.created_at = datetime.now().isoformat()

        # Directories
        self.working_dir = Path(sessions_dir) / task_id
        self.working_dir.mkdir(parents=True, exist_ok=True)

        self.worktree_path = Path(worktrees_dir) / task_id
        self.base_repo = Path(base_repo)

        # Files
        self.state_file = self.working_dir / "state.json"
        self.log_file = self.working_dir / "session.log"

        # Git branch
        self.branch_name = f"defender-session-{task_id}"

        # Save initial state
        self._save_state()

    def _save_state(self):
        """Persist session state to JSON"""
        state_data = {
            'id': self.id,
            'task_type': self.task_type,
            'state': self.state.value,
            'created_at': self.created_at,
            'updated_at': datetime.now().isoformat(),
            'branch_name': self.branch_name,
            'working_dir': str(self.working_dir),
            'worktree_path': str(self.worktree_path)
        }

        with open(self.state_file, 'w') as f:
            json.dump(state_data, f, indent=2)

    def transition_to(self, new_state: SessionState):
        """Transition to new state"""
        old_state = self.state
        self.state = new_state
        self._save_state()
        self.log(f"State transition: {old_state.value} -> {new_state.value}")
        return old_state, new_state

    def log(self, message):
        """Log message to session log"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_msg = f"[{timestamp}] {message}\n"

        with open(self.log_file, 'a') as f:
            f.write(log_msg)

    def create_worktree(self):
        """Create isolated git worktree for this session"""
        try:
            # Create worktree from main branch
            subprocess.run([
                'git', 'worktree', 'add',
                str(self.worktree_path),
                '-b', self.branch_name,
                'main'
            ], cwd=self.base_repo, check=True, capture_output=True)

            self.log(f"Created worktree: {self.worktree_path}")
            return True
        except subprocess.CalledProcessError as e:
            self.log(f"Failed to create worktree: {e.stderr.decode()}")
            return False

    def cleanup_worktree(self):
        """Remove worktree and delete branch"""
        try:
            # Remove worktree
            subprocess.run([
                'git', 'worktree', 'remove',
                str(self.worktree_path)
            ], cwd=self.base_repo, check=True, capture_output=True)

            # Delete branch
            subprocess.run([
                'git', 'branch', '-D',
                self.branch_name
            ], cwd=self.base_repo, check=True, capture_output=True)

            self.log(f"Cleaned up worktree and branch")
            return True
        except subprocess.CalledProcessError as e:
            self.log(f"Failed to cleanup worktree: {e.stderr.decode()}")
            return False


class SessionManager:
    """Manages multiple isolated sessions"""

    def __init__(self, sessions_dir, worktrees_dir, base_repo):
        self.sessions_dir = Path(sessions_dir)
        self.worktrees_dir = Path(worktrees_dir)
        self.base_repo = Path(base_repo)

        # Ensure directories exist
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self.worktrees_dir.mkdir(parents=True, exist_ok=True)

        # Active sessions
        self.sessions = {}

        # Load existing sessions
        self._load_existing_sessions()

    def _load_existing_sessions(self):
        """Load sessions from disk"""
        if not self.sessions_dir.exists():
            return

        for session_dir in self.sessions_dir.iterdir():
            if session_dir.is_dir():
                state_file = session_dir / "state.json"
                if state_file.exists():
                    try:
                        with open(state_file) as f:
                            state_data = json.load(f)

                        # Reconstruct session object
                        session = DefenderSession(
                            state_data['id'],
                            state_data['task_type'],
                            self.sessions_dir,
                            self.worktrees_dir,
                            self.base_repo
                        )
                        session.state = SessionState(state_data['state'])
                        self.sessions[session.id] = session
                    except Exception as e:
                        print(f"Failed to load session {session_dir.name}: {e}")

    def create_session(self, task_type, with_worktree=False):
        """Create new isolated session"""
        task_id = str(uuid.uuid4())[:8]

        session = DefenderSession(
            task_id,
            task_type,
            self.sessions_dir,
            self.worktrees_dir,
            self.base_repo
        )

        if with_worktree:
            if not session.create_worktree():
                return None

        self.sessions[task_id] = session
        return session

    def get_session(self, task_id):
        """Get session by ID"""
        return self.sessions.get(task_id)

    def list_sessions(self, state_filter=None):
        """List sessions, optionally filtered by state"""
        if state_filter:
            return [s for s in self.sessions.values() if s.state == state_filter]
        return list(self.sessions.values())

    def cleanup_session(self, task_id):
        """Cleanup session and remove from tracking"""
        session = self.sessions.get(task_id)
        if not session:
            return False

        # Cleanup worktree if exists
        if session.worktree_path.exists():
            session.cleanup_worktree()

        # Remove from active sessions
        del self.sessions[task_id]

        return True

    def cleanup_completed_sessions(self):
        """Clean up all completed/failed/cancelled sessions"""
        cleanup_states = [
            SessionState.COMPLETED,
            SessionState.FAILED,
            SessionState.CANCELLED
        ]

        sessions_to_cleanup = [
            s.id for s in self.sessions.values()
            if s.state in cleanup_states
        ]

        for session_id in sessions_to_cleanup:
            self.cleanup_session(session_id)

        return len(sessions_to_cleanup)
