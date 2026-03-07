#!/usr/bin/env python3
# Copyright (c) 2026 TrailLensCo
# All rights reserved.
#
# This file is proprietary and confidential.

"""
Python Code Validation Script for TrailLens API (DynamoDB)

Validates all Python code for:
- Syntax errors (compilation)
- PEP 8 compliance (black, flake8, isort)
- Undefined names and imports
- Code formatting standards

Usage:
    python scripts/validate-python.py [--fix]

Options:
    --fix    Automatically fix formatting issues with black and isort
"""

import ast
import os
import subprocess
import sys
from pathlib import Path


class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    NC = "\033[0m"  # No Color


def print_header(msg):
    print(f"\n{Colors.BLUE}{'=' * 70}{Colors.NC}")
    print(f"{Colors.BLUE}{msg}{Colors.NC}")
    print(f"{Colors.BLUE}{'=' * 70}{Colors.NC}\n")


def print_success(msg):
    print(f"{Colors.GREEN}✓{Colors.NC} {msg}")


def print_error(msg):
    print(f"{Colors.RED}✗{Colors.NC} {msg}")


def print_warning(msg):
    print(f"{Colors.YELLOW}⚠{Colors.NC} {msg}")


def check_tools():
    """Check if required tools are installed."""
    print_header("Checking Required Tools")

    tools = {
        "black": ["python", "-m", "black", "--version"],
        "flake8": ["python", "-m", "flake8", "--version"],
        "isort": ["python", "-m", "isort", "--version"],
    }

    missing = []
    for tool, cmd in tools.items():
        try:
            subprocess.run(cmd, capture_output=True, check=True)
            print_success(f"{tool} is installed")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print_error(f"{tool} is not installed")
            missing.append(tool)

    if missing:
        print_error(f"\nMissing tools: {', '.join(missing)}")
        print(f"Install with: pip install {' '.join(missing)}")
        return False

    return True


def check_syntax(python_files):
    """Check Python files for syntax errors using AST parser."""
    print_header("Checking Syntax (AST Compilation)")

    errors = []
    for filepath in python_files:
        try:
            with open(filepath, "r") as f:
                ast.parse(f.read(), filename=str(filepath))
            print_success(f"{filepath}")
        except SyntaxError as e:
            error_msg = f"{filepath}:{e.lineno}:{e.offset}: {e.msg}"
            errors.append(error_msg)
            print_error(error_msg)

    if errors:
        print_error(f"\n{len(errors)} syntax error(s) found")
        return False

    print_success(f"\nAll {len(python_files)} files have valid syntax")
    return True


def check_formatting(python_dirs, fix=False):
    """Check Python code formatting with black."""
    print_header("Checking Code Formatting (black)")

    cmd = [
        "python",
        "-m",
        "black",
        "--line-length",
        "125",
        f"--exclude=({'|'.join(EXCLUDE_DIRS)})",
    ]
    if not fix:
        cmd.extend(["--check", "--diff"])

    cmd.extend(python_dirs)

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        if fix:
            print_success("All files formatted successfully")
        else:
            print_success("All files are properly formatted")
        return True
    else:
        if fix:
            print_error("Some files could not be formatted")
            print(result.stderr)
        else:
            print_warning("Some files need formatting")
            print(result.stdout)
            print("\nRun with --fix to automatically format")
        return False


def check_imports(python_dirs, fix=False):
    """Check and organize imports with isort."""
    print_header("Checking Import Organization (isort)")

    cmd = ["python", "-m", "isort"]
    if not fix:
        cmd.extend(["--check-only", "--diff"])

    cmd.extend(
        [
            "--profile",
            "black",
            "--skip",
            ".venv",
            "--skip",
            "venv",
            "--skip",
            ".env",
            "--skip",
            "env",
        ]
    )
    cmd.extend(python_dirs)

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print_success("All imports are properly organized")
        return True
    else:
        if fix:
            print_warning("Imports reorganized")
        else:
            print_warning("Some imports need reorganization")
            print(result.stdout)
            print("\nRun with --fix to automatically organize imports")
        return False


