#!/usr/bin/env python3
"""
Linux Defender Module Tests

Tests each module independently to verify functionality.
"""

import sys
import os
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def test_session_manager():
    """Test session_manager module"""
    print("\n=== Testing session_manager.py ===")
    try:
        from linux_defender.core.session_manager import SessionManager, SessionState

        # Test imports
        print("✓ Imports successful")

        # Test SessionState enum
        assert hasattr(SessionState, 'ACTIVE')
        assert hasattr(SessionState, 'AWAITING_REVIEW')
        assert hasattr(SessionState, 'COMPLETED')
        assert hasattr(SessionState, 'FAILED')
        assert hasattr(SessionState, 'CANCELLED')
        print("✓ SessionState enum valid")

        # Test SessionManager class exists
        assert SessionManager is not None
        print("✓ SessionManager class available")

        print("✅ session_manager.py: PASS")
        return True
    except Exception as e:
        print(f"❌ session_manager.py: FAIL - {e}")
        return False


def test_termux_bridge():
    """Test termux_bridge module"""
    print("\n=== Testing termux_bridge.py ===")
    try:
        from linux_defender.integrations.termux_bridge import TermuxBridge

        # Test imports
        print("✓ Imports successful")

        # Test TermuxBridge class exists
        assert TermuxBridge is not None
        print("✓ TermuxBridge class available")

        # Test instantiation (without actually connecting)
        config = {
            'termux_host': 'localhost',
            'termux_port': 8022,
            'termux_user': 'test',
            'termux_arianna_path': '/test/path'
        }
        bridge = TermuxBridge(config)
        print("✓ TermuxBridge instantiation successful")

        # Test methods exist
        assert hasattr(bridge, 'test_connection')
        assert hasattr(bridge, 'check_defender_status')
        assert hasattr(bridge, 'capture_tmux_output')
        assert hasattr(bridge, 'detect_issues')
        assert hasattr(bridge, 'restart_defender')
        assert hasattr(bridge, 'sync_resonance_db')
        assert hasattr(bridge, 'full_health_check')
        print("✓ All expected methods present")

        print("✅ termux_bridge.py: PASS")
        return True
    except Exception as e:
        print(f"❌ termux_bridge.py: FAIL - {e}")
        return False


def test_linux_defender_daemon():
    """Test main daemon module"""
    print("\n=== Testing linux_defender_daemon.py ===")
    try:
        # Import main daemon (but don't run it)
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))

        # Just check imports work
        import linux_defender_daemon
        print("✓ Main daemon imports successful")

        # Check constants defined
        assert hasattr(linux_defender_daemon, 'CHECK_INFRASTRUCTURE_INTERVAL')
        assert hasattr(linux_defender_daemon, 'CHECK_TERMUX_INTERVAL')
        assert hasattr(linux_defender_daemon, 'FORTIFICATION_INTERVAL')
        assert hasattr(linux_defender_daemon, 'SYNC_RESONANCE_INTERVAL')
        print("✓ Interval constants defined")

        # Check class exists
        assert hasattr(linux_defender_daemon, 'LinuxDefenderDaemon')
        print("✓ LinuxDefenderDaemon class available")

        print("✅ linux_defender_daemon.py: PASS")
        return True
    except Exception as e:
        print(f"❌ linux_defender_daemon.py: FAIL - {e}")
        return False


def test_defender_identity():
    """Test defender_identity module"""
    print("\n=== Testing defender_identity.py ===")
    try:
        from defender_identity import get_defender_system_prompt, DEFENDER_IDENTITY

        # Test imports
        print("✓ Imports successful")

        # Test DEFENDER_IDENTITY dict
        assert 'name' in DEFENDER_IDENTITY
        assert 'role' in DEFENDER_IDENTITY
        assert 'git_identity' in DEFENDER_IDENTITY
        assert DEFENDER_IDENTITY['git_identity'] == 'iamdefender'
        print("✓ DEFENDER_IDENTITY structure valid")

        # Test system prompt
        prompt = get_defender_system_prompt()
        assert len(prompt) > 0
        assert 'Defender' in prompt
        print("✓ System prompt generation works")

        print("✅ defender_identity.py: PASS")
        return True
    except Exception as e:
        print(f"❌ defender_identity.py: FAIL - {e}")
        return False


def main():
    """Run all module tests"""
    print("🛡️ Linux Defender Module Tests")
    print("=" * 60)

    results = []

    # Test each module
    results.append(("defender_identity", test_defender_identity()))
    results.append(("session_manager", test_session_manager()))
    results.append(("termux_bridge", test_termux_bridge()))
    results.append(("linux_defender_daemon", test_linux_defender_daemon()))

    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary:")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for module, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{module:30} {status}")

    print("=" * 60)
    print(f"Total: {passed}/{total} passed")

    if passed == total:
        print("\n🎉 All modules PASSED")
        return 0
    else:
        print(f"\n⚠️ {total - passed} module(s) FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
