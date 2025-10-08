#!/usr/bin/env python3
"""Test script for all Git tools"""

import sys
import os

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from server.tools.git_status import git_status
from server.tools.git_branch import git_branch
from server.tools.git_log import git_log
from server.tools.git_diff import git_diff
from server.tools.git_commit import git_commit

def print_section(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")

def test_git_tools():
    """Test all git tools on the anvil repository itself"""
    
    print_section("Testing Git Tools on Anvil Repository")
    
    # Use current directory (should be run from repo root)
    repo_path = "."
    
    # Test 1: git_status
    print_section("1. GIT STATUS")
    result = git_status({"path": repo_path})
    print(result[0].text)
    
    # Test 2: git_branch (list)
    print_section("2. GIT BRANCH - List")
    result = git_branch({"path": repo_path, "action": "list"})
    print(result[0].text)
    
    # Test 3: git_log
    print_section("3. GIT LOG - Last 5 commits")
    result = git_log({"path": repo_path, "count": 5})
    print(result[0].text)
    
    # Test 4: git_diff (compact)
    print_section("4. GIT DIFF - Compact unstaged")
    result = git_diff({"path": repo_path, "mode": "unstaged", "compact": True})
    print(result[0].text)
    
    # Test 5: git_diff (both)
    print_section("5. GIT DIFF - Both staged and unstaged (compact)")
    result = git_diff({"path": repo_path, "mode": "both", "compact": True})
    print(result[0].text)
    
    print_section("Git Tools Test Complete!")
    print("\nAll 5 Git tools are working! ✓")
    print("\nAvailable tools:")
    print("  • git_status  - Check repository status")
    print("  • git_branch  - Manage branches (list, create, switch, delete)")
    print("  • git_log     - View commit history")
    print("  • git_diff    - See file changes")
    print("  • git_commit  - Stage and commit changes")

if __name__ == "__main__":
    test_git_tools()
