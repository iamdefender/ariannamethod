#!/usr/bin/env python3
"""
Linux Defender Daemon Tests

Tests the main daemon functionality.
"""

import sys
import os
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def test_daemon_cli():
    """Test daemon CLI commands"""
    print("\n=== Testing linux_defender_daemon.py CLI ===")

    import subprocess

    daemon_script = Path(__file__).parent.parent.parent / "linux_defender_daemon.py"

    # Test status command
    try:
        result = subprocess.run(
            [sys.executable, str(daemon_script), "status"],
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0
        assert "LINUX DEFENDER" in result.stdout
        print("✓ status command works")
    except Exception as e:
        print(f"❌ status command failed: {e}")
        return False

    # Test logs command (should fail gracefully if no logs)
    try:
        result = subprocess.run(
            [sys.executable, str(daemon_script), "logs"],
            capture_output=True,
            text=True,
            timeout=10
        )
        # OK if returns 0 or 1 (no logs)
        print("✓ logs command works")
    except Exception as e:
        print(f"❌ logs command failed: {e}")
        return False

    print("✅ Daemon CLI: PASS")
    return True


def test_daemon_initialization():
    """Test daemon can be initialized"""
    print("\n=== Testing Daemon Initialization ===")

    try:
        import linux_defender_daemon

        # Check constants
        assert hasattr(linux_defender_daemon, 'CHECK_INFRASTRUCTURE_INTERVAL')
        assert linux_defender_daemon.CHECK_INFRASTRUCTURE_INTERVAL == 180
        print("✓ Infrastructure interval: 180s")

        assert hasattr(linux_defender_daemon, 'CHECK_TERMUX_INTERVAL')
        assert linux_defender_daemon.CHECK_TERMUX_INTERVAL == 120
        print("✓ Termux check interval: 120s")

        assert hasattr(linux_defender_daemon, 'FORTIFICATION_INTERVAL')
        assert linux_defender_daemon.FORTIFICATION_INTERVAL == 1800
        print("✓ Fortification interval: 1800s")

        assert hasattr(linux_defender_daemon, 'SYNC_RESONANCE_INTERVAL')
        assert linux_defender_daemon.SYNC_RESONANCE_INTERVAL == 300
        print("✓ Resonance sync interval: 300s")

        # Check paths
        assert hasattr(linux_defender_daemon, 'HOME')
        assert hasattr(linux_defender_daemon, 'ARIANNA_PATH')
        assert hasattr(linux_defender_daemon, 'DEFENDER_DIR')
        assert hasattr(linux_defender_daemon, 'LOGS_DIR')
        print("✓ All path constants defined")

        print("✅ Daemon Initialization: PASS")
        return True
    except Exception as e:
        print(f"❌ Daemon Initialization: FAIL - {e}")
        return False


def test_daemon_class_methods():
    """Test daemon class has required methods"""
    print("\n=== Testing Daemon Class Methods ===")

    try:
        import linux_defender_daemon

        daemon_class = linux_defender_daemon.LinuxDefenderDaemon

        # Check all required methods exist
        required_methods = [
            '__init__',
            '_load_config',
            '_load_git_credentials',
            '_load_state',
            '_save_state',
            'log',
            '_log_to_resonance',
            'check_infrastructure',
            'check_termux_defender',
            'sync_resonance_from_termux',
            'run_fortification',
            'daemon_loop'
        ]

        for method in required_methods:
            assert hasattr(daemon_class, method), f"Missing method: {method}"
            print(f"✓ Method exists: {method}")

        print("✅ Daemon Class Methods: PASS")
        return True
    except Exception as e:
        print(f"❌ Daemon Class Methods: FAIL - {e}")
        return False


def main():
    """Run all daemon tests"""
    print("🛡️ Linux Defender Daemon Tests")
    print("=" * 60)

    results = []

    # Run tests
    results.append(("Daemon Initialization", test_daemon_initialization()))
    results.append(("Daemon Class Methods", test_daemon_class_methods()))
    results.append(("Daemon CLI", test_daemon_cli()))

    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary:")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:30} {status}")

    print("=" * 60)
    print(f"Total: {passed}/{total} passed")

    if passed == total:
        print("\n🎉 All daemon tests PASSED")
        return 0
    else:
        print(f"\n⚠️ {total - passed} test(s) FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
