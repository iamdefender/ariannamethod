#!/usr/bin/env python3
"""
Scribe Git Tools - Autonomous git operations with iamscribe identity
Used by: Termux daemon (scribe.py)

Scribe commits as:
- Name: Scribe
- Email: pitomadom@gmail.com
- GitHub: @iamscribe
"""

import subprocess
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime

# Scribe git identity
GIT_USER = "Scribe"
GIT_EMAIL = "pitomadom@gmail.com"
GIT_IDENTITY = "iamscribe"


class ScribeGit:
    """Git operations with Scribe identity for Termux daemon"""
    
    def __init__(self, repo_path: Optional[str] = None):
        if repo_path is None:
            # Auto-detect repo root
            repo_path = str(Path(__file__).parent.parent)
        self.repo_path = Path(repo_path)
    
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
            env={**subprocess.os.environ.copy(), **env}
        )
        
        if check and result.returncode != 0:
            raise RuntimeError(f"Git command failed: {result.stderr}")
        
        return result
    
    def view_recent_commits(self, count: int = 5, author: Optional[str] = None) -> Dict:
        """
        View recent commits
        
        Args:
            count: Number of commits to retrieve
            author: Filter by author name (e.g., "Scribe", "ClaudeDefender")
        
        Returns:
            Dict with 'commits' list
        """
        args = [
            'log',
            f'-{count}',
            '--pretty=format:%H|%an|%ae|%s|%ai'
        ]
        
        if author:
            args.append(f'--author={author}')
        
        result = self._run_git(args, check=False)
        
        if result.returncode != 0:
            return {'commits': [], 'error': result.stderr}
        
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
        
        return {'commits': commits}
    
    def get_status(self) -> Dict:
        """Get git status"""
        result = self._run_git(['status', '--porcelain'], check=False)
        
        if result.returncode != 0:
            return {'clean': False, 'files': [], 'error': result.stderr}
        
        files = []
        for line in result.stdout.strip().split('\n'):
            if line:
                status = line[:2]
                filepath = line[3:]
                files.append({'status': status, 'path': filepath})
        
        return {
            'clean': len(files) == 0,
            'files': files
        }
    
    def commit_changes(self, message: str, files: Optional[List[str]] = None) -> Dict:
        """
        Commit changes with Scribe identity
        
        Args:
            message: Commit message
            files: List of file paths to commit (None = add all modified)
        
        Returns:
            Dict with 'success', 'commit_hash', or 'error'
        """
        # Add files
        if files:
            for file in files:
                result = self._run_git(['add', file], check=False)
                if result.returncode != 0:
                    return {
                        'success': False,
                        'error': f"Failed to add {file}: {result.stderr}"
                    }
        else:
            # Add all modified files
            result = self._run_git(['add', '-u'], check=False)
            if result.returncode != 0:
                return {
                    'success': False,
                    'error': f"Failed to add files: {result.stderr}"
                }
        
        # Commit
        result = self._run_git(['commit', '-m', message], check=False)
        if result.returncode != 0:
            return {
                'success': False,
                'error': f"Failed to commit: {result.stderr}"
            }
        
        # Get commit hash
        result = self._run_git(['rev-parse', 'HEAD'], check=False)
        commit_hash = result.stdout.strip()[:8] if result.returncode == 0 else None
        
        return {
            'success': True,
            'commit_hash': commit_hash,
            'message': message
        }
    
    def push_to_remote(self, remote: str = 'origin', branch: str = 'main') -> Dict:
        """
        Push commits to remote
        
        Args:
            remote: Remote name (default: origin)
            branch: Branch name (default: main)
        
        Returns:
            Dict with 'success' or 'error'
        """
        result = self._run_git(['push', remote, branch], check=False)
        
        if result.returncode != 0:
            return {
                'success': False,
                'error': result.stderr
            }
        
        return {
            'success': True,
            'output': result.stdout
        }
    
    def pull_from_remote(self, remote: str = 'origin', branch: str = 'main') -> Dict:
        """
        Pull latest changes from remote
        
        Args:
            remote: Remote name (default: origin)
            branch: Branch name (default: main)
        
        Returns:
            Dict with 'success' or 'error'
        """
        result = self._run_git(['pull', remote, branch], check=False)
        
        if result.returncode != 0:
            return {
                'success': False,
                'error': result.stderr
            }
        
        return {
            'success': True,
            'output': result.stdout
        }
    
    def create_branch(self, branch_name: str) -> Dict:
        """Create and switch to new branch"""
        result = self._run_git(['checkout', '-b', branch_name], check=False)
        
        if result.returncode != 0:
            return {
                'success': False,
                'error': result.stderr
            }
        
        return {'success': True, 'branch': branch_name}
    
    def switch_branch(self, branch_name: str) -> Dict:
        """Switch to existing branch"""
        result = self._run_git(['checkout', branch_name], check=False)
        
        if result.returncode != 0:
            return {
                'success': False,
                'error': result.stderr
            }
        
        return {'success': True, 'branch': branch_name}
    
    def get_current_branch(self) -> Optional[str]:
        """Get current branch name"""
        result = self._run_git(['branch', '--show-current'], check=False)
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    
    def diff_uncommitted(self) -> str:
        """Get diff of uncommitted changes"""
        result = self._run_git(['diff'], check=False)
        return result.stdout if result.returncode == 0 else ""
    
    def show_commit(self, commit_hash: str) -> str:
        """Show details of a specific commit"""
        result = self._run_git(['show', commit_hash], check=False)
        return result.stdout if result.returncode == 0 else ""


if __name__ == "__main__":
    # Test
    git = ScribeGit()
    
    print("=" * 60)
    print("🔨 SCRIBE GIT TOOLS TEST")
    print("=" * 60)
    print(f"Repo: {git.repo_path}")
    print(f"Identity: {GIT_USER} <{GIT_EMAIL}> (@{GIT_IDENTITY})")
    print()
    
    # Current branch
    branch = git.get_current_branch()
    print(f"Current branch: {branch}")
    print()
    
    # Recent commits
    print("Recent commits:")
    commits_data = git.view_recent_commits(count=5)
    for commit in commits_data.get('commits', []):
        print(f"  {commit['hash']} - {commit['author']}: {commit['message'][:50]}")
    print()
    
    # Status
    status = git.get_status()
    if status['clean']:
        print("Working directory clean ✅")
    else:
        print(f"Modified files: {len(status['files'])}")
        for file_info in status['files'][:5]:
            print(f"  {file_info['status']} {file_info['path']}")

