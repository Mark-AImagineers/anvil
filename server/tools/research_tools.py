# server/tools/research_tools.py
import json
import requests
import websocket
import time
import logging
from typing import List, Dict, Optional
from mcp.types import TextContent
from server.registry import registry

# Configure logging
logger = logging.getLogger(__name__)


class ResearchHelper:
    """Helper for multi-source research using browser tabs"""

    # Cache timeout in seconds (5 minutes)
    CACHE_TIMEOUT = 300

    def __init__(self, host: str = "localhost", port: int = 9222):
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self._content_cache: Dict[str, Dict] = {}  # Cache tab content by URL
        self._cache_timestamps: Dict[str, float] = {}  # Track cache age
    
    def get_tabs(self) -> List[Dict]:
        """Get list of all open tabs"""
        try:
            response = requests.get(f"{self.base_url}/json", timeout=5)
            response.raise_for_status()
            return [t for t in response.json() if t.get("type") == "page"]
        except Exception as e:
            raise Exception(f"Failed to get tabs: {str(e)}")
    
    def get_tab_content(self, tab: Dict) -> Dict:
        """Get content from a specific tab (with caching)"""
        tab_url = tab.get("url", "")

        # Check cache first
        if tab_url in self._content_cache:
            cache_age = time.time() - self._cache_timestamps.get(tab_url, 0)
            if cache_age < self.CACHE_TIMEOUT:
                logger.debug(f"Using cached content for {tab_url} (age: {cache_age:.1f}s)")
                return self._content_cache[tab_url]

        ws_url = tab.get("webSocketDebuggerUrl")
        if not ws_url:
            return {"error": "No WebSocket URL"}

        try:
            ws = websocket.create_connection(ws_url, timeout=5)

            # Execute JavaScript to get content
            message = {
                "id": 1,
                "method": "Runtime.evaluate",
                "params": {
                    "expression": """
                    (function() {
                        const main = document.querySelector('main, article, .content, [role="main"]') || document.body;
                        return {
                            title: document.title,
                            url: window.location.href,
                            text: main.innerText || main.textContent,
                            links: Array.from(document.querySelectorAll('a[href]')).slice(0, 20).map(a => ({
                                text: a.innerText.trim(),
                                url: a.href
                            }))
                        };
                    })();
                    """,
                    "returnByValue": True
                }
            }

            ws.send(json.dumps(message))
            response = json.loads(ws.recv())
            ws.close()

            if "error" in response:
                return {"error": str(response["error"])}

            content = response.get("result", {}).get("value", {})

            # Cache the content
            if tab_url and "error" not in content:
                self._content_cache[tab_url] = content
                self._cache_timestamps[tab_url] = time.time()
                logger.debug(f"Cached content for {tab_url}")

            return content

        except Exception as e:
            logger.error(f"Error fetching tab content: {e}")
            return {"error": str(e)}
    
    def find_tabs_by_pattern(self, patterns: List[str]) -> List[Dict]:
        """Find tabs matching URL or title patterns"""
        tabs = self.get_tabs()
        matched = []
        
        for pattern in patterns:
            pattern_lower = pattern.lower()
            for tab in tabs:
                url = tab.get("url", "").lower()
                title = tab.get("title", "").lower()
                
                if pattern_lower in url or pattern_lower in title:
                    if tab not in matched:
                        matched.append(tab)
        
        return matched


