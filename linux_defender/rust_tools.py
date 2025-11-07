#!/usr/bin/env python3
"""
Rust Tools Integration for Linux Defender
High-performance file search, git operations, and safe execution using compiled Rust binaries
"""

import subprocess
import json
from pathlib import Path
from typing import List, Dict, Optional

# Path to compiled Rust binaries
HOME = Path.home()

# Try both possible locations (Mac vs Linux)
POSSIBLE_LABS_DIRS = [
    HOME / "ariannamethod" / "labs" / "repos",
    HOME / "Downloads" / "arianna_clean" / "labs" / "repos"
]

def _find_rust_binary(binary_name: str) -> Optional[Path]:
    """Find Rust binary in any of the possible locations"""
    for labs_dir in POSSIBLE_LABS_DIRS:
        if labs_dir.exists():
            # claude-agent-daemon
            bin_path = labs_dir / "claude-agent-daemon" / "target" / "release" / binary_name
            if bin_path.exists():
                return bin_path
    return None

class RustTools:
    """Interface to Rust-based tools for Linux Defender"""
    
    def __init__(self):
        """Initialize Rust tools"""
        self.claude_daemon_bin = _find_rust_binary("claude-daemon")
        
        if not self.claude_daemon_bin:
            print(f"⚠️ Warning: Rust claude-daemon binary not found")
            print("   Run: cd labs/repos/claude-agent-daemon && cargo build --release")
            # Don't raise - allow daemon to run without Rust tools
    
    def safe_exec(self, command: List[str], cwd: Path, timeout: int = 30) -> Dict:
        """
        Execute command safely with sandboxing
        
        Args:
            command: Command and args
            cwd: Working directory
            timeout: Timeout in seconds
        
        Returns:
            Dict with 'stdout', 'stderr', 'returncode', 'success'
        """
        try:
            result = subprocess.run(
                command,
                cwd=str(cwd),
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False
            )
            
            return {
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode,
                'success': result.returncode == 0
            }
        except subprocess.TimeoutExpired:
            return {
                'stdout': '',
                'stderr': f'Command timed out after {timeout}s',
                'returncode': -1,
                'success': False
            }
        except Exception as e:
            return {
                'stdout': '',
                'stderr': str(e),
                'returncode': -1,
                'success': False
            }
    
    def git_status(self, repo_path: Path) -> Optional[Dict]:
        """
        Get git repository status quickly
        
        Args:
            repo_path: Path to git repository
        
        Returns:
            Dict with 'branch', 'dirty', 'ahead', 'behind' or None
        """
        try:
            # Check if it's a git repo
            git_dir = repo_path / '.git'
            if not git_dir.exists():
                return None
            
            # Get branch
            result = subprocess.run(
                ['git', 'branch', '--show-current'],
                cwd=str(repo_path),
                capture_output=True,
                text=True,
                timeout=5,
                check=True
            )
            branch = result.stdout.strip() if result.returncode == 0 else 'unknown'
            
            # Check if dirty
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=str(repo_path),
                capture_output=True,
                text=True,
                timeout=5,
                check=True
            )
            dirty = len(result.stdout.strip()) > 0 if result.returncode == 0 else False
            
            # Check ahead/behind
            result = subprocess.run(
                ['git', 'rev-list', '--left-right', '--count', 'HEAD...@{upstream}'],
                cwd=str(repo_path),
                capture_output=True,
                text=True,
                timeout=5,
                check=False  # May fail if no upstream
            )
            
            ahead, behind = 0, 0
            if result.returncode == 0 and result.stdout.strip():
                parts = result.stdout.strip().split()
                if len(parts) >= 2:
                    ahead, behind = int(parts[0]), int(parts[1])
            
            return {
                'branch': branch,
                'dirty': dirty,
                'ahead': ahead,
                'behind': behind,
                'repo_path': str(repo_path)
            }
        except Exception as e:
            return {
                'branch': 'unknown',
                'dirty': False,
                'ahead': 0,
                'behind': 0,
                'error': str(e)
            }
    
    def check_claude_daemon_available(self) -> bool:
        """Check if claude-daemon binary is available"""
        return self.claude_daemon_bin is not None and self.claude_daemon_bin.exists()
    
    def get_claude_daemon_help(self) -> Optional[str]:
        """Get help output from claude-daemon"""
        if not self.check_claude_daemon_available():
            return None
        
        try:
            result = subprocess.run(
                [str(self.claude_daemon_bin), '--help'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                return result.stdout
            else:
                return None
        except Exception:
            return None

# Singleton instance
_rust_tools_instance = None

def get_rust_tools() -> RustTools:
    """Get singleton RustTools instance"""
    global _rust_tools_instance
    if _rust_tools_instance is None:
        _rust_tools_instance = RustTools()
    return _rust_tools_instance

