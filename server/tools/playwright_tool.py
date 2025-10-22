# server/tools/playwright_tool.py
from typing import Optional, List
from urllib.parse import urlparse
from mcp.types import TextContent
from server.registry import registry
from server.tools.playwright_session import get_session

# Import config with fallback
try:
    from server.playwright_config import (
        PLAYWRIGHT_BLACKLIST,
        PLAYWRIGHT_WHITELIST,
        ALLOW_LOCALHOST
    )
except ImportError:
    PLAYWRIGHT_BLACKLIST = []
    PLAYWRIGHT_WHITELIST = []
    ALLOW_LOCALHOST = True


def is_safe_url(url: str, allow_domain: Optional[str] = None) -> tuple[bool, str]:
    """
    Check if URL is safe to visit based on whitelist/blacklist
    Returns: (is_safe, reason)
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        if not domain:
            return False, "Invalid URL: no domain"
        
        # Check localhost
        if ALLOW_LOCALHOST:
            localhost_domains = ["localhost", "127.0.0.1", "0.0.0.0", "[::1]"]
            if any(d in domain for d in localhost_domains):
                return True, "Localhost allowed"
        
        # Check blacklist first
        for blocked in PLAYWRIGHT_BLACKLIST:
            if blocked.lower() in domain:
                return False, f"Domain blocked: {blocked}"
        
        # Check temporary allow_domain parameter
        if allow_domain and allow_domain.lower() in domain:
            return True, f"Temporarily allowed: {allow_domain}"
        
        # Check whitelist (if not empty)
        if PLAYWRIGHT_WHITELIST:
            for allowed in PLAYWRIGHT_WHITELIST:
                if allowed.lower() in domain:
                    return True, f"Whitelisted: {allowed}"
            return False, f"Domain not in whitelist: {domain}"
        
        # If whitelist is empty, allow all (except blacklisted)
        return True, "No whitelist restrictions"
    
    except Exception as e:
        return False, f"URL validation error: {str(e)}"


def action_launch(arguments: dict) -> str:
    """Launch browser session"""
    session = get_session()
    
    headless = arguments.get("headless", True)
    browser_type = arguments.get("browser", "chromium")
    
    if browser_type not in ["chromium", "firefox", "webkit"]:
        return f"❌ Invalid browser type: {browser_type}. Use: chromium, firefox, webkit"
    
    result = session.launch(headless=headless, browser_type=browser_type)
    
    if result["success"]:
        return f"""✅ Browser launched
Session ID: {result['session_id']}
Browser: {result['browser']}
Mode: {'Headless' if result['headless'] else 'Visible'}"""
    else:
        return f"❌ Failed to launch browser: {result['error']}"


def action_navigate(arguments: dict) -> str:
    """Navigate to URL"""
    session = get_session()
    
    if not session.is_active():
        return "❌ No active session. Use action=launch first."
    
    url = arguments.get("url", "")
    if not url:
        return "❌ No URL provided"
    
    # Safety check
    allow_domain = arguments.get("allow_domain")
    is_safe, reason = is_safe_url(url, allow_domain)
    
    if not is_safe:
        return f"❌ URL blocked: {reason}\n\nTo allow this domain:\n1. Add to PLAYWRIGHT_WHITELIST in server/playwright_config.py\n2. Or use allow_domain parameter for one-time access"
    
    try:
        page = session.get_page()
        wait_until = arguments.get("wait_until", "load")
        
        if wait_until not in ["load", "domcontentloaded", "networkidle"]:
            wait_until = "load"
        
        import time
        start = time.time()
        page.goto(url, wait_until=wait_until)
        load_time = time.time() - start
        
        title = page.title()
        
        return f"""✅ Navigated to: {url}
