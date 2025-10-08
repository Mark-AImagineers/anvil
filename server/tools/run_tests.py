# server/tools/run_tests.py
import subprocess
import os
import json
from pathlib import Path
from mcp.types import TextContent
from server.registry import registry


def is_command_available(command: list, cwd: str) -> bool:
    """Check if a command is available"""
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=5
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def detect_test_framework(path: str) -> str:
    """Detect which test framework to use"""
    
    # Check for pytest
    pytest_indicators = [
        'pytest.ini',
        'pyproject.toml',
        'setup.cfg',
        '.pytest_cache'
    ]
    
    for indicator in pytest_indicators:
        if os.path.exists(os.path.join(path, indicator)):
            # Verify pytest is installed
            if is_command_available(["python3", "-m", "pytest", "--version"], path):
                return "pytest"
    
    # Check for pytest in requirements
    req_files = ['requirements.txt', 'requirements-dev.txt', 'dev-requirements.txt']
    for req_file in req_files:
        req_path = os.path.join(path, req_file)
        if os.path.exists(req_path):
            try:
                with open(req_path, 'r') as f:
                    content = f.read().lower()
                    if 'pytest' in content:
                        # Check if actually installed
                        if is_command_available(["python3", "-m", "pytest", "--version"], path):
                            return "pytest"
            except:
                pass
    
    # Check for Django (uses unittest or pytest)
    if os.path.exists(os.path.join(path, 'manage.py')):
        # Prefer pytest for Django if available
        if is_command_available(["python3", "-m", "pytest", "--version"], path):
            return "pytest"
        return "django"
    
    # Check for jest (JavaScript)
    package_json = os.path.join(path, 'package.json')
    if os.path.exists(package_json):
        try:
            with open(package_json, 'r') as f:
                data = json.load(f)
                if 'jest' in data.get('devDependencies', {}) or 'jest' in data.get('dependencies', {}):
                    if is_command_available(["npm", "test", "--", "--version"], path):
                        return "jest"
        except:
            pass
    
    # Check if there are any test files
    test_patterns = ['test_*.py', '*_test.py', 'tests.py']
    for pattern in test_patterns:
        if list(Path(path).rglob(pattern)):
            # Check if pytest is available
            if is_command_available(["python3", "-m", "pytest", "--version"], path):
                return "pytest"
            # Fall back to unittest (always available with Python)
            return "unittest"
    
    return "unknown"


def run_pytest(path: str, pattern: str, verbose: bool, coverage: bool, markers: str, fail_fast: bool, parallel: bool) -> dict:
    """Run tests with pytest"""
    cmd = ["python3", "-m", "pytest"]
    
    # Add verbosity
    if verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")
    
    # Add coverage
    if coverage:
        cmd.extend(["--cov=.", "--cov-report=term-missing"])
    
    # Add markers
    if markers:
        cmd.extend(["-m", markers])
    
    # Fail fast
    if fail_fast:
        cmd.append("-x")
    
    # Parallel execution
    if parallel:
        cmd.extend(["-n", "auto"])
    
    # Add pattern if specified
    if pattern:
        cmd.append(pattern)
    
    # Run tests
    result = subprocess.run(
        cmd,
        cwd=path,
        capture_output=True,
        text=True,
        timeout=300  # 5 minute timeout
    )
    
    return {
        "framework": "pytest",
        "command": " ".join(cmd),
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr
    }


def run_unittest(path: str, pattern: str, verbose: bool) -> dict:
    """Run tests with unittest"""
    cmd = ["python3", "-m", "unittest"]
    
    if verbose:
        cmd.append("-v")
    
    if pattern:
        cmd.append(pattern)
    else:
        cmd.append("discover")
    
    result = subprocess.run(
        cmd,
        cwd=path,
        capture_output=True,
        text=True,
        timeout=300
    )
    
    return {
        "framework": "unittest",
        "command": " ".join(cmd),
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr
    }


def run_django_tests(path: str, pattern: str, verbose: bool, fail_fast: bool, parallel: bool) -> dict:
    """Run Django tests"""
    cmd = ["python3", "manage.py", "test"]
    
    if verbose:
        cmd.append("--verbosity=2")
    
    if fail_fast:
        cmd.append("--failfast")
    
    if parallel:
        cmd.append("--parallel")
    
    if pattern:
        cmd.append(pattern)
    
    result = subprocess.run(
        cmd,
        cwd=path,
        capture_output=True,
        text=True,
        timeout=300
    )
    
    return {
        "framework": "django",
        "command": " ".join(cmd),
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr
    }


