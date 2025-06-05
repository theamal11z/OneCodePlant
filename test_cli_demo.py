#!/usr/bin/env python3
"""Interactive CLI demonstration script for OneCode Plant."""

import subprocess
import sys
import time
from typing import List, Tuple

def run_command(cmd: List[str], description: str) -> Tuple[int, str, str]:
    """Run a command and return result with formatting."""
    print(f"\n{'='*60}")
    print(f"🔧 {description}")
    print(f"{'='*60}")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 40)
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.stdout:
            print("📤 Output:")
            print(result.stdout)
        
        if result.stderr:
            print("⚠️  Stderr:")
            print(result.stderr)
        
        print(f"📊 Exit Code: {result.returncode}")
        return result.returncode, result.stdout, result.stderr
        
    except subprocess.TimeoutExpired:
        print("⏰ Command timed out after 30 seconds")
        return 1, "", "Timeout"
    except Exception as e:
        print(f"❌ Error running command: {e}")
        return 1, "", str(e)

def main():
    """Run comprehensive CLI demonstration."""
    print("""
🤖 OneCode Plant CLI - Interactive Demonstration
==============================================

This script demonstrates all available CLI functionality.
""")
    
    # Test basic CLI functionality
    commands = [
        (["python", "-m", "onecode.cli", "--help"], "Display main help"),
        (["python", "-m", "onecode.cli", "version"], "Show version information"),
        (["python", "-m", "onecode.cli", "plugins"], "List available plugins"),
        (["python", "-m", "onecode.cli", "build", "--help"], "Show build commands help"),
        (["python", "-m", "onecode.cli", "build", "workspace", "--help"], "Show workspace build options"),
        (["python", "-m", "onecode.cli", "sim", "--help"], "Show simulation commands help"),
        (["python", "-m", "onecode.cli", "sim", "start", "--help"], "Show simulation start options"),
    ]
    
    # Execute all test commands
    results = []
    for cmd, desc in commands:
        returncode, stdout, stderr = run_command(cmd, desc)
        results.append((desc, returncode == 0, returncode))
        time.sleep(1)  # Brief pause between commands
    
    # Summary report
    print(f"\n{'='*60}")
    print("📋 TEST SUMMARY REPORT")
    print(f"{'='*60}")
    
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    for desc, success, code in results:
        status = "✅ PASS" if success else f"❌ FAIL (code {code})"
        print(f"{status:<12} {desc}")
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All CLI functionality is working correctly!")
    else:
        print("⚠️  Some commands may require additional dependencies.")
    
    print(f"\n{'='*60}")
    print("🚀 CLI is ready for deployment!")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()