Page title: {title}
Load time: {load_time:.2f}s
Safety: {reason}"""
    
    except Exception as e:
        return f"❌ Navigation error: {str(e)}"


def action_click(arguments: dict) -> str:
    """Click element by selector (CSS or XPath)"""
    session = get_session()

    if not session.is_active():
        return "❌ No active session. Use action=launch first."

    selector = arguments.get("selector", "")
    if not selector:
        return "❌ No selector provided"

    try:
        page = session.get_page()
        selector_type = arguments.get("selector_type", "css")

        # Determine if XPath or CSS
        if selector_type == "xpath" or selector.startswith("//") or selector.startswith("("):
            # Use XPath
            element = page.locator(f"xpath={selector}")
        else:
            # Use CSS (default)
            element = page.locator(selector)

        element.click()

        return f"✅ Clicked: {selector} ({selector_type})"

    except Exception as e:
        return f"❌ Click error: {str(e)}\n\nSelector: {selector}"


def action_fill(arguments: dict) -> str:
    """Fill input field with text (CSS or XPath)"""
    session = get_session()

    if not session.is_active():
        return "❌ No active session. Use action=launch first."

    selector = arguments.get("selector", "")
    text = arguments.get("text", "")

    if not selector:
        return "❌ No selector provided"

    if not text:
        return "❌ No text provided"

    try:
        page = session.get_page()
        selector_type = arguments.get("selector_type", "css")

        # Determine if XPath or CSS
        if selector_type == "xpath" or selector.startswith("//") or selector.startswith("("):
            element = page.locator(f"xpath={selector}")
        else:
            element = page.locator(selector)

        element.fill(text)

        return f"✅ Filled: {selector} ({selector_type})\nText: {text[:50]}{'...' if len(text) > 50 else ''}"

    except Exception as e:
        return f"❌ Fill error: {str(e)}\n\nSelector: {selector}"


def action_extract(arguments: dict) -> str:
    """Extract data from page (CSS or XPath)"""
    session = get_session()

    if not session.is_active():
        return "❌ No active session. Use action=launch first."

    selector = arguments.get("selector", "")
    if not selector:
        return "❌ No selector provided"

    try:
        page = session.get_page()
        multiple = arguments.get("multiple", False)
        attribute = arguments.get("attribute")
        selector_type = arguments.get("selector_type", "css")

        # Determine if XPath or CSS
        if selector_type == "xpath" or selector.startswith("//") or selector.startswith("("):
            locator = page.locator(f"xpath={selector}")
        else:
            locator = page.locator(selector)

        if multiple:
            # Get all matching elements
            count = locator.count()

            if count == 0:
                return f"❌ No elements found: {selector}"

            data = []
            for i in range(min(count, 100)):  # Limit to 100
                elem = locator.nth(i)
                if attribute:
                    value = elem.get_attribute(attribute)
                else:
                    value = elem.inner_text()

                if value:
                    data.append(value)

            output = []
            output.append("📊 EXTRACTED DATA")
            output.append("=" * 80)
            output.append(f"Selector: {selector} ({selector_type})")
            output.append(f"Attribute: {attribute if attribute else 'text'}")
            output.append(f"Count: {len(data)}")
            output.append("")

            for i, item in enumerate(data[:50], 1):  # Show first 50
                output.append(f"{i}. {item[:200]}{'...' if len(item) > 200 else ''}")

            if len(data) > 50:
                output.append(f"\n... and {len(data) - 50} more items")

            output.append("")
            output.append("=" * 80)

            return "\n".join(output)

        else:
            # Get single element
            if locator.count() == 0:
                return f"❌ Element not found: {selector}"

            if attribute:
                value = locator.get_attribute(attribute)
            else:
                value = locator.inner_text()

            return f"""✅ Extracted from: {selector} ({selector_type})
Attribute: {attribute if attribute else 'text'}

