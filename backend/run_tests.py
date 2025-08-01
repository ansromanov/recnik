#!/usr/bin/env python3
"""
Test runner script for Serbian Vocabulary Application
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, cwd=None):
    """Run a command and return the result"""
    try:
        result = subprocess.run(
            cmd, shell=True, cwd=cwd, capture_output=True, text=True, check=False
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)


def install_test_dependencies():
    """Install test dependencies"""
    print("📦 Installing test dependencies...")

    # Install main requirements first
    returncode, stdout, stderr = run_command("pip install -r requirements.txt")
    if returncode != 0:
        print(f"❌ Failed to install main requirements: {stderr}")
        return False

    # Install test requirements
    returncode, stdout, stderr = run_command("pip install -r requirements-test.txt")
    if returncode != 0:
        print(f"❌ Failed to install test requirements: {stderr}")
        return False

    print("✅ Test dependencies installed successfully")
    return True


def run_tests(test_type="all", coverage=True, verbose=True, markers=None):
    """Run tests with specified options"""

    # Base pytest command
    cmd_parts = ["python", "-m", "pytest"]

    # Add verbosity
    if verbose:
        cmd_parts.append("-v")

    # Add coverage if requested
    if coverage:
        cmd_parts.extend(
            ["--cov=.", "--cov-report=term-missing", "--cov-report=html:htmlcov"]
        )

    # Add test markers if specified
    if markers:
        for marker in markers:
            cmd_parts.extend(["-m", marker])

    # Add specific test files/directories based on test type
    if test_type == "unit":
        cmd_parts.extend(["-m", "unit"])
    elif test_type == "integration":
        cmd_parts.extend(["-m", "integration"])
    elif test_type == "models":
        cmd_parts.append("tests/test_models.py")
    elif test_type == "services":
        cmd_parts.extend(
            [
                "tests/test_text_processor.py",
                "tests/test_translation_cache.py",
                "tests/test_image_service.py",
            ]
        )
    elif test_type == "fast":
        cmd_parts.extend(["-m", "not slow"])
    elif test_type != "all":
        # Assume it's a specific test file or path
        cmd_parts.append(test_type)

    cmd = " ".join(cmd_parts)

    print(f"🧪 Running tests: {cmd}")
    print("-" * 80)

    returncode, stdout, stderr = run_command(cmd)

    # Print output
    if stdout:
        print(stdout)
    if stderr:
        print(stderr, file=sys.stderr)

    return returncode == 0


def check_environment():
    """Check if the environment is set up correctly"""
    print("🔍 Checking test environment...")

    # Check if we're in the right directory
    if not Path("tests").exists():
        print("❌ Tests directory not found. Are you in the backend directory?")
        return False

    # Check for pytest.ini
    if not Path("pytest.ini").exists():
        print("❌ pytest.ini not found")
        return False

    # Check Python version
    python_version = sys.version_info
    if python_version.major < 3 or (
        python_version.major == 3 and python_version.minor < 8
    ):
        print(
            f"❌ Python 3.8+ required, found {python_version.major}.{python_version.minor}"
        )
        return False

    print("✅ Environment looks good")
    return True


def generate_test_report():
    """Generate a comprehensive test report"""
    print("📊 Generating test report...")

    # Run tests with coverage and JUnit XML output
    cmd = [
        "python",
        "-m",
        "pytest",
        "--cov=.",
        "--cov-report=html:htmlcov",
        "--cov-report=xml:coverage.xml",
        "--junitxml=test-results.xml",
        "-v",
    ]

    returncode, stdout, stderr = run_command(" ".join(cmd))

    if returncode == 0:
        print("✅ Test report generated successfully")
        print("📁 Coverage report: htmlcov/index.html")
        print("📁 JUnit XML: test-results.xml")
        print("📁 Coverage XML: coverage.xml")
    else:
        print("❌ Failed to generate test report")

    return returncode == 0


def main():
    parser = argparse.ArgumentParser(
        description="Run tests for Serbian Vocabulary Application"
    )

    parser.add_argument(
        "--type",
        "-t",
        choices=["all", "unit", "integration", "models", "services", "fast"],
        default="all",
        help="Type of tests to run",
    )

    parser.add_argument(
        "--no-coverage", "-nc", action="store_true", help="Disable coverage reporting"
    )

    parser.add_argument("--quiet", "-q", action="store_true", help="Run in quiet mode")

    parser.add_argument(
        "--install-deps",
        "-i",
        action="store_true",
        help="Install test dependencies before running tests",
    )

    parser.add_argument(
        "--report", "-r", action="store_true", help="Generate comprehensive test report"
    )

    parser.add_argument(
        "--markers",
        "-m",
        nargs="+",
        help="Pytest markers to filter tests (e.g., --markers unit redis)",
    )

    parser.add_argument(
        "test_path", nargs="?", help="Specific test file or path to run"
    )

    args = parser.parse_args()

    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)

    # Check environment
    if not check_environment():
        sys.exit(1)

    # Install dependencies if requested
    if args.install_deps:
        if not install_test_dependencies():
            sys.exit(1)

    # Generate report if requested
    if args.report:
        success = generate_test_report()
        sys.exit(0 if success else 1)

    # Determine test type
    test_type = args.test_path if args.test_path else args.type

    # Run tests
    success = run_tests(
        test_type=test_type,
        coverage=not args.no_coverage,
        verbose=not args.quiet,
        markers=args.markers,
    )

    if success:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
