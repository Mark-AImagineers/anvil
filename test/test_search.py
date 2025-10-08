#!/usr/bin/env python3
"""Test script for search_files tool"""

import sys
import os

# Add server to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'server'))

from tools.search_files import search_files

def test_search():
    print("=" * 60)
    print("Testing search_files tool")
    print("=" * 60)
    
    # Test 1: Search for Python files
    print("\n1. Searching for all .py files in current directory:")
    result = search_files({
        "path": ".",
        "file_extensions": [".py"],
        "max_results": 10
    })
    print(result[0].text)
    
    # Test 2: Search for files with specific pattern
    print("\n2. Searching for files matching 'test_*':")
    result = search_files({
        "path": ".",
        "pattern": "test_*",
        "max_results": 10
    })
    print(result[0].text)
    
    # Test 3: Search for content in files
    print("\n3. Searching for 'registry' in Python files:")
    result = search_files({
        "path": "./server",
        "content": "registry",
        "file_extensions": [".py"],
        "case_sensitive": False,
        "max_results": 5
    })
    print(result[0].text)
    
    print("\n" + "=" * 60)
    print("Tests complete!")
    print("=" * 60)

if __name__ == "__main__":
    test_search()
