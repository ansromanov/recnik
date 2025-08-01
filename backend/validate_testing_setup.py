#!/usr/bin/env python3
"""
Testing Setup Validation Script
Validates that the testing infrastructure is properly configured.
"""

import sys
import os
import subprocess
import importlib.util
from pathlib import Path


def check_file_exists(file_path, description):
    """Check if a file exists and print status"""
    if os.path.exists(file_path):
        print(f"✅ {description}: {file_path}")
        return True
    else:
        print(f"❌ {description}: {file_path} (missing)")
        return False


def check_python_module(module_name):
    """Check if a Python module can be imported"""
    try:
        importlib.import_module(module_name)
        print(f"✅ Python module: {module_name}")
        return True
    except ImportError:
        print(f"❌ Python module: {module_name} (not available)")
        return False


def run_command(command, description):
    """Run a command and check if it succeeds"""
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, cwd="."
        )
        if result.returncode == 0:
            print(f"✅ {description}")
            return True, result.stdout
        else:
            print(f"❌ {description}: {result.stderr}")
            return False, result.stderr
    except Exception as e:
        print(f"❌ {description}: {str(e)}")
        return False, str(e)


def main():
    """Main validation function"""
    print("🧪 Serbian Vocabulary App - Testing Setup Validation")
    print("=" * 60)

    # Change to backend directory
    os.chdir(Path(__file__).parent)

    # Track validation results
    checks_passed = 0
    total_checks = 0

    print("\n📁 File Structure Validation")
    print("-" * 30)

    files_to_check = [
        ("pytest.ini", "Pytest configuration"),
        ("requirements-test.txt", "Test dependencies"),
        ("run_tests.py", "Test runner script"),
        ("TESTING.md", "Testing documentation"),
        ("tests/__init__.py", "Test package init"),
        ("tests/conftest.py", "Pytest fixtures"),
        ("tests/test_models.py", "Model tests"),
        ("tests/test_text_processor.py", "Text processor tests"),
        ("tests/test_translation_cache.py", "Translation cache tests"),
        ("tests/test_image_service.py", "Image service tests"),
    ]

    for file_path, description in files_to_check:
        total_checks += 1
        if check_file_exists(file_path, description):
            checks_passed += 1

    print("\n📦 Python Dependencies Validation")
    print("-" * 35)

    dependencies_to_check = [
        "pytest",
        "pytest_cov",
        "fakeredis",
        "unittest.mock",
    ]

    for dep in dependencies_to_check:
        total_checks += 1
        if check_python_module(dep):
            checks_passed += 1

    print("\n⚙️ Test Configuration Validation")
    print("-" * 35)

    # Check pytest configuration
    total_checks += 1
    success, output = run_command("pytest --collect-only -q", "Pytest test collection")
    if success:
        checks_passed += 1
        print(f"   Found tests: {output.count('test_')} test functions")

    # Check if pytest markers are recognized
    total_checks += 1
    success, output = run_command("pytest --markers", "Pytest markers check")
    if success:
        checks_passed += 1

    print("\n🚀 Basic Test Execution")
    print("-" * 25)

    # Try to run a simple test to validate the setup
    total_checks += 1
    success, output = run_command(
        "python -m pytest tests/ --tb=short -v", "Basic test execution"
    )
    if success:
        checks_passed += 1
        print("   Test execution successful!")
    else:
        print(f"   Test execution output: {output}")

    print("\n📊 Test Runner Validation")
    print("-" * 25)

    # Test the custom test runner
    total_checks += 1
    success, output = run_command("python run_tests.py --help", "Test runner help")
    if success:
        checks_passed += 1

    print("\n" + "=" * 60)
    print(f"🏁 Validation Summary: {checks_passed}/{total_checks} checks passed")

    if checks_passed == total_checks:
        print("🎉 All checks passed! Testing setup is ready to use.")
        print("\n💡 Quick Start:")
        print("   python run_tests.py              # Run all tests")
        print("   python run_tests.py --type unit  # Run unit tests only")
        print("   python run_tests.py --report     # Generate comprehensive report")
        return True
    else:
        print(
            f"⚠️  {total_checks - checks_passed} checks failed. Please review the issues above."
        )
        print("\n🔧 Next Steps:")
        print(
            "   1. Install missing dependencies: pip install -r requirements-test.txt"
        )
        print("   2. Check file permissions and paths")
        print("   3. Review error messages above")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
