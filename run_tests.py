#!/usr/bin/env python3
"""
Test Runner Script
Convenient wrapper for running different test suites
"""

import sys
import subprocess
from pathlib import Path


def run_command(cmd: list[str]) -> int:
    """Run command and return exit code"""
    print(f"\n{'='*70}")
    print(f"Running: {' '.join(cmd)}")
    print(f"{'='*70}\n")
    
    result = subprocess.run(cmd)
    return result.returncode


def main():
    """Main test runner"""
    if len(sys.argv) < 2:
        print("Usage: python run_tests.py [command]")
        print("\nAvailable commands:")
        print("  all          - Run all tests")
        print("  unit         - Run unit tests only")
        print("  integration  - Run integration tests only")
        print("  service      - Run service layer tests")
        print("  agent        - Run agent tests")
        print("  api          - Run API endpoint tests")
        print("  auth         - Run authentication tests")
        print("  coverage     - Run tests with coverage report")
        print("  html         - Generate HTML coverage report")
        print("  fast         - Run tests skipping slow ones")
        print("  file <path>  - Run specific test file")
        print("\nExamples:")
        print("  python run_tests.py all")
        print("  python run_tests.py unit")
        print("  python run_tests.py coverage")
        print("  python run_tests.py file tests/test_chat_service.py")
        return 1
    
    command = sys.argv[1].lower()
    
    # Command mapping
    commands = {
        "all": ["pytest", "-v"],
        "unit": ["pytest", "-m", "unit", "-v"],
        "integration": ["pytest", "-m", "integration", "-v"],
        "service": ["pytest", "-m", "service", "-v"],
        "agent": ["pytest", "-m", "agent", "-v"],
        "api": ["pytest", "-m", "api", "-v"],
        "auth": ["pytest", "-m", "auth", "-v"],
        "coverage": ["pytest", "--cov=app", "--cov-report=term-missing", "-v"],
        "html": ["pytest", "--cov=app", "--cov-report=html", "--cov-report=term", "-v"],
        "fast": ["pytest", "-m", "not slow", "-v"],
    }
    
    if command == "file":
        if len(sys.argv) < 3:
            print("Error: Please specify test file path")
            print("Example: python run_tests.py file tests/test_chat_service.py")
            return 1
        
        test_file = sys.argv[2]
        if not Path(test_file).exists():
            print(f"Error: Test file not found: {test_file}")
            return 1
        
        return run_command(["pytest", test_file, "-v"])
    
    elif command in commands:
        exit_code = run_command(commands[command])
        
        # Print summary
        print(f"\n{'='*70}")
        if exit_code == 0:
            print("✅ All tests passed!")
        else:
            print("❌ Some tests failed!")
        print(f"{'='*70}\n")
        
        # If HTML coverage was generated, print path
        if command == "html" and exit_code == 0:
            print("📊 Coverage report generated: htmlcov/index.html")
            print("   Open it in your browser to view detailed coverage\n")
        
        return exit_code
    
    else:
        print(f"Error: Unknown command '{command}'")
        print("Run 'python run_tests.py' for usage information")
        return 1


if __name__ == "__main__":
    sys.exit(main())
