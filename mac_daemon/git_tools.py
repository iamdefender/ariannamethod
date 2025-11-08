#!/usr/bin/env python3
"""
Git tools for Mac Daemon - Scribe identity
Autonomous git operations with iamscribe identity
"""

import subprocess
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime

# Scribe git identity (matching existing commits: ea39d08, 984b89e, etc.)
GIT_USER = "Scribe"
GIT_EMAIL = "pitomadom@gmail.com"

class GitTools:
    """Git operations with Scribe identity"""
    
    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
    
    def _run_git(self, args: List[str], check: bool = True) -> subprocess.CompletedProcess:
        """Run git command with Scribe identity"""
        # Set git identity for this command
        env = {
            'GIT_AUTHOR_NAME': GIT_USER,
            'GIT_AUTHOR_EMAIL': GIT_EMAIL,
            'GIT_COMMITTER_NAME': GIT_USER,
            'GIT_COMMITTER_EMAIL': GIT_EMAIL
        }
        
        result = subprocess.run(
            ['git'] + args,
            cwd=str(self.repo_path),
            capture_output=True,
            text=True,
            check=False,
            env={**subprocess.os.environ, **env}
        )
        
        if check and result.returncode != 0:
            raise RuntimeError(f"Git command failed: {result.stderr}")
        
        return result
    
    def view_recent_commits(self, count: int = 5) -> List[Dict]:
        """View recent commits"""
        result = self._run_git([
            'log',
            f'-{count}',
            '--pretty=format:%H|%an|%ae|%s|%ai'
        ], check=False)
        
        if result.returncode != 0:
            return []
        
        commits = []
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            parts = line.split('|')
            if len(parts) >= 5:
                commits.append({
                    'hash': parts[0][:8],
                    'author': parts[1],
                    'email': parts[2],
                    'message': parts[3],
                    'date': parts[4]
                })
        
        return commits
    
    def get_status(self) -> Dict:
        """Get git status"""
        result = self._run_git(['status', '--porcelain'], check=False)
        
        if result.returncode != 0:
            return {'clean': False, 'files': []}
        
        files = []
        for line in result.stdout.strip().split('\n'):
            if line:
                files.append(line)
        
        return {
            'clean': len(files) == 0,
            'files': files
        }
    
    def commit_changes(self, files: List[str], message: str) -> Optional[str]:
        """
        Commit changes with Scribe identity
        
        Args:
            files: List of file paths to commit
            message: Commit message
        
        Returns:
            Commit hash or None if failed
        """
        # Add files
        for file in files:
            result = self._run_git(['add', file], check=False)
            if result.returncode != 0:
                print(f"Failed to add {file}: {result.stderr}")
                return None
        
        # Commit
        result = self._run_git(['commit', '-m', message], check=False)
        if result.returncode != 0:
            print(f"Failed to commit: {result.stderr}")
            return None
        
        # Get commit hash
        result = self._run_git(['rev-parse', 'HEAD'], check=False)
        if result.returncode == 0:
            return result.stdout.strip()[:8]
        
        return None
    
    def create_branch(self, branch_name: str) -> bool:
        """Create new branch"""
        result = self._run_git(['checkout', '-b', branch_name], check=False)
        return result.returncode == 0
    
    def switch_branch(self, branch_name: str) -> bool:
        """Switch to existing branch"""
        result = self._run_git(['checkout', branch_name], check=False)
        return result.returncode == 0
    
    def get_current_branch(self) -> Optional[str]:
        """Get current branch name"""
        result = self._run_git(['branch', '--show-current'], check=False)
        if result.returncode == 0:
            return result.stdout.strip()
        return None

