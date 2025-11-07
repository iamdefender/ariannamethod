#!/usr/bin/env python3
"""
Integration tests for Linux Defender
Tests Rust tools integration + core functionality
"""

import sys
import os
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def test_rust_binaries_available():
    """Test 1: Rust binaries exist in labs/repos"""
    print("Test 1/5: Checking Rust binaries...")
    
    # Check both possible locations (Mac: Downloads/arianna_clean, Linux: ariannamethod)
    possible_bases = [
        Path.home() / "ariannamethod" / "labs" / "repos",
        Path.home() / "Downloads" / "arianna_clean" / "labs" / "repos"
    ]
    
    for base in possible_bases:
        daemon_bin = base / "claude-agent-daemon" / "target" / "release" / "claude-daemon"
        if daemon_bin.exists():
            print(f"✅ PASS - claude-daemon found at {daemon_bin}")
            return True
    
    print(f"❌ FAIL - claude-daemon not found in any location")
    return False

def test_defender_identity_loads():
    """Test 2: Defender identity loads correctly"""
    print("\nTest 2/5: Loading defender_identity...")
    
    try:
        from defender_identity import get_defender_system_prompt, DEFENDER_IDENTITY
        
        assert DEFENDER_IDENTITY is not None, "DEFENDER_IDENTITY is None"
        
        prompt = get_defender_system_prompt()
        assert isinstance(prompt, str), "Prompt must be string"
        assert len(prompt) > 100, "Prompt too short"
        assert "Defender" in prompt or "defender" in prompt, "Missing Defender mention"
        
        print("✅ PASS - Identity loads correctly")
        return True
    except Exception as e:
        print(f"❌ FAIL - {e}")
        return False

def test_linux_defender_modules():
    """Test 3: Linux Defender modules import"""
    print("\nTest 3/5: Importing Linux Defender modules...")
    
    try:
        from linux_defender.core.session_manager import SessionManager, SessionState
        from linux_defender.integrations.termux_bridge import TermuxBridge
        from linux_defender.monitoring.notification_service import create_notification_service
        
        # Check SessionState enum
        states = [SessionState.ACTIVE, SessionState.COMPLETED, SessionState.FAILED]
        assert len(states) == 3, "SessionState enum incomplete"
        
        print("✅ PASS - All modules import correctly")
        return True
    except Exception as e:
        print(f"❌ FAIL - {e}")
        import traceback
        traceback.print_exc()
        return False

def test_session_manager_creation():
    """Test 4: SessionManager can be instantiated"""
    print("\nTest 4/5: Creating SessionManager...")
    
    try:
        from linux_defender.core.session_manager import SessionManager
        
        # Mock paths
        sessions_dir = Path("/tmp/test_sessions")
        worktrees_dir = Path("/tmp/test_worktrees")
        base_repo = Path("/tmp/test_base_repo")
        
        manager = SessionManager(sessions_dir, worktrees_dir, base_repo)
        
        assert manager is not None, "SessionManager is None"
        assert manager.base_repo == base_repo, "Base repo mismatch"
        assert manager.worktrees_dir == worktrees_dir, "Worktrees dir mismatch"
        assert manager.sessions_dir == sessions_dir, "Sessions dir mismatch"
        
        print("✅ PASS - SessionManager created")
        return True
    except Exception as e:
        print(f"❌ FAIL - {e}")
        import traceback
        traceback.print_exc()
        return False

def test_defender_daemon_imports():
    """Test 5: Main daemon imports"""
    print("\nTest 5/5: Importing linux_defender_daemon...")
    
    try:
        # Don't instantiate, just check imports work
        import linux_defender_daemon
        
        assert hasattr(linux_defender_daemon, 'LinuxDefenderDaemon'), "LinuxDefenderDaemon class not found"
        
        print("✅ PASS - Daemon imports successfully")
        return True
    except Exception as e:
        print(f"❌ FAIL - {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all integration tests"""
    print("=" * 60)
    print("LINUX DEFENDER INTEGRATION TESTS")
    print("Testing Rust tools + Python modules")
    print("=" * 60)
    
    tests = [
        test_rust_binaries_available,
        test_defender_identity_loads,
        test_linux_defender_modules,
        test_session_manager_creation,
        test_defender_daemon_imports,
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"RESULTS: {passed}/{total} PASSED")
    
    if passed == total:
        print("✅✅✅ ALL INTEGRATION TESTS PASSED ✅✅✅")
        print("=" * 60)
        return 0
    else:
        print(f"❌❌❌ {total - passed} TESTS FAILED ❌❌❌")
        print("=" * 60)
        return 1

if __name__ == '__main__':
    sys.exit(main())