def action_compare(helper: ResearchHelper, arguments: dict) -> str:
    """Compare information from multiple tabs"""
    try:
        patterns = arguments.get("patterns", [])
        if not patterns:
            # Get all tabs if no patterns specified
            tabs = helper.get_tabs()[:5]  # Limit to 5 tabs
        else:
            tabs = helper.find_tabs_by_pattern(patterns)
        
        if not tabs:
            return "❌ No tabs found matching patterns"
        
        output = []
        output.append("=" * 80)
        output.append("🔍 COMPARING SOURCES")
        output.append("=" * 80)
        output.append("")
        
        sources = []
        for i, tab in enumerate(tabs[:5], 1):  # Limit to 5
            content = helper.get_tab_content(tab)
            
            if "error" in content:
                continue
            
            sources.append(content)
            
            output.append(f"📄 SOURCE {i}: {content.get('title', 'Untitled')}")
            output.append(f"   URL: {content.get('url', '')}")
            output.append("")
            
            # Show preview of content
            text = content.get("text", "")[:500]
            output.append(f"   Preview: {text}...")
            output.append("")
            output.append("-" * 80)
            output.append("")
        
        # Summary
        output.append("📊 COMPARISON SUMMARY")
        output.append(f"   Total sources: {len(sources)}")
        output.append(f"   Ready for analysis")
        output.append("")
        output.append("=" * 80)
        
        return "\n".join(output)
    
    except Exception as e:
        return f"❌ Error comparing sources: {str(e)}"


def action_fact_check(helper: ResearchHelper, arguments: dict) -> str:
    """Verify claims across multiple sources"""
    try:
        claim = arguments.get("claim", "")
        if not claim:
            return "❌ No claim provided. Use 'claim' parameter."
        
        patterns = arguments.get("patterns", [])
        tabs = helper.find_tabs_by_pattern(patterns) if patterns else helper.get_tabs()[:10]
        
        if not tabs:
            return "❌ No tabs found"
        
        output = []
        output.append("=" * 80)
        output.append(f"✅ FACT-CHECKING: {claim}")
        output.append("=" * 80)
        output.append("")
        
        claim_lower = claim.lower()
        matches = []
        
        for tab in tabs[:10]:  # Check up to 10 sources
            content = helper.get_tab_content(tab)
            
            if "error" in content:
                continue
            
            text = content.get("text", "").lower()
            
            # Simple keyword matching
            keywords = claim_lower.split()
            keyword_count = sum(1 for kw in keywords if kw in text and len(kw) > 3)
            
            if keyword_count >= len(keywords) // 2:  # At least half keywords match
                matches.append({
                    "title": content.get("title", "Untitled"),
                    "url": content.get("url", ""),
                    "relevance": keyword_count / len(keywords) if keywords else 0
                })
        
        if not matches:
            output.append("❌ No sources found mentioning this claim")
        else:
            output.append(f"✅ Found {len(matches)} sources mentioning related keywords")
            output.append("")
            
            # Sort by relevance
            matches.sort(key=lambda x: x["relevance"], reverse=True)
            
            for i, match in enumerate(matches[:5], 1):
                output.append(f"{i}. {match['title']}")
                output.append(f"   URL: {match['url']}")
                output.append(f"   Relevance: {match['relevance']:.0%}")
                output.append("")
        
        output.append("=" * 80)
        output.append("💡 Note: This is keyword-based matching. Review sources manually for accuracy.")
        output.append("=" * 80)
        
        return "\n".join(output)
    
    except Exception as e:
        return f"❌ Error fact-checking: {str(e)}"


