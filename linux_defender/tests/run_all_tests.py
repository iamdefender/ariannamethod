#!/usr/bin/env python3
"""
Linux Defender - Complete Test Suite

Runs all tests for Linux Defender modules and daemon.
"""

import sys
import subprocess
from pathlib import Path

def run_test_file(test_file):
    """Run a test file and return result"""
    print(f"\n{'='*60}")
    print(f"Running: {test_file.name}")
    print('='*60)

    try:
        result = subprocess.run(
            [sys.executable, str(test_file)],
            cwd=test_file.parent.parent.parent,
            timeout=30
        )
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Test file failed: {e}")
        return False


def main():
    """Run all tests"""
    print("🛡️ Linux Defender - Complete Test Suite")
    print("="*60)

    tests_dir = Path(__file__).parent

    # Find all test files
    test_files = [
        tests_dir / "test_modules.py",
        tests_dir / "test_daemon.py"
    ]

    results = []

    for test_file in test_files:
        if test_file.exists():
            results.append((test_file.name, run_test_file(test_file)))
        else:
            print(f"⚠️ Test file not found: {test_file}")
            results.append((test_file.name, False))

    # Final summary
    print("\n" + "="*60)
    print("🏁 Final Test Summary")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:30} {status}")

    print("="*60)
    print(f"Total Test Suites: {passed}/{total} passed")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED - Linux Defender fully functional")
        return 0
    else:
        print(f"\n⚠️ {total - passed} test suite(s) FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
