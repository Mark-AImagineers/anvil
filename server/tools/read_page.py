# server/tools/read_page.py
import json
import requests
import websocket
from typing import Optional
from mcp.types import TextContent
from server.registry import registry


class PageReader:
    """Simple page content reader using Chrome DevTools"""
    
    def __init__(self, host: str = "localhost", port: int = 9222):
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self.ws = None
        self.message_id = 0
    
    def get_tabs(self):
        """Get list of all open tabs"""
        try:
            response = requests.get(f"{self.base_url}/json", timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise Exception(f"Failed to get tabs: {str(e)}")
    
    def find_tab(self, url: Optional[str] = None, title: Optional[str] = None, index: Optional[int] = None):
        """Find tab by URL pattern, title, or index"""
        tabs = self.get_tabs()
        
        if index is not None:
            if 0 <= index < len(tabs):
                return tabs[index]
            return None
        
        if url:
            for tab in tabs:
                if url.lower() in tab.get("url", "").lower():
                    return tab
        
        if title:
            for tab in tabs:
                if title.lower() in tab.get("title", "").lower():
                    return tab
        
        return tabs[0] if tabs else None
    
    def connect_to_tab(self, tab):
        """Connect WebSocket to specific tab"""
        ws_url = tab.get("webSocketDebuggerUrl")
        if not ws_url:
            raise Exception("Tab does not have WebSocket URL")
        
        self.ws = websocket.create_connection(ws_url)
    
    def send_command(self, method: str, params: Optional[dict] = None):
        """Send command to Chrome DevTools"""
        if not self.ws:
            raise Exception("Not connected to any tab")
        
        self.message_id += 1
        message = {
            "id": self.message_id,
            "method": method,
            "params": params or {}
        }
        
        self.ws.send(json.dumps(message))
        
        while True:
            response = json.loads(self.ws.recv())
            if response.get("id") == self.message_id:
                if "error" in response:
                    raise Exception(f"DevTools error: {response['error']}")
                return response.get("result", {})
    
    def execute_js(self, code: str):
        """Execute JavaScript and return result"""
        result = self.send_command("Runtime.evaluate", {
            "expression": code,
            "returnByValue": True
        })
        
        if result.get("exceptionDetails"):
            error = result["exceptionDetails"]
            raise Exception(f"JavaScript error: {error.get('text', 'Unknown error')}")
        
        return result.get("result", {}).get("value")
    
    def close(self):
        """Close WebSocket connection"""
        if self.ws:
            self.ws.close()
            self.ws = None


def action_read(reader: PageReader, arguments: dict) -> str:
    """Read clean text content from page"""
    try:
        tab = reader.find_tab(
            url=arguments.get("url"),
            title=arguments.get("title"),
            index=arguments.get("tab_index")
        )
        
        if not tab:
            return "❌ Tab not found. Use chrome_devtools connect action to see available tabs."
        
        reader.connect_to_tab(tab)
        
        # JavaScript to extract clean content
        js_code = """
        (function() {
            // Remove scripts, styles, nav, footer, ads
            const excludeSelectors = 'script, style, nav, footer, .ad, .advertisement, .sidebar, .menu, .header';
            const exclude = document.querySelectorAll(excludeSelectors);
            exclude.forEach(el => el.remove());
            
            // Get main content
            const main = document.querySelector('main, article, .content, .post, [role="main"]') || document.body;
            
            // Extract text
            const text = main.innerText || main.textContent;
            
            // Clean up whitespace
            return text.replace(/\\n\\s*\\n\\s*\\n/g, '\\n\\n').trim();
        })();
        """
        
        content = reader.execute_js(js_code)
        
        page_title = tab.get("title", "Untitled")
        page_url = tab.get("url", "")
        
        output = []
        output.append("=" * 80)
        output.append(f"📄 {page_title}")
        output.append("=" * 80)
        output.append(f"URL: {page_url}")
        output.append("")
        output.append(content)
        output.append("")
        output.append("=" * 80)
        
        return "\n".join(output)
    
    except Exception as e:
        return f"❌ Error reading page: {str(e)}"
    finally:
        reader.close()


def action_markdown(reader: PageReader, arguments: dict) -> str:
    """Convert page to markdown"""
    try:
        tab = reader.find_tab(
            url=arguments.get("url"),
            title=arguments.get("title"),
            index=arguments.get("tab_index")
        )
        
        if not tab:
            return "❌ Tab not found"
        
        reader.connect_to_tab(tab)
        
        # JavaScript to convert to markdown
        js_code = """
        (function() {
            let markdown = '';
            
            // Title
            const title = document.querySelector('h1, .title, [role="heading"]');
            if (title) {
                markdown += '# ' + title.innerText + '\\n\\n';
            }
            
            // Process content
            const main = document.querySelector('main, article, .content, [role="main"]') || document.body;
            
            const process = (element) => {
                if (!element || element.nodeType !== 1) return;
                
                const tag = element.tagName.toLowerCase();
                
                if (tag === 'h1') markdown += '# ' + element.innerText + '\\n\\n';
                else if (tag === 'h2') markdown += '## ' + element.innerText + '\\n\\n';
                else if (tag === 'h3') markdown += '### ' + element.innerText + '\\n\\n';
                else if (tag === 'h4') markdown += '#### ' + element.innerText + '\\n\\n';
                else if (tag === 'p') markdown += element.innerText + '\\n\\n';
                else if (tag === 'a') markdown += '[' + element.innerText + '](' + element.href + ')';
                else if (tag === 'li') markdown += '- ' + element.innerText + '\\n';
                else if (tag === 'code' || tag === 'pre') markdown += '`' + element.innerText + '`\\n\\n';
                else if (tag === 'strong' || tag === 'b') markdown += '**' + element.innerText + '**';
                else if (tag === 'em' || tag === 'i') markdown += '*' + element.innerText + '*';
                else {
                    Array.from(element.childNodes).forEach(child => {
                        if (child.nodeType === 3) markdown += child.textContent;
                        else if (child.nodeType === 1) process(child);
                    });
                }
            };
            
            Array.from(main.children).forEach(process);
            
            return markdown.replace(/\\n\\s*\\n\\s*\\n/g, '\\n\\n').trim();
        })();
        """
        
        markdown = reader.execute_js(js_code)
        
        page_title = tab.get("title", "Untitled")
        page_url = tab.get("url", "")
        
        output = []
        output.append(f"# {page_title}\n")
        output.append(f"Source: {page_url}\n")
        output.append("---\n")
        output.append(markdown)
        
        return "\n".join(output)
    
    except Exception as e:
        return f"❌ Error converting to markdown: {str(e)}"
    finally:
        reader.close()


def action_extract(reader: PageReader, arguments: dict) -> str:
    """Extract specific data types from page"""
    try:
        tab = reader.find_tab(
            url=arguments.get("url"),
            title=arguments.get("title"),
            index=arguments.get("tab_index")
        )
        
        if not tab:
            return "❌ Tab not found"
        
        reader.connect_to_tab(tab)
        
        data_type = arguments.get("data_type", "links")
        
        js_code = ""
        
        if data_type == "links":
            js_code = """
            Array.from(document.querySelectorAll('a[href]'))
                .map(a => ({ text: a.innerText.trim(), url: a.href }))
                .filter(link => link.text && link.url)
                .slice(0, 100);
            """
        
        elif data_type == "images":
            js_code = """
            Array.from(document.querySelectorAll('img[src]'))
                .map(img => ({ alt: img.alt, src: img.src, width: img.width, height: img.height }))
                .slice(0, 50);
            """
        
        elif data_type == "emails":
            js_code = """
            const text = document.body.innerText;
            const emailRegex = /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}/g;
            const emails = text.match(emailRegex) || [];
            [...new Set(emails)];
            """
        
        elif data_type == "prices":
            js_code = """
            const text = document.body.innerText;
            const priceRegex = /\\$\\s?\\d+(?:,\\d{3})*(?:\\.\\d{2})?/g;
            const prices = text.match(priceRegex) || [];
            [...new Set(prices)];
            """
        
        elif data_type == "tables":
            js_code = """
            Array.from(document.querySelectorAll('table')).slice(0, 5).map(table => {
                const headers = Array.from(table.querySelectorAll('th')).map(th => th.innerText.trim());
                const rows = Array.from(table.querySelectorAll('tr')).slice(1).map(tr => 
                    Array.from(tr.querySelectorAll('td')).map(td => td.innerText.trim())
                );
                return { headers, rows: rows.slice(0, 10) };
            });
            """
        
        else:
            return f"❌ Unknown data type: {data_type}. Use: links, images, emails, prices, tables"
        
        data = reader.execute_js(js_code)
        
        output = []
        output.append(f"📊 EXTRACTED {data_type.upper()}")
        output.append("=" * 80)
        output.append(f"From: {tab.get('title', 'Untitled')}")
        output.append(f"URL: {tab.get('url', '')}")
        output.append("")
        output.append(json.dumps(data, indent=2))
        output.append("")
        output.append(f"Total items: {len(data) if isinstance(data, list) else 'N/A'}")
        output.append("=" * 80)
        
        return "\n".join(output)
    
    except Exception as e:
        return f"❌ Error extracting data: {str(e)}"
    finally:
        reader.close()


@registry.register(
    name="read_page",
    description="Read and extract content from web pages open in your browser. Simple interface for getting clean text, markdown, or specific data (links, images, emails, prices, tables) from any tab.",
    input_schema={
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["read", "markdown", "extract"],
                "description": "Action: read (clean text), markdown (convert to MD), extract (pull specific data)"
            },
            "url": {
                "type": "string",
                "description": "Find tab by URL pattern (e.g., 'github.com', 'localhost:8000')"
            },
            "title": {
                "type": "string",
                "description": "Find tab by title pattern"
            },
            "tab_index": {
                "type": "integer",
                "description": "Tab index (0-based, from chrome_devtools connect)"
            },
            "data_type": {
                "type": "string",
                "enum": ["links", "images", "emails", "prices", "tables"],
                "description": "For extract action: type of data to extract"
            }
        },
        "required": ["action"]
    }
)
def read_page(arguments: dict) -> list[TextContent]:
    """Read page content tool"""
    action = arguments.get("action", "read")
    reader = PageReader()
    
    try:
        if action == "read":
            result = action_read(reader, arguments)
        elif action == "markdown":
            result = action_markdown(reader, arguments)
        elif action == "extract":
            result = action_extract(reader, arguments)
        else:
            result = f"❌ Unknown action: {action}"
        
        return [TextContent(type="text", text=result)]
    
    except Exception as e:
        return [TextContent(type="text", text=f"❌ Error: {str(e)}")]
