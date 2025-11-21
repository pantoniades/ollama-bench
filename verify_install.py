#!/usr/bin/env python3
"""Verify ollama-bench installation and dependencies."""
import sys

def check_dependency(name):
    try:
        __import__(name)
        print(f"✓ {name} installed")
        return True
    except ImportError:
        print(f"✗ {name} NOT installed")
        return False

def main():
    print("Checking ollama-bench installation...\n")

    # Check Python version
    py_version = sys.version_info
    print(f"Python version: {py_version.major}.{py_version.minor}.{py_version.micro}")
    if py_version < (3, 10):
        print("✗ Python 3.10+ required")
        return False
    print("✓ Python version OK\n")

    # Check dependencies
    print("Checking dependencies:")
    all_ok = True
    all_ok &= check_dependency("click")
    all_ok &= check_dependency("rich")
    all_ok &= check_dependency("ollama")
    all_ok &= check_dependency("ollama_bench")

    print()
    if all_ok:
        print("✓ All dependencies installed!")
        print("\nYou can run: ollama-bench benchmark")
        print("Or: python -m ollama_bench benchmark")
        return True
    else:
        print("✗ Some dependencies missing!")
        print("\nMake sure your venv is activated:")
        print("  source .venv/bin/activate")
        print("\nThen reinstall:")
        print("  pip install -e .")
        return False

if __name__ == "__main__":
    sys.exit(0 if main() else 1)