def run_jest(path: str, pattern: str, verbose: bool, coverage: bool) -> dict:
    """Run tests with jest"""
    cmd = ["npm", "test", "--"]
    
    if verbose:
        cmd.append("--verbose")
    
    if coverage:
        cmd.append("--coverage")
    
    if pattern:
        cmd.append(pattern)
    
    result = subprocess.run(
        cmd,
        cwd=path,
        capture_output=True,
        text=True,
        timeout=300
    )
    
    return {
        "framework": "jest",
        "command": " ".join(cmd),
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr
    }


def format_output(result: dict) -> str:
    """Format test output in a clean, readable way"""
    output_lines = []
    
    # Header
    output_lines.append("=" * 70)
    output_lines.append(f"Running tests with {result['framework']}")
    output_lines.append(f"Command: {result['command']}")
    output_lines.append("=" * 70)
    output_lines.append("")
    
    # Test output
    if result['stdout']:
        output_lines.append(result['stdout'])
    
    if result['stderr']:
        output_lines.append("\n" + result['stderr'])
    
    # Result summary
    output_lines.append("\n" + "=" * 70)
    if result['returncode'] == 0:
        output_lines.append("✓ ALL TESTS PASSED")
    else:
        output_lines.append("✗ TESTS FAILED")
    output_lines.append("=" * 70)
    
    return "\n".join(output_lines)


@registry.register(
    name="run_tests",
    description="Run tests with auto-detected framework (pytest, unittest, django, jest). Smart detection with clean output.",
    input_schema={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to project directory",
                "default": "."
            },
            "pattern": {
                "type": "string",
                "description": "Test file pattern or specific test to run (e.g., 'test_api.py', 'tests/unit/')"
            },
            "verbose": {
                "type": "boolean",
                "description": "Verbose output",
                "default": False
            },
            "coverage": {
                "type": "boolean",
                "description": "Run with coverage report (pytest/jest only)",
                "default": False
            },
            "markers": {
                "type": "string",
                "description": "Pytest markers to filter tests (e.g., 'unit', 'integration')"
            },
            "fail_fast": {
                "type": "boolean",
                "description": "Stop on first failure",
                "default": False
            },
            "parallel": {
                "type": "boolean",
                "description": "Run tests in parallel (if supported by framework)",
                "default": False
            },
            "framework": {
                "type": "string",
                "enum": ["auto", "pytest", "unittest", "django", "jest"],
                "description": "Force specific test framework (default: auto-detect)",
                "default": "auto"
            }
        }
    }
)
def run_tests(arguments: dict) -> list[TextContent]:
    """Run tests with auto-detected framework"""
    path = arguments.get("path", ".")
    pattern = arguments.get("pattern")
    verbose = arguments.get("verbose", False)
    coverage = arguments.get("coverage", False)
    markers = arguments.get("markers")
    fail_fast = arguments.get("fail_fast", False)
    parallel = arguments.get("parallel", False)
    framework = arguments.get("framework", "auto")
    
    # Validate path
    if not os.path.exists(path):
        return [TextContent(type="text", text=f"Error: Path does not exist: {path}")]
    
    try:
        # Detect framework if auto
        if framework == "auto":
            framework = detect_test_framework(path)
        
        if framework == "unknown":
            return [TextContent(
                type="text",
                text="Error: Could not detect test framework. No test files or configuration found.\n\n"
                     "Supported frameworks: pytest, unittest, Django, jest\n"
                     "Try specifying the framework explicitly with the 'framework' parameter."
            )]
        
        # Run tests based on framework
        if framework == "pytest":
            result = run_pytest(path, pattern, verbose, coverage, markers, fail_fast, parallel)
        elif framework == "unittest":
            result = run_unittest(path, pattern, verbose)
        elif framework == "django":
            result = run_django_tests(path, pattern, verbose, fail_fast, parallel)
        elif framework == "jest":
            result = run_jest(path, pattern, verbose, coverage)
        else:
            return [TextContent(type="text", text=f"Error: Unsupported framework: {framework}")]
        
        # Format and return output
        formatted_output = format_output(result)
        return [TextContent(type="text", text=formatted_output)]
    
    except subprocess.TimeoutExpired:
        return [TextContent(type="text", text="Error: Tests timed out after 5 minutes")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error running tests: {str(e)}")]
