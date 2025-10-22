# server/tools/chrome_devtools.py
import logging
from typing import Dict
from mcp.types import TextContent
from server.registry import registry
from server.tools.devtools_base import DevToolsClient

# Configure logging
logger = logging.getLogger(__name__)


def action_connect(client: DevToolsClient, arguments: dict) -> str:
    """Connect to browser and list tabs"""
    try:
        tabs = client.get_tabs()
        
        output = []
        output.append("=" * 80)
        output.append("🌐 CHROME DEVTOOLS - AVAILABLE TABS")
        output.append("=" * 80)
        output.append("")
        
        for i, tab in enumerate(tabs):
            tab_type = tab.get("type", "unknown")
            if tab_type != "page":
                continue
            
            title = tab.get("title", "Untitled")[:50]
            url = tab.get("url", "")[:60]
            output.append(f"[{i}] {title}")
            output.append(f"    URL: {url}")
            output.append("")
        
        output.append(f"Total tabs: {len([t for t in tabs if t.get('type') == 'page'])}")
        output.append("=" * 80)
        
        return "\n".join(output)
    
    except Exception as e:
        return f"❌ Failed to connect: {str(e)}\n\nMake sure Opera GX is running with --remote-debugging-port=9222"


def action_console(client: DevToolsClient, arguments: dict) -> str:
    """Execute JavaScript or read console logs"""
    try:
        # Find and connect to tab
        tab = client.find_tab(
            url=arguments.get("tab_url"),
            title=arguments.get("tab_title"),
            index=arguments.get("tab_index")
        )
        
        if not tab:
            return "❌ Tab not found"
        
        client.connect_to_tab(tab)
        
        command = arguments.get("command", "")
        
        if command == "logs":
            # Enable console and get logs
            client.send_command("Console.enable")
            client.send_command("Log.enable")
            
            return "✅ Console logging enabled. Logs will be captured in real-time."
        
        elif command.startswith("exec:"):
            # Execute JavaScript
            js_code = command[5:].strip()
            result = client.send_command("Runtime.evaluate", {
                "expression": js_code,
                "returnByValue": True
            })
            
            if result.get("exceptionDetails"):
                error = result["exceptionDetails"]
                return f"❌ JavaScript Error:\n{error.get('text', 'Unknown error')}"
            
            value = result.get("result", {}).get("value")
            return f"✅ Result:\n{json.dumps(value, indent=2)}"
        
        else:
            return "❌ Invalid command. Use 'logs' or 'exec:<javascript>'"
    
    except Exception as e:
        return f"❌ Console error: {str(e)}"
    finally:
        client.close()


def action_network(client: DevToolsClient, arguments: dict) -> str:
    """Monitor network requests"""
    try:
        # Find and connect to tab
        tab = client.find_tab(
            url=arguments.get("tab_url"),
            title=arguments.get("tab_title"),
            index=arguments.get("tab_index")
        )
        
        if not tab:
            return "❌ Tab not found"
        
        client.connect_to_tab(tab)
        
        # Enable network tracking
        client.send_command("Network.enable")
        
        command = arguments.get("command", "list")
        
        if command == "clear":
            client.send_command("Network.clearBrowserCache")
            return "✅ Network cache cleared"
        
        return "✅ Network monitoring enabled. Refresh the page to see requests."
    
    except Exception as e:
        return f"❌ Network error: {str(e)}"
    finally:
        client.close()


def action_inspect(client: DevToolsClient, arguments: dict) -> str:
    """Inspect DOM elements"""
    try:
        # Find and connect to tab
        tab = client.find_tab(
            url=arguments.get("tab_url"),
            title=arguments.get("tab_title"),
            index=arguments.get("tab_index")
        )
        
        if not tab:
            return "❌ Tab not found"
        
        client.connect_to_tab(tab)
        
        selector = arguments.get("selector", "")
        if not selector:
            return "❌ No selector provided. Use selector parameter (e.g., 'div.main', '#header')"
        
        # Query selector
        result = client.send_command("Runtime.evaluate", {
            "expression": f"document.querySelector('{selector}')",
            "returnByValue": False
        })
        
        if result.get("result", {}).get("type") == "object" and result["result"].get("subtype") != "null":
            # Get element properties
            obj_id = result["result"]["objectId"]
            props = client.send_command("Runtime.getProperties", {
                "objectId": obj_id
            })
            
            output = []
            output.append(f"✅ Element found: {selector}")
            output.append("")
            output.append("Properties:")
            
            for prop in props.get("result", [])[:10]:  # Limit to 10 properties
                name = prop.get("name")
                value = prop.get("value", {})
                val_str = str(value.get("value", ""))[:50]
                output.append(f"  {name}: {val_str}")
            
            return "\n".join(output)
        else:
            return f"❌ Element not found: {selector}"
    
    except Exception as e:
        return f"❌ Inspect error: {str(e)}"
    finally:
        client.close()


