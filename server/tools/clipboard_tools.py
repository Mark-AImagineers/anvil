# server/tools/clipboard_tools.py
import os
import json
import subprocess
import csv
import io
import logging
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path
from mcp.types import TextContent
from server.registry import registry

# Configure logging
logger = logging.getLogger(__name__)


CLIPBOARD_HISTORY_FILE = Path.home() / ".anvil_clipboard_history.json"
SNIPPETS_FILE = Path.home() / ".anvil_snippets.json"


def get_clipboard() -> str:
    """Get current clipboard content (cross-platform)"""
    try:
        # Try xclip (Linux)
        result = subprocess.run(
            ["xclip", "-selection", "clipboard", "-o"],
            capture_output=True,
            text=True,
            timeout=2
        )
        if result.returncode == 0:
            return result.stdout
    except:
        pass
    
    try:
        # Try wl-paste (Wayland)
        result = subprocess.run(
            ["wl-paste"],
            capture_output=True,
            text=True,
            timeout=2
        )
        if result.returncode == 0:
            return result.stdout
    except:
        pass
    
    try:
        # Try PowerShell (Windows via WSL)
        result = subprocess.run(
            ["powershell.exe", "-command", "Get-Clipboard"],
            capture_output=True,
            text=True,
            timeout=2
        )
        if result.returncode == 0:
            return result.stdout
    except:
        pass
    
    raise Exception("Could not access clipboard. Install xclip (Linux) or use WSL with PowerShell (Windows)")


def set_clipboard(content: str) -> bool:
    """Set clipboard content (cross-platform)"""
    try:
        # Try xclip (Linux)
        result = subprocess.run(
            ["xclip", "-selection", "clipboard"],
            input=content.encode(),
            timeout=2,
            capture_output=True
        )
        if result.returncode == 0:
            return True
    except Exception as e:
        logger.debug(f"xclip failed: {e}")

    try:
        # Try wl-copy (Wayland)
        result = subprocess.run(
            ["wl-copy"],
            input=content.encode(),
            timeout=2,
            capture_output=True
        )
        if result.returncode == 0:
            return True
    except Exception as e:
        logger.debug(f"wl-copy failed: {e}")

    try:
        # Try PowerShell (Windows via WSL) - FIXED: No command injection
        # Use stdin instead of command-line argument to avoid injection
        result = subprocess.run(
            ["powershell.exe", "-Command", "Set-Clipboard -Value $input"],
            input=content.encode('utf-16le'),  # PowerShell expects UTF-16LE
            timeout=2,
            capture_output=True
        )
        if result.returncode == 0:
            return True
    except Exception as e:
        logger.debug(f"PowerShell clipboard failed: {e}")

    return False


def load_clipboard_history() -> List[Dict]:
    """Load clipboard history from file"""
    if CLIPBOARD_HISTORY_FILE.exists():
        try:
            with open(CLIPBOARD_HISTORY_FILE, "r") as f:
                return json.load(f)
        except:
            return []
    return []


def save_clipboard_history(history: List[Dict]) -> None:
    """Save clipboard history to file"""
    try:
        with open(CLIPBOARD_HISTORY_FILE, "w") as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        print(f"Error saving clipboard history: {e}")