def action_timeline(helper: ResearchHelper, arguments: dict) -> str:
    """Build chronological overview from sources"""
    try:
        patterns = arguments.get("patterns", [])
        tabs = helper.find_tabs_by_pattern(patterns) if patterns else helper.get_tabs()[:5]
        
        if not tabs:
            return "❌ No tabs found"
        
        output = []
        output.append("=" * 80)
        output.append("📅 TIMELINE / CHRONOLOGICAL OVERVIEW")
        output.append("=" * 80)
        output.append("")
        
        # Extract date patterns from content
        events = []
        
        for tab in tabs[:10]:
            content = helper.get_tab_content(tab)
            
            if "error" in content:
                continue
            
            text = content.get("text", "")
            
            # Simple date extraction (YYYY, Month YYYY patterns)
            import re
            
            # Find years
            years = re.findall(r'\b(19\d{2}|20\d{2})\b', text)
            
            # Find month-year patterns
            months = re.findall(r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+(19\d{2}|20\d{2})\b', text)
            
            if years or months:
                events.append({
                    "source": content.get("title", "Untitled"),
                    "url": content.get("url", ""),
                    "years": list(set(years))[:10],
                    "months": [f"{m[0]} {m[1]}" for m in months][:5]
                })
        
        if not events:
            output.append("❌ No temporal information found in sources")
        else:
            for i, event in enumerate(events, 1):
                output.append(f"📄 {event['source']}")
                output.append(f"   URL: {event['url']}")
                
                if event['months']:
                    output.append(f"   Dates mentioned: {', '.join(event['months'][:5])}")
                elif event['years']:
                    output.append(f"   Years mentioned: {', '.join(sorted(set(event['years']))[:10])}")
                
                output.append("")
        
        output.append("=" * 80)
        output.append("💡 Review sources to build accurate timeline")
        output.append("=" * 80)
        
        return "\n".join(output)
    
    except Exception as e:
        return f"❌ Error building timeline: {str(e)}"


def action_references(helper: ResearchHelper, arguments: dict) -> str:
    """Extract citations and links from sources"""
    try:
        patterns = arguments.get("patterns", [])
        tabs = helper.find_tabs_by_pattern(patterns) if patterns else helper.get_tabs()[:5]
        
        if not tabs:
            return "❌ No tabs found"
        
        output = []
        output.append("=" * 80)
        output.append("📚 REFERENCES & CITATIONS")
        output.append("=" * 80)
        output.append("")
        
        all_links = []
        
        for tab in tabs[:10]:
            content = helper.get_tab_content(tab)
            
            if "error" in content:
                continue
            
            output.append(f"📄 {content.get('title', 'Untitled')}")
            output.append(f"   URL: {content.get('url', '')}")
            output.append("")
            
            links = content.get("links", [])
            
            if links:
                output.append("   Key Links:")
                for link in links[:10]:
                    if link.get("text") and link.get("url"):
                        output.append(f"   • {link['text'][:60]}")
                        output.append(f"     {link['url']}")
                
                all_links.extend(links)
            
            output.append("")
            output.append("-" * 80)
            output.append("")
        
        # Summary
        output.append("📊 SUMMARY")
        output.append(f"   Total sources: {len([t for t in tabs if 'error' not in helper.get_tab_content(t)])}")
        output.append(f"   Total links extracted: {len(all_links)}")
        output.append("")
        output.append("=" * 80)
        
        return "\n".join(output)
    
    except Exception as e:
        return f"❌ Error extracting references: {str(e)}"


@registry.register(
    name="research_tools",
    description="Multi-source research and synthesis. Compare information from multiple tabs, fact-check claims, build timelines, and extract references. Perfect for research tasks using open browser tabs.",
    input_schema={
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["compare", "fact_check", "timeline", "references"],
                "description": "Action: compare (compare multiple sources), fact_check (verify claims), timeline (chronological overview), references (extract citations/links)"
            },
            "patterns": {
                "type": "array",
                "items": {"type": "string"},
                "description": "URL or title patterns to find specific tabs (e.g., ['github', 'docs']). If empty, uses all/recent tabs."
            },
            "claim": {
                "type": "string",
                "description": "For fact_check: the claim to verify across sources"
            }
        },
        "required": ["action"]
    }
)
def research_tools(arguments: dict) -> list[TextContent]:
    """Research tools for multi-source analysis"""
    action = arguments.get("action", "compare")
    helper = ResearchHelper()
    
    try:
        if action == "compare":
            result = action_compare(helper, arguments)
        elif action == "fact_check":
            result = action_fact_check(helper, arguments)
        elif action == "timeline":
            result = action_timeline(helper, arguments)
        elif action == "references":
            result = action_references(helper, arguments)
        else:
            result = f"❌ Unknown action: {action}"
        
        return [TextContent(type="text", text=result)]
    
    except Exception as e:
        return [TextContent(type="text", text=f"❌ Error: {str(e)}")]
