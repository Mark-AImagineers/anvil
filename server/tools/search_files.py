# server/tools/search_files.py
import os
import re
import fnmatch
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from mcp.types import TextContent
from server.registry import registry


def is_binary_file(filepath: str) -> bool:
    """Check if a file is binary by reading the first 8KB"""
    try:
        with open(filepath, 'rb') as f:
            chunk = f.read(8192)
            # Check for null bytes which indicate binary
            if b'\x00' in chunk:
                return True
            # Try to decode as text
            try:
                chunk.decode('utf-8')
                return False
            except UnicodeDecodeError:
                return True
    except Exception:
        return True


def parse_gitignore(directory: str) -> Optional[List[str]]:
    """Parse .gitignore file and return patterns"""
    gitignore_path = os.path.join(directory, '.gitignore')
    if not os.path.exists(gitignore_path):
        return None
    
    try:
        with open(gitignore_path, 'r', encoding='utf-8') as f:
            patterns = []
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if line and not line.startswith('#'):
                    patterns.append(line)
            return patterns
    except Exception:
        return None


def should_ignore(path: str, gitignore_patterns: List[str]) -> bool:
    """Check if path matches any gitignore pattern"""
    if not gitignore_patterns:
        return False
    
    # Get relative path components
    path_parts = Path(path).parts
    
    for pattern in gitignore_patterns:
        # Handle directory patterns
        if pattern.endswith('/'):
            pattern = pattern.rstrip('/')
            for part in path_parts:
                if fnmatch.fnmatch(part, pattern):
                    return True
        # Handle file patterns
        elif fnmatch.fnmatch(os.path.basename(path), pattern):
            return True
        # Handle full path patterns
        elif fnmatch.fnmatch(path, pattern):
            return True
    
    return False


def matches_extension(filepath: str, extensions: List[str]) -> bool:
    """Check if file matches any of the extensions"""
    if "*" in extensions or ["*"] == extensions:
        return True
    
    file_ext = os.path.splitext(filepath)[1]
    return file_ext in extensions


def search_content_in_file(filepath: str, search_text: str, case_sensitive: bool, max_size_mb: int) -> List[Dict]:
    """Search for content in a file and return matches with line numbers"""
    matches = []
    
    try:
        # Check file size
        file_size = os.path.getsize(filepath)
        if file_size > max_size_mb * 1024 * 1024:
            return []
        
        # Skip binary files
        if is_binary_file(filepath):
            return []
        
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, start=1):
                # Search for pattern
                if case_sensitive:
                    if search_text in line:
                        column = line.find(search_text)
                        matches.append({
                            "line_number": line_num,
                            "line_content": line.rstrip('\n'),
                            "column": column
                        })
                else:
                    if search_text.lower() in line.lower():
                        column = line.lower().find(search_text.lower())
                        matches.append({
                            "line_number": line_num,
                            "line_content": line.rstrip('\n'),
                            "column": column
                        })
    except Exception:
        pass
    
    return matches


@registry.register(
    name="search_files",
    description="Search for files by name pattern and/or content. Supports filename wildcards, content search, and various filters.",
    input_schema={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Root directory to search from",
                "default": "."
            },
            "pattern": {
                "type": "string",
                "description": "Filename pattern to match (e.g., '*.py', 'test_*'). Optional."
            },
            "content": {
                "type": "string",
                "description": "Text to search for within files. Optional."
            },
            "case_sensitive": {
                "type": "boolean",
                "description": "Whether content search should be case-sensitive",
                "default": False
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of results to return",
                "default": 100
            },
            "include_hidden": {
                "type": "boolean",
                "description": "Include hidden files and directories",
                "default": False
            },
            "respect_gitignore": {
                "type": "boolean",
                "description": "Respect .gitignore patterns",
                "default": True
            },
            "file_extensions": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Filter by file extensions (e.g., ['.py', '.js']). Use ['*'] for all files.",
                "default": ["*"]
            },
            "max_depth": {
                "type": "integer",
                "description": "Maximum directory depth to search. None for unlimited."
            },
            "max_file_size_mb": {
                "type": "integer",
                "description": "Maximum file size in MB for content search",
                "default": 10
            }
        },
        "required": ["path"]
    }
)
def search_files(arguments: dict) -> list[TextContent]:
    """Search for files by pattern and/or content"""
    start_time = time.time()
    
    # Parse arguments
    root_path = arguments.get("path", ".")
    pattern = arguments.get("pattern")
    content = arguments.get("content")
    case_sensitive = arguments.get("case_sensitive", False)
    max_results = arguments.get("max_results", 100)
    include_hidden = arguments.get("include_hidden", False)
    respect_gitignore = arguments.get("respect_gitignore", True)
    file_extensions = arguments.get("file_extensions", ["*"])
    max_depth = arguments.get("max_depth")
    max_file_size_mb = arguments.get("max_file_size_mb", 10)
    
    # Validate path
    if not os.path.exists(root_path):
        return [TextContent(type="text", text=f"Error: Path does not exist: {root_path}")]
    
    # Load gitignore patterns
    gitignore_patterns = []
    if respect_gitignore:
        patterns = parse_gitignore(root_path)
        if patterns:
            gitignore_patterns = patterns
    
    results = []
    total_files_searched = 0
    total_matches = 0
    
    try:
        # Walk directory tree
        for dirpath, dirnames, filenames in os.walk(root_path):
            # Calculate current depth
            depth = dirpath[len(root_path):].count(os.sep)
            if max_depth is not None and depth >= max_depth:
                dirnames.clear()  # Don't recurse deeper
                continue
            
            # Filter out hidden directories
            if not include_hidden:
                dirnames[:] = [d for d in dirnames if not d.startswith('.')]
            
            # Filter by gitignore
            if respect_gitignore and gitignore_patterns:
                dirnames[:] = [d for d in dirnames if not should_ignore(os.path.join(dirpath, d), gitignore_patterns)]
            
            for filename in filenames:
                # Stop if we've hit max results
                if len(results) >= max_results:
                    break
                
                # Skip hidden files
                if not include_hidden and filename.startswith('.'):
                    continue
                
                filepath = os.path.join(dirpath, filename)
                
                # Filter by gitignore
                if respect_gitignore and gitignore_patterns and should_ignore(filepath, gitignore_patterns):
                    continue
                
                # Filter by extension
                if not matches_extension(filename, file_extensions):
                    continue
                
                # Filter by filename pattern
                if pattern and not fnmatch.fnmatch(filename, pattern):
                    continue
                
                total_files_searched += 1
                
                # If content search is requested
                matches = []
                if content:
                    matches = search_content_in_file(filepath, content, case_sensitive, max_file_size_mb)
                    if not matches:
                        continue  # Skip files with no content matches
                
                # Add result
                result = {
                    "path": filepath,
                    "size_bytes": os.path.getsize(filepath)
                }
                
                if matches:
                    result["matches"] = matches
                    total_matches += len(matches)
                
                results.append(result)
            
            # Break outer loop if max results reached
            if len(results) >= max_results:
                break
        
        # If no content search, count results as matches
        if not content:
            total_matches = len(results)
        
        search_time = time.time() - start_time
        
        # Format output
        output = {
            "results": results,
            "total_files_searched": total_files_searched,
            "total_matches": total_matches,
            "search_time_seconds": round(search_time, 3)
        }
        
        import json
        return [TextContent(type="text", text=json.dumps(output, indent=2))]
    
    except Exception as e:
        return [TextContent(type="text", text=f"Error during search: {str(e)}")]
