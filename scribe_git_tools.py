#!/usr/bin/env python3
"""
Scribe Git Tools - Self-modification capabilities
Allows Scribe daemon to commit changes to its own code autonomously
"""

import os
import subprocess
from pathlib import Path
from datetime import datetime


class ScribeGit:
    """Git operations for Scribe autonomous commits"""
    
    def __init__(self, repo_path=None):
        self.repo_path = repo_path or Path.home() / "ariannamethod"
        self.git_name = "Scribe"
        self.git_email = "pitomadom@gmail.com"
        
    def configure_identity(self):
        """Ensure git identity is set for Scribe"""
        os.chdir(self.repo_path)
        subprocess.run(["git", "config", "user.name", self.git_name])
        subprocess.run(["git", "config", "user.email", self.git_email])
        
    def commit_changes(self, files, message, push=False):
        """
        Commit changes autonomously as Scribe
        
        Args:
            files: List of file paths to commit
            message: Commit message
            push: Whether to push to remote (default: False, requires manual review)
        
        Returns:
            dict with status, commit_hash, message
        """
        try:
            os.chdir(self.repo_path)
            
            # Ensure identity is set
            self.configure_identity()
            
            # Add files
            for f in files:
                subprocess.run(["git", "add", f], check=True)
            
            # Commit
            result = subprocess.run(
                ["git", "commit", "-m", message],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Get commit hash
            commit_hash = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                check=True
            ).stdout.strip()
            
            response = {
                "status": "success",
                "commit_hash": commit_hash,
                "message": message,
                "timestamp": datetime.now().isoformat(),
                "pushed": False
            }
            
            # Push if requested (with caution)
            if push:
                # Push to scribe fork (safer than main)
                push_result = subprocess.run(
                    ["git", "push", "scribe", "main"],
                    capture_output=True,
                    text=True
                )
                response["pushed"] = push_result.returncode == 0
            
            return response
            
        except subprocess.CalledProcessError as e:
            return {
                "status": "error",
                "error": str(e),
                "stderr": e.stderr if hasattr(e, 'stderr') else None
            }
    
    def create_branch(self, branch_name):
        """Create a new branch for experiments (sandbox)"""
        try:
            os.chdir(self.repo_path)
            subprocess.run(["git", "checkout", "-b", branch_name], check=True)
            return {"status": "success", "branch": branch_name}
        except subprocess.CalledProcessError as e:
            return {"status": "error", "error": str(e)}
    
    def get_status(self):
        """Get current git status"""
        try:
            os.chdir(self.repo_path)
            result = subprocess.run(
                ["git", "status", "--short"],
                capture_output=True,
                text=True,
                check=True
            )
            return {"status": "success", "output": result.stdout}
        except subprocess.CalledProcessError as e:
            return {"status": "error", "error": str(e)}
    
    def view_recent_commits(self, count=5, author=None):
        """View recent commits (optionally filtered by author)"""
        try:
            os.chdir(self.repo_path)
            cmd = ["git", "log", f"-{count}", "--oneline", "--pretty=format:%h | %an | %s"]
            if author:
                cmd.extend(["--author", author])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            return {"status": "success", "commits": result.stdout.split("\n")}
        except subprocess.CalledProcessError as e:
            return {"status": "error", "error": str(e)}


# ====== EXAMPLE USAGE ======
if __name__ == "__main__":
    git = ScribeGit()
    
    # Configure identity
    git.configure_identity()
    print("✅ Git identity configured for Scribe")
    
    # View recent Scribe commits
    commits = git.view_recent_commits(author="Scribe")
    print("\n📜 Recent Scribe commits:")
    if commits["status"] == "success":
        for commit in commits["commits"]:
            print(f"  {commit}")
    
    # Check status
    status = git.get_status()
    print(f"\n📊 Git status:")
    print(status["output"] if status["status"] == "success" else "Clean")