Data:
{value}"""

    except Exception as e:
        return f"❌ Extract error: {str(e)}\n\nSelector: {selector}"


def action_screenshot(arguments: dict) -> str:
    """Capture screenshot (CSS or XPath)"""
    session = get_session()

    if not session.is_active():
        return "❌ No active session. Use action=launch first."

    try:
        page = session.get_page()

        filename = arguments.get("filename", "screenshot.png")
        full_page = arguments.get("full_page", False)
        selector = arguments.get("selector")
        selector_type = arguments.get("selector_type", "css")

        if selector:
            # Screenshot specific element
            if selector_type == "xpath" or selector.startswith("//") or selector.startswith("("):
                locator = page.locator(f"xpath={selector}")
            else:
                locator = page.locator(selector)

            if locator.count() == 0:
                return f"❌ Element not found: {selector}"

            locator.screenshot(path=filename)
            return f"✅ Element screenshot saved: {filename}\nSelector: {selector} ({selector_type})"
        else:
            # Screenshot entire page
            page.screenshot(path=filename, full_page=full_page)
            return f"✅ Screenshot saved: {filename}\nFull page: {full_page}"

    except Exception as e:
        return f"❌ Screenshot error: {str(e)}"


def action_wait(arguments: dict) -> str:
    """Wait for element or condition (CSS or XPath)"""
    session = get_session()

    if not session.is_active():
        return "❌ No active session. Use action=launch first."

    selector = arguments.get("selector", "")
    if not selector:
        return "❌ No selector provided"

    try:
        page = session.get_page()
        timeout = arguments.get("timeout", 30000)
        selector_type = arguments.get("selector_type", "css")

        # Determine if XPath or CSS
        if selector_type == "xpath" or selector.startswith("//") or selector.startswith("("):
            locator = page.locator(f"xpath={selector}")
        else:
            locator = page.locator(selector)

        locator.wait_for(timeout=timeout)

        return f"✅ Element appeared: {selector} ({selector_type})\nTimeout: {timeout}ms"

    except Exception as e:
        return f"❌ Wait timeout: {str(e)}\n\nSelector: {selector}"


def action_cookies(arguments: dict) -> str:
    """Manage browser cookies"""
    session = get_session()

    if not session.is_active():
        return "❌ No active session. Use action=launch first."

    try:
        page = session.get_page()
        operation = arguments.get("operation", "get")

        if operation == "get":
            # Get all cookies
            cookies = page.context.cookies()
            if not cookies:
                return "🍪 No cookies found"

            output = []
            output.append("=" * 80)
            output.append("🍪 BROWSER COOKIES")
            output.append("=" * 80)
            output.append("")

            for i, cookie in enumerate(cookies, 1):
                output.append(f"{i}. {cookie['name']}")
                output.append(f"   Domain: {cookie.get('domain', 'N/A')}")
                output.append(f"   Path: {cookie.get('path', '/')}")
                output.append(f"   Value: {cookie.get('value', '')[:50]}...")
                output.append("")

            output.append(f"Total cookies: {len(cookies)}")
            output.append("=" * 80)

            return "\n".join(output)

        elif operation == "clear":
            # Clear all cookies
            page.context.clear_cookies()
            return "✅ All cookies cleared"

        elif operation == "set":
            # Set a new cookie
            name = arguments.get("name")
            value = arguments.get("value")
            domain = arguments.get("domain")

            if not name or not value:
                return "❌ Both 'name' and 'value' required for set operation"

            cookie_data = {
                "name": name,
                "value": value,
                "domain": domain or page.url.split("/")[2],
                "path": "/"
            }

            page.context.add_cookies([cookie_data])
            return f"✅ Cookie set: {name}={value}"

        elif operation == "delete":
            # Delete specific cookie
            name = arguments.get("name")
            if not name:
                return "❌ Cookie 'name' required for delete operation"

            # Get cookies, filter out the one to delete
            cookies = page.context.cookies()
            page.context.clear_cookies()

            remaining = [c for c in cookies if c['name'] != name]
            if remaining:
                page.context.add_cookies(remaining)

            return f"✅ Cookie deleted: {name}"

        else:
            return f"❌ Unknown operation: {operation}. Use: get, set, clear, delete"

    except Exception as e:
        return f"❌ Cookie error: {str(e)}"


def action_storage(arguments: dict) -> str:
    """Manage localStorage/sessionStorage"""
    session = get_session()

    if not session.is_active():
        return "❌ No active session. Use action=launch first."

    try:
        page = session.get_page()
        operation = arguments.get("operation", "get")
        storage_type = arguments.get("storage_type", "local")  # local or session

        storage_obj = f"{storage_type}Storage"

        if operation == "get":
            # Get all storage items
            js_code = f"""
            Object.keys({storage_obj}).map(key => ({{
                key: key,
                value: {storage_obj}.getItem(key)
            }}))
            """
            items = page.evaluate(js_code)

            if not items:
                return f"📦 No {storage_type}Storage items found"

            output = []
            output.append("=" * 80)
            output.append(f"📦 {storage_type.upper()}STORAGE")
            output.append("=" * 80)
            output.append("")

            for i, item in enumerate(items, 1):
                output.append(f"{i}. {item['key']}")
                output.append(f"   Value: {item['value'][:100]}...")
                output.append("")

            output.append(f"Total items: {len(items)}")
            output.append("=" * 80)

            return "\n".join(output)

        elif operation == "set":
            # Set storage item
            key = arguments.get("key")
            value = arguments.get("value")

            if not key or not value:
                return "❌ Both 'key' and 'value' required for set operation"

            js_code = f"{storage_obj}.setItem('{key}', '{value}')"
            page.evaluate(js_code)

            return f"✅ {storage_type}Storage set: {key}={value}"

        elif operation == "clear":
            # Clear all storage
            js_code = f"{storage_obj}.clear()"
            page.evaluate(js_code)

            return f"✅ All {storage_type}Storage cleared"

        elif operation == "delete":
            # Delete specific key
            key = arguments.get("key")
            if not key:
                return "❌ 'key' required for delete operation"

            js_code = f"{storage_obj}.removeItem('{key}')"
            page.evaluate(js_code)

            return f"✅ {storage_type}Storage deleted: {key}"

        else:
            return f"❌ Unknown operation: {operation}. Use: get, set, clear, delete"

    except Exception as e:
        return f"❌ Storage error: {str(e)}"


def action_close(arguments: dict) -> str:
    """Close browser session"""
    session = get_session()
    
    result = session.close()
    
    if result["success"]:
        return "✅ Browser closed\nSession cleaned up"
    else:
        return f"❌ Close error: {result['error']}"


@registry.register(
    name="playwright",
    description="Browser automation using Playwright. Launch browser, navigate URLs, click elements, fill forms, extract data, capture screenshots, manage cookies/storage. Supports CSS and XPath selectors. Perfect for web scraping, testing, and automation.",
    input_schema={
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["launch", "navigate", "click", "fill", "extract", "screenshot", "wait", "cookies", "storage", "close"],
                "description": "Action: launch (start browser), navigate (go to URL), click (element), fill (input), extract (data), screenshot (capture), wait (for element), cookies (manage), storage (localStorage/sessionStorage), close (end session)"
            },
            "headless": {
                "type": "boolean",
                "description": "For launch: run browser in headless mode (default: true)"
            },
            "browser": {
                "type": "string",
                "enum": ["chromium", "firefox", "webkit"],
                "description": "For launch: browser type (default: chromium)"
            },
            "url": {
                "type": "string",
                "description": "For navigate: URL to visit"
            },
            "wait_until": {
                "type": "string",
                "enum": ["load", "domcontentloaded", "networkidle"],
                "description": "For navigate: when to consider navigation complete (default: load)"
            },
            "allow_domain": {
                "type": "string",
                "description": "For navigate: temporarily allow this domain (one-time bypass)"
            },
            "selector": {
                "type": "string",
                "description": "CSS or XPath selector for click, fill, extract, wait, screenshot actions. Auto-detects XPath if starts with // or ("
            },
            "selector_type": {
                "type": "string",
                "enum": ["css", "xpath"],
                "description": "Selector type: css (default) or xpath. Auto-detected from selector syntax if not specified."
            },
            "text": {
                "type": "string",
                "description": "For fill: text to type in input field"
            },
            "attribute": {
                "type": "string",
                "description": "For extract: attribute to get (href, src, class, etc). Gets text if not specified."
            },
            "multiple": {
                "type": "boolean",
                "description": "For extract: get all matching elements (default: false, gets first only)"
            },
            "filename": {
                "type": "string",
                "description": "For screenshot: output filename (default: screenshot.png)"
            },
            "full_page": {
                "type": "boolean",
                "description": "For screenshot: capture full page scroll (default: false)"
            },
            "timeout": {
                "type": "integer",
                "description": "For wait: timeout in milliseconds (default: 30000)"
            },
            "operation": {
                "type": "string",
                "enum": ["get", "set", "clear", "delete"],
                "description": "For cookies/storage: operation to perform (get, set, clear, delete)"
            },
            "name": {
                "type": "string",
                "description": "For cookies set/delete: cookie name"
            },
            "value": {
                "type": "string",
                "description": "For cookies/storage set: value to set"
            },
            "domain": {
                "type": "string",
                "description": "For cookies set: cookie domain (uses current domain if not specified)"
            },
            "key": {
                "type": "string",
                "description": "For storage set/delete: storage key"
            },
            "storage_type": {
                "type": "string",
                "enum": ["local", "session"],
                "description": "For storage: localStorage (local) or sessionStorage (session). Default: local"
            }
        },
        "required": ["action"]
    }
)
def playwright(arguments: dict) -> list[TextContent]:
    """Playwright browser automation tool"""
    action = arguments.get("action", "launch")

    try:
        if action == "launch":
            result = action_launch(arguments)
        elif action == "navigate":
            result = action_navigate(arguments)
        elif action == "click":
            result = action_click(arguments)
        elif action == "fill":
            result = action_fill(arguments)
        elif action == "extract":
            result = action_extract(arguments)
        elif action == "screenshot":
            result = action_screenshot(arguments)
        elif action == "wait":
            result = action_wait(arguments)
        elif action == "cookies":
            result = action_cookies(arguments)
        elif action == "storage":
            result = action_storage(arguments)
        elif action == "close":
            result = action_close(arguments)
        else:
            result = f"❌ Unknown action: {action}"

        return [TextContent(type="text", text=result)]

    except Exception as e:
        return [TextContent(type="text", text=f"❌ Error: {str(e)}")]
