#!/usr/bin/env python3
"""
Scribe File Browser - System awareness and file exploration
Allows Scribe to browse Termux filesystem, monitor changes, explore codebase
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Add arianna_core_utils to path
sys.path.insert(0, str(Path.home() / "ariannamethod" / "arianna_core_utils"))

try:
    from repo_monitor import RepoMonitor
    REPO_MONITOR_AVAILABLE = True
except ImportError:
    REPO_MONITOR_AVAILABLE = False
    print("⚠️ RepoMonitor not available")


class ScribeFileBrowser:
    """File system awareness for Scribe daemon"""
    
    def __init__(self, base_path=None):
        self.base_path = base_path or Path.home() / "ariannamethod"
        self.monitors = {}
        
    def list_directory(self, path, recursive=False, max_depth=2):
        """
        List directory contents with metadata
        
        Args:
            path: Directory path (relative to base_path or absolute)
            recursive: Whether to recurse into subdirectories
            max_depth: Maximum recursion depth
        
        Returns:
            dict with files, directories, metadata
        """
        target = Path(path) if Path(path).is_absolute() else self.base_path / path
        
        if not target.exists():
            return {"status": "error", "message": f"Path not found: {target}"}
        
        if not target.is_dir():
            return {"status": "error", "message": f"Not a directory: {target}"}
        
        result = {
            "status": "success",
            "path": str(target),
            "files": [],
            "directories": []
        }
        
        try:
            for item in target.iterdir():
                if item.name.startswith('.') and item.name not in ['.github', '.claude-defender']:
                    continue  # Skip hidden files except specific ones
                
                stat = item.stat()
                metadata = {
                    "name": item.name,
                    "path": str(item),
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                }
                
                if item.is_file():
                    metadata["type"] = "file"
                    metadata["extension"] = item.suffix
                    result["files"].append(metadata)
                elif item.is_dir():
                    metadata["type"] = "directory"
                    result["directories"].append(metadata)
            
            # Sort by name
            result["files"].sort(key=lambda x: x["name"])
            result["directories"].sort(key=lambda x: x["name"])
            
            return result
            
        except PermissionError:
            return {"status": "error", "message": f"Permission denied: {target}"}
    
    def read_file(self, path, lines=None, offset=0):
        """
        Read file contents safely
        
        Args:
            path: File path
            lines: Number of lines to read (None = all)
            offset: Line offset to start from
        
        Returns:
            dict with status, content, metadata
        """
        target = Path(path) if Path(path).is_absolute() else self.base_path / path
        
        if not target.exists():
            return {"status": "error", "message": f"File not found: {target}"}
        
        if not target.is_file():
            return {"status": "error", "message": f"Not a file: {target}"}
        
        try:
            with open(target, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
            
            # Apply offset and limit
            if offset > 0:
                all_lines = all_lines[offset:]
            if lines:
                all_lines = all_lines[:lines]
            
            stat = target.stat()
            
            return {
                "status": "success",
                "path": str(target),
                "content": "".join(all_lines),
                "total_lines": len(all_lines),
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
            }
            
        except UnicodeDecodeError:
            return {"status": "error", "message": f"Binary file or encoding error: {target}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def monitor_directory(self, path, monitor_name=None):
        """
        Set up RepoMonitor for a directory
        
        Args:
            path: Directory to monitor
            monitor_name: Unique name for this monitor
        
        Returns:
            dict with status, monitor info
        """
        if not REPO_MONITOR_AVAILABLE:
            return {"status": "error", "message": "RepoMonitor not available"}
        
        target = Path(path) if Path(path).is_absolute() else self.base_path / path
        monitor_name = monitor_name or f"scribe_monitor_{target.name}"
        
        cache_file = self.base_path / f".{monitor_name}_cache.json"
        
        try:
            monitor = RepoMonitor(repo_path=str(target), cache_file=str(cache_file))
            self.monitors[monitor_name] = monitor
            
            return {
                "status": "success",
                "monitor_name": monitor_name,
                "path": str(target),
                "cache": str(cache_file)
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def check_changes(self, monitor_name):
        """
        Check for changes in monitored directory
        
        Args:
            monitor_name: Name of monitor to check
        
        Returns:
            dict with status, changes
        """
        if monitor_name not in self.monitors:
            return {"status": "error", "message": f"Monitor not found: {monitor_name}"}
        
        try:
            monitor = self.monitors[monitor_name]
            changes = monitor.detect_changes()
            
            return {
                "status": "success",
                "monitor_name": monitor_name,
                "changes": changes,
                "has_changes": any(changes.values())
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def search_files(self, pattern, directory=None, file_type=None):
        """
        Search for files matching pattern
        
        Args:
            pattern: Glob pattern (e.g. "*.py", "scribe*")
            directory: Directory to search in (default: base_path)
            file_type: File extension to filter (e.g. ".py")
        
        Returns:
            dict with status, matching files
        """
        search_path = Path(directory) if directory else self.base_path
        
        try:
            matches = []
            for item in search_path.rglob(pattern):
                if item.is_file():
                    if file_type and not item.name.endswith(file_type):
                        continue
                    
                    stat = item.stat()
                    matches.append({
                        "path": str(item),
                        "name": item.name,
                        "size": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
            
            return {
                "status": "success",
                "pattern": pattern,
                "count": len(matches),
                "matches": matches
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}


# ====== EXAMPLE USAGE ======
if __name__ == "__main__":
    browser = ScribeFileBrowser()
    
    # List current directory
    print("📁 Listing arianna_clean directory:")
    result = browser.list_directory(".")
    if result["status"] == "success":
        print(f"  Files: {len(result['files'])}")
        print(f"  Directories: {len(result['directories'])}")
        print("\n  Python files:")
        for f in result['files']:
            if f['name'].endswith('.py'):
                print(f"    - {f['name']} ({f['size']} bytes)")
    
    # Search for scribe files
    print("\n🔍 Searching for scribe-related files:")
    search = browser.search_files("scribe*")
    if search["status"] == "success":
        print(f"  Found {search['count']} matches:")
        for match in search['matches'][:5]:
            print(f"    - {match['name']}")
    
    # Monitor memory/scribe/
    print("\n👁️ Setting up monitor for memory/scribe/:")
    monitor = browser.monitor_directory("memory/scribe", "scribe_memory_monitor")
    if monitor["status"] == "success":
        print(f"  ✓ Monitor created: {monitor['monitor_name']}")

