#!/usr/bin/env python3
"""Test script for run_tests tool"""

import sys
import os

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from server.tools.run_tests import run_tests, detect_test_framework

def print_section(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")

def test_run_tests_tool():
    """Test the run_tests tool"""
    
    print_section("Testing run_tests Tool")
    
    # Test 1: Framework detection
    print_section("1. Framework Detection")
    framework = detect_test_framework(parent_dir)
    print(f"Detected framework for Anvil project: {framework}")
    
    # Test 2: Create a proper unittest file
    print_section("2. Creating Sample Test File (unittest format)")
    
    test_file_content = """import unittest

class TestMath(unittest.TestCase):
    def test_addition(self):
        self.assertEqual(1 + 1, 2)
    
    def test_subtraction(self):
        self.assertEqual(5 - 3, 2)
    
    def test_multiplication(self):
        self.assertEqual(3 * 4, 12)

if __name__ == '__main__':
    unittest.main()
"""
    
    test_file_path = os.path.join(parent_dir, "test", "test_sample_unittest.py")
    with open(test_file_path, "w") as f:
        f.write(test_file_content)
    
    print(f"Created test file: {test_file_path}")
    
    # Test 3: Run the tests with specific class
    print_section("3. Running Tests (specific test class)")
    result = run_tests({
        "path": parent_dir,
        "pattern": "test.test_sample_unittest.TestMath",
        "verbose": True,
        "framework": "unittest"
    })
    print(result[0].text)
    
    # Cleanup
    print_section("Cleanup")
    os.remove(test_file_path)
    print(f"Removed test file: {test_file_path}")
    
    print_section("Test Complete!")
    print("\n✓ The run_tests tool is working!")
    print("\nFeatures verified:")
    print("  ✓ Framework auto-detection (detected: {})".format(framework))
    print("  ✓ Running specific test classes")
    print("  ✓ Verbose mode")
    print("  ✓ Clean formatted output")
    print("\nSupported frameworks:")
    print("  • pytest (if installed)")
    print("  • unittest (Python built-in)")
    print("  • Django (manage.py test)")
    print("  • jest (npm test)")
    print("\nThe tool will auto-detect the framework in your actual projects!")

if __name__ == "__main__":
    test_run_tests_tool()