def check_linting(python_dirs):
    """Check code quality with flake8."""
    print_header("Checking Code Quality (flake8)")

    cmd = [
        "python",
        "-m",
        "flake8",
        *python_dirs,
        "--max-line-length=125",
        "--extend-ignore=E203,W503",
        "--show-source",
        f"--exclude={EXCLUDE_DIRS_STR}",
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print_success("No linting issues found")
        return True
    else:
        error_lines = [line for line in result.stdout.split("\n") if line.strip()]
        print_warning(f"Found {len(error_lines)} linting issues")
        return False


def check_undefined_names(python_dirs):
    """Check for undefined names and critical errors."""
    print_header("Checking for Undefined Names (flake8 critical)")

    cmd = [
        "python",
        "-m",
        "flake8",
        *python_dirs,
        "--select=E999,F821,F822,F823",
        "--show-source",
        f"--exclude={EXCLUDE_DIRS_STR}",
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print_success("No undefined names or critical errors")
        return True
    else:
        print_error("Critical errors found:")
        print(result.stdout)
        return False


# Directories excluded from all scanning, linting, and formatting.
EXCLUDE_DIRS = {
    ".venv",
    "venv",
    ".env",
    "env",
    "__pycache__",
    ".git",
    "node_modules",
    ".pytest_cache",
    "htmlcov",
    "dist",
    "build",
}

# Comma-separated string for tools that accept --exclude flags.
EXCLUDE_DIRS_STR = ",".join(EXCLUDE_DIRS)


def find_python_files(base_dirs):
    """Find all Python files in the specified directories.

    Excludes virtual environment and cache directories.

    Args:
        base_dirs: List of directory paths to search.

    Returns:
        List of Path objects for all found .py files.
    """
    python_files = []

    for base_dir in base_dirs:
        for root, dirs, files in os.walk(base_dir):
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            for file in files:
                if file.endswith(".py"):
                    python_files.append(Path(root) / file)

    return python_files


def main():
    """Main validation routine."""
    fix = "--fix" in sys.argv

    # Get repository root (parent of scripts directory)
    repo_root = Path(__file__).parent.parent
    os.chdir(repo_root)

    print(f"\n{Colors.BLUE}TrailLens Python Code Validator{Colors.NC}")
    print(f"{Colors.BLUE}Repository: {repo_root.name}{Colors.NC}")
    print(f"Mode: {'FIX' if fix else 'CHECK'}\n")

    # Define directories to check
    python_dirs = ["pulumi/", "scripts/"]

    # Find all Python files
    python_files = find_python_files(python_dirs)
    print(f"Found {len(python_files)} Python files\n")

    # Run validation checks
    checks = []

    if not check_tools():
        sys.exit(1)

    checks.append(("Syntax", check_syntax(python_files)))
    checks.append(("Formatting", check_formatting(python_dirs, fix)))
    checks.append(("Imports", check_imports(python_dirs, fix)))
    checks.append(("Undefined Names", check_undefined_names(python_dirs)))
    checks.append(("Linting", check_linting(python_dirs)))

    # Summary
    print_header("Validation Summary")

    passed = sum(1 for _, result in checks if result)
    total = len(checks)

    for check_name, result in checks:
        if result:
            print_success(f"{check_name}: PASSED")
        else:
            print_error(f"{check_name}: FAILED")

    print(f"\n{passed}/{total} checks passed")

    if passed == total:
        print_success("\n✅ All validation checks passed!")
        sys.exit(0)
    else:
        print_error("\n❌ Some validation checks failed")
        if not fix:
            print("\nRun with --fix to automatically fix some issues:")
            print(f"  python {sys.argv[0]} --fix")
        sys.exit(1)


if __name__ == "__main__":
    main()