def load_snippets() -> Dict:
    """Load snippets from file"""
    if SNIPPETS_FILE.exists():
        try:
            with open(SNIPPETS_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_snippets(snippets: Dict) -> None:
    """Save snippets to file"""
    try:
        with open(SNIPPETS_FILE, "w") as f:
            json.dump(snippets, f, indent=2)
    except Exception as e:
        print(f"Error saving snippets: {e}")


def action_capture(arguments: dict) -> str:
    """Capture current clipboard and save to history"""
    try:
        content = get_clipboard()
        
        if not content.strip():
            return "❌ Clipboard is empty"
        
        # Load history
        history = load_clipboard_history()
        
        # Add to history (avoid duplicates)
        if not history or history[0].get("content") != content:
            entry = {
                "content": content,
                "timestamp": datetime.now().isoformat(),
                "preview": content[:100] + "..." if len(content) > 100 else content
            }
            history.insert(0, entry)
            
            # Keep last 100 entries
            history = history[:100]
            
            save_clipboard_history(history)
        
        return f"✅ Clipboard captured\nPreview: {content[:200]}{'...' if len(content) > 200 else ''}\n\nTotal history items: {len(history)}"
    
    except Exception as e:
        return f"❌ Error capturing clipboard: {str(e)}"


def action_history(arguments: dict) -> str:
    """Show clipboard history"""
    try:
        history = load_clipboard_history()
        
        if not history:
            return "📋 Clipboard history is empty. Use 'capture' action to start tracking."
        
        limit = arguments.get("limit", 10)
        
        output = []
        output.append("=" * 80)
        output.append("📋 CLIPBOARD HISTORY")
        output.append("=" * 80)
        output.append("")
        
        for i, entry in enumerate(history[:limit], 1):
            timestamp = entry.get("timestamp", "Unknown")
            preview = entry.get("preview", "")
            
            output.append(f"[{i}] {timestamp}")
            output.append(f"    {preview}")
            output.append("")
        
        output.append(f"Showing {min(limit, len(history))} of {len(history)} items")
        output.append("=" * 80)
        
        return "\n".join(output)
    
    except Exception as e:
        return f"❌ Error loading history: {str(e)}"


def action_transform(arguments: dict) -> str:
    """Transform clipboard content between formats"""
    try:
        content = get_clipboard()
        
        if not content.strip():
            return "❌ Clipboard is empty"
        
        transform_type = arguments.get("transform_type", "")
        
        if not transform_type:
            return "❌ No transform_type specified. Use: json_to_csv, csv_to_json, code_to_markdown, markdown_to_html, base64_encode, base64_decode"
        
        result = ""
        
        if transform_type == "json_to_csv":
            data = json.loads(content)
            if isinstance(data, list) and data:
                # Use proper CSV writer
                output = io.StringIO()
                keys = list(data[0].keys())
                writer = csv.DictWriter(output, fieldnames=keys)
                writer.writeheader()
                writer.writerows(data)
                result = output.getvalue()
            else:
                return "❌ Content is not a JSON array"

        elif transform_type == "csv_to_json":
            # Use proper CSV reader
            try:
                csv_file = io.StringIO(content)
                reader = csv.DictReader(csv_file)
                data = list(reader)
                result = json.dumps(data, indent=2)
            except csv.Error as e:
                return f"❌ Invalid CSV format: {str(e)}"
        
        elif transform_type == "code_to_markdown":
            # Detect language (simple heuristic)
            language = arguments.get("language", "python")
            result = f"```{language}\n{content}\n```"
        
        elif transform_type == "markdown_to_html":
            # Simple markdown to HTML (basic support)
            import re
            result = content
            result = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', result, flags=re.MULTILINE)
            result = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', result, flags=re.MULTILINE)
            result = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', result, flags=re.MULTILINE)
            result = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', result)
            result = re.sub(r'\*(.*?)\*', r'<em>\1</em>', result)
            result = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2">\1</a>', result)
        
        elif transform_type == "base64_encode":
            import base64
            result = base64.b64encode(content.encode()).decode()
        
        elif transform_type == "base64_decode":
            import base64
            result = base64.b64decode(content.encode()).decode()
        
        else:
            return f"❌ Unknown transform type: {transform_type}"
        
        # Set clipboard with result
        if set_clipboard(result):
            return f"✅ Transformed: {transform_type}\n\nResult (copied to clipboard):\n{result[:500]}{'...' if len(result) > 500 else ''}"
        else:
            return f"✅ Transformed: {transform_type}\n\nResult:\n{result[:500]}{'...' if len(result) > 500 else ''}\n\n⚠️  Could not copy to clipboard"
    
    except Exception as e:
        return f"❌ Error transforming content: {str(e)}"


def action_snippet(arguments: dict) -> str:
    """Save or retrieve reusable snippets"""
    try:
        operation = arguments.get("operation", "list")
        
        snippets = load_snippets()
        
        if operation == "save":
            name = arguments.get("name", "")
            if not name:
                return "❌ No name provided. Use 'name' parameter."
            
            content = arguments.get("content", "")
            if not content:
                # Get from clipboard
                content = get_clipboard()
            
            if not content.strip():
                return "❌ No content to save"
            
            tags = arguments.get("tags", [])
            
            snippets[name] = {
                "content": content,
                "tags": tags,
                "created": datetime.now().isoformat(),
                "preview": content[:100] + "..." if len(content) > 100 else content
            }
            
            save_snippets(snippets)
            return f"✅ Snippet '{name}' saved\nTags: {', '.join(tags) if tags else 'none'}"
        
        elif operation == "get":
            name = arguments.get("name", "")
            if not name:
                return "❌ No name provided"
            
            if name not in snippets:
                return f"❌ Snippet '{name}' not found"
            
            snippet = snippets[name]
            content = snippet["content"]
            
            # Copy to clipboard
            set_clipboard(content)
            
            return f"✅ Retrieved snippet '{name}'\n\nContent (copied to clipboard):\n{content}"
        
        elif operation == "list":
            if not snippets:
                return "📝 No snippets saved. Use operation='save' to create snippets."
            
            tag_filter = arguments.get("tag", "")
            
            output = []
            output.append("=" * 80)
            output.append("📝 SAVED SNIPPETS")
            output.append("=" * 80)
            output.append("")
            
            for name, snippet in snippets.items():
                tags = snippet.get("tags", [])
                
                if tag_filter and tag_filter not in tags:
                    continue
                
                preview = snippet.get("preview", "")
                created = snippet.get("created", "Unknown")
                
                output.append(f"• {name}")
                output.append(f"  Tags: {', '.join(tags) if tags else 'none'}")
                output.append(f"  Created: {created}")
                output.append(f"  Preview: {preview}")
                output.append("")
            
            output.append(f"Total snippets: {len(snippets)}")
            output.append("=" * 80)
            
            return "\n".join(output)
        
        elif operation == "delete":
            name = arguments.get("name", "")
            if not name:
                return "❌ No name provided"
            
            if name not in snippets:
                return f"❌ Snippet '{name}' not found"
            
            del snippets[name]
            save_snippets(snippets)
            
            return f"✅ Snippet '{name}' deleted"
        
        else:
            return f"❌ Unknown operation: {operation}. Use: save, get, list, delete"
    
    except Exception as e:
        return f"❌ Error with snippet: {str(e)}"


@registry.register(
    name="clipboard_tools",
    description="Cross-context data handling via clipboard. Capture clipboard history, transform between formats (JSON/CSV/Markdown/Base64), and save reusable snippets with tags. Bridge gaps between browser, terminal, and files.",
    input_schema={
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["capture", "history", "transform", "snippet"],
                "description": "Action: capture (save current clipboard), history (show past clips), transform (convert formats), snippet (save/get reusable snippets)"
            },
            "limit": {
                "type": "integer",
                "description": "For history: number of items to show (default: 10)"
            },
            "transform_type": {
                "type": "string",
                "enum": ["json_to_csv", "csv_to_json", "code_to_markdown", "markdown_to_html", "base64_encode", "base64_decode"],
                "description": "For transform: conversion type"
            },
            "language": {
                "type": "string",
                "description": "For code_to_markdown: programming language (default: python)"
            },
            "operation": {
                "type": "string",
                "enum": ["save", "get", "list", "delete"],
                "description": "For snippet: operation to perform"
            },
            "name": {
                "type": "string",
                "description": "For snippet: name of the snippet"
            },
            "content": {
                "type": "string",
                "description": "For snippet save: content to save (uses clipboard if empty)"
            },
            "tags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "For snippet save: tags for organization"
            },
            "tag": {
                "type": "string",
                "description": "For snippet list: filter by tag"
            }
        },
        "required": ["action"]
    }
)
def clipboard_tools(arguments: dict) -> list[TextContent]:
    """Clipboard and snippet management tool"""
    action = arguments.get("action", "capture")
    
    try:
        if action == "capture":
            result = action_capture(arguments)
        elif action == "history":
            result = action_history(arguments)
        elif action == "transform":
            result = action_transform(arguments)
        elif action == "snippet":
            result = action_snippet(arguments)
        else:
            result = f"❌ Unknown action: {action}"
        
        return [TextContent(type="text", text=result)]
    
    except Exception as e:
        return [TextContent(type="text", text=f"❌ Error: {str(e)}")]
