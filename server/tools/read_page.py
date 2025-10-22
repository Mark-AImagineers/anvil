# server/tools/read_page.py
import json
import logging
from typing import Optional
from mcp.types import TextContent
from server.registry import registry
from server.tools.devtools_base import DevToolsClient

# Configure logging
logger = logging.getLogger(__name__)


class PageReader(DevToolsClient):
    """Simple page content reader using Chrome DevTools"""

    # International currency patterns
    CURRENCY_PATTERNS = {
        'USD': r'\$\s?\d+(?:,\d{3})*(?:\.\d{2})?',
        'EUR': r'€\s?\d+(?:,\d{3})*(?:[.,]\d{2})?',
        'GBP': r'£\s?\d+(?:,\d{3})*(?:\.\d{2})?',
        'JPY': r'¥\s?\d+(?:,\d{3})*',
        'CNY': r'¥\s?\d+(?:,\d{3})*(?:\.\d{2})?|CN¥\s?\d+',
        'INR': r'₹\s?\d+(?:,\d{3})*(?:\.\d{2})?',
        'KRW': r'₩\s?\d+(?:,\d{3})*',
        'RUB': r'₽\s?\d+(?:,\d{3})*(?:\.\d{2})?',
        'BRL': r'R\$\s?\d+(?:,\d{3})*(?:\.\d{2})?'
    }

    def __init__(self, host: str = "localhost", port: int = 9222):
        super().__init__(host, port)


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

        # Enhanced JavaScript to extract clean content with readability
        js_code = """
        (function() {
            // Remove scripts, styles, nav, footer, ads
            const excludeSelectors = 'script, style, nav, footer, .ad, .advertisement, .sidebar, .menu, .header, [class*="nav"], [class*="sidebar"], [id*="sidebar"]';
            const clone = document.cloneNode(true);
            const exclude = clone.querySelectorAll(excludeSelectors);
            exclude.forEach(el => el.remove());

            // Try multiple main content selectors (priority order)
            const selectors = [
                'main',
                'article',
                '[role="main"]',
                '.main-content',
                '.post-content',
                '.entry-content',
                '.article-content',
                '.content',
                '#content',
                '.post',
                'body'
            ];

            let main = null;
            for (const selector of selectors) {
                main = clone.querySelector(selector);
                if (main && main.innerText && main.innerText.length > 100) {
                    break;
                }
            }

            if (!main) main = clone.body;

            // Extract text
            const text = main.innerText || main.textContent;

            // Clean up whitespace
            return text
                .replace(/\\n\\s*\\n\\s*\\n+/g, '\\n\\n')  // Multiple newlines to double
                .replace(/[ \\t]+/g, ' ')  // Multiple spaces to single
                .trim();
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
        logger.error(f"Error reading page: {e}")
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
            # Use improved multi-currency regex
            js_code = """
            const text = document.body.innerText;
            // International currency patterns
            const currencyRegex = /[$€£¥₹₩₽]\s?\d+(?:,\d{3})*(?:[.,]\d{2})?|R\$\s?\d+(?:,\d{3})*(?:\.\d{2})?|CN¥\s?\d+/g;
            const prices = text.match(currencyRegex) || [];
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