def action_screenshot(client: DevToolsClient, arguments: dict) -> str:
    """Capture screenshot"""
    try:
        # Find and connect to tab
        tab = client.find_tab(
            url=arguments.get("tab_url"),
            title=arguments.get("tab_title"),
            index=arguments.get("tab_index")
        )
        
        if not tab:
            return "❌ Tab not found"
        
        client.connect_to_tab(tab)
        
        # Capture screenshot
        result = client.send_command("Page.captureScreenshot", {
            "format": "png",
            "quality": 100
        })
        
        # Save to file
        import base64
        screenshot_data = result.get("data", "")
        filename = arguments.get("filename", "screenshot.png")
        
        with open(filename, "wb") as f:
            f.write(base64.b64decode(screenshot_data))
        
        return f"✅ Screenshot saved to: {filename}"
    
    except Exception as e:
        return f"❌ Screenshot error: {str(e)}"
    finally:
        client.close()


def action_performance(client: DevToolsClient, arguments: dict) -> str:
    """Get performance metrics"""
    try:
        # Find and connect to tab
        tab = client.find_tab(
            url=arguments.get("tab_url"),
            title=arguments.get("tab_title"),
            index=arguments.get("tab_index")
        )
        
        if not tab:
            return "❌ Tab not found"
        
        client.connect_to_tab(tab)
        
        # Get performance metrics
        metrics = client.send_command("Performance.getMetrics")
        
        output = []
        output.append("📊 PERFORMANCE METRICS")
        output.append("=" * 80)
        output.append("")
        
        metric_list = metrics.get("metrics", [])
        for metric in metric_list:
            name = metric.get("name", "")
            value = metric.get("value", 0)
            
            # Format common metrics nicely
            if "Time" in name or "Duration" in name:
                output.append(f"  {name}: {value:.2f}s")
            elif "Bytes" in name or "Size" in name:
                output.append(f"  {name}: {value / 1024:.2f} KB")
            else:
                output.append(f"  {name}: {value}")
        
        output.append("")
        output.append("=" * 80)
        
        return "\n".join(output)
    
    except Exception as e:
        return f"❌ Performance error: {str(e)}"
    finally:
        client.close()


@registry.register(
    name="chrome_devtools",
    description="Debug web applications using Chrome DevTools Protocol. Connect to Opera GX/Chrome, execute JavaScript, inspect network requests, analyze DOM, capture screenshots, and monitor performance.",
    input_schema={
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["connect", "console", "network", "inspect", "screenshot", "performance"],
                "description": "Action to perform: connect (list tabs), console (execute JS/read logs), network (monitor requests), inspect (query DOM), screenshot (capture page), performance (get metrics)"
            },
            "tab_url": {
                "type": "string",
                "description": "Find tab by URL pattern (e.g., 'localhost:8000')"
            },
            "tab_title": {
                "type": "string",
                "description": "Find tab by title pattern"
            },
            "tab_index": {
                "type": "integer",
                "description": "Tab index from connect action (0-based)"
            },
            "command": {
                "type": "string",
                "description": "Specific command: 'logs' to enable console logging, 'exec:<code>' to run JavaScript, 'list' for network requests, 'clear' to clear cache"
            },
            "selector": {
                "type": "string",
                "description": "CSS selector for inspect action (e.g., 'div.main', '#header', 'button')"
            },
            "filename": {
                "type": "string",
                "description": "Filename for screenshot (default: screenshot.png)"
            }
        },
        "required": ["action"]
    }
)
def chrome_devtools(arguments: dict) -> list[TextContent]:
    """Chrome DevTools debugging tool"""
    action = arguments.get("action", "connect")

    # Create client
    client = DevToolsClient()
    
    try:
        if action == "connect":
            result = action_connect(client, arguments)
        elif action == "console":
            result = action_console(client, arguments)
        elif action == "network":
            result = action_network(client, arguments)
        elif action == "inspect":
            result = action_inspect(client, arguments)
        elif action == "screenshot":
            result = action_screenshot(client, arguments)
        elif action == "performance":
            result = action_performance(client, arguments)
        else:
            result = f"❌ Unknown action: {action}"
        
        return [TextContent(type="text", text=result)]
    
    except Exception as e:
        return [TextContent(type="text", text=f"❌ Error: {str(e)}")]
