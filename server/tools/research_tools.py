# server/tools/research_tools.py
import time
import re
import logging
from typing import List, Dict, Optional
from mcp.types import TextContent
from server.registry import registry
from server.tools.devtools_base import DevToolsClient

# Configure logging
logger = logging.getLogger(__name__)


class ResearchHelper(DevToolsClient):
    """Helper for multi-source research using browser tabs"""

    # Cache timeout in seconds (5 minutes)
    CACHE_TIMEOUT = 300

    # Trusted domains for credibility scoring
    TRUSTED_DOMAINS = {
        # News
        'reuters.com': 0.9, 'apnews.com': 0.9, 'bbc.com': 0.9, 'npr.org': 0.85,
        # Academic
        'arxiv.org': 0.95, 'ieee.org': 0.95, 'nature.com': 0.95, 'science.org': 0.95,
        'scholar.google.com': 0.9, 'researchgate.net': 0.85,
        # Government
        'gov': 0.9, 'edu': 0.85,
        # Tech Documentation
        'github.com': 0.8, 'stackoverflow.com': 0.75, 'docs.python.org': 0.9,
        'developer.mozilla.org': 0.9, 'w3.org': 0.9
    }

    def __init__(self, host: str = "localhost", port: int = 9222):
        super().__init__(host, port)
        self._content_cache: Dict[str, Dict] = {}  # Cache tab content by URL
        self._cache_timestamps: Dict[str, float] = {}  # Track cache age

    def extract_keywords(self, text: str, top_n: int = 10) -> List[str]:
        """Extract top keywords from text using simple frequency analysis"""
        # Remove common stop words
        stop_words = {
            'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'i',
            'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at',
            'this', 'but', 'his', 'by', 'from', 'they', 'we', 'say', 'her', 'she',
            'or', 'an', 'will', 'my', 'one', 'all', 'would', 'there', 'their',
            'is', 'was', 'are', 'been', 'has', 'had', 'were', 'can', 'said',
            'use', 'each', 'which', 'how', 'when', 'up', 'out', 'if', 'about',
            'who', 'get', 'them', 'make', 'than', 'many', 'then', 'so', 'some'
        }

        # Tokenize and count
        words = re.findall(r'\b[a-z]{4,}\b', text.lower())
        word_freq = {}

        for word in words:
            if word not in stop_words:
                word_freq[word] = word_freq.get(word, 0) + 1

        # Sort by frequency
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, _ in sorted_words[:top_n]]

    def analyze_sentiment(self, text: str) -> Dict[str, any]:
        """Basic sentiment analysis using keyword matching"""
        positive_words = {
            'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic',
            'best', 'better', 'improved', 'success', 'successful', 'effective',
            'positive', 'benefit', 'advantage', 'helpful', 'valuable', 'quality'
        }

        negative_words = {
            'bad', 'poor', 'terrible', 'awful', 'worst', 'worse', 'failed',
            'failure', 'ineffective', 'negative', 'problem', 'issue', 'disadvantage',
            'concern', 'risk', 'danger', 'harmful', 'difficult', 'challenge'
        }

        words = set(re.findall(r'\b[a-z]+\b', text.lower()))

        pos_count = len(words & positive_words)
        neg_count = len(words & negative_words)
        total = pos_count + neg_count

        if total == 0:
            return {'sentiment': 'neutral', 'confidence': 0.5, 'positive': 0, 'negative': 0}

        sentiment = 'positive' if pos_count > neg_count else ('negative' if neg_count > pos_count else 'neutral')
        confidence = abs(pos_count - neg_count) / total if total > 0 else 0.5

        return {
            'sentiment': sentiment,
            'confidence': round(confidence, 2),
            'positive': pos_count,
            'negative': neg_count
        }

    def score_source_credibility(self, url: str) -> Dict[str, any]:
        """Score source credibility based on domain and URL patterns"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc.lower()

            # Check against trusted domains
            score = 0.5  # Default neutral score

            for trusted, trust_score in self.TRUSTED_DOMAINS.items():
                if trusted in domain:
                    score = trust_score
                    break

            # Adjust based on URL patterns
            indicators = {
                'positive': ['research', 'study', 'journal', 'academic', 'official', 'docs', 'documentation'],
                'negative': ['blog', 'forum', 'wiki', 'personal', 'ad', 'ads', 'promo']
            }

            url_lower = url.lower()
            for keyword in indicators['positive']:
                if keyword in url_lower:
                    score = min(score + 0.05, 1.0)

            for keyword in indicators['negative']:
                if keyword in url_lower:
                    score = max(score - 0.1, 0.0)

            # HTTPS bonus
            if parsed.scheme == 'https':
                score = min(score + 0.05, 1.0)

            credibility = 'high' if score >= 0.8 else ('medium' if score >= 0.5 else 'low')

            return {
                'score': round(score, 2),
                'credibility': credibility,
                'domain': domain
            }

        except Exception as e:
            logger.error(f"Error scoring credibility: {e}")
            return {'score': 0.5, 'credibility': 'unknown', 'domain': url}

    def get_page_tabs(self) -> List[Dict]:
        """Get list of all page tabs (excludes extensions, etc.)"""
        try:
            tabs = self.get_tabs()
            return [t for t in tabs if t.get("type") == "page"]
        except Exception as e:
            logger.error(f"Failed to get tabs: {e}")
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

        try:
            # Connect to tab
            self.connect_to_tab(tab)

            # JavaScript to extract content
            js_code = """
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
            """

            # Use base class execute_js method
            content = self.execute_js(js_code)

            # Cache the content
            if tab_url and content and isinstance(content, dict):
                self._content_cache[tab_url] = content
                self._cache_timestamps[tab_url] = time.time()
                logger.debug(f"Cached content for {tab_url}")

            return content

        except Exception as e:
            logger.error(f"Error fetching tab content: {e}")
            return {"error": str(e)}
        finally:
            self.close()
    
    def find_tabs_by_pattern(self, patterns: List[str]) -> List[Dict]:
        """Find tabs matching URL or title patterns"""
        tabs = self.get_page_tabs()
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
    """Compare information from multiple tabs with NLP analysis"""
    try:
        patterns = arguments.get("patterns", [])
        max_sources = arguments.get("max_sources", 5)  # Configurable limit

        if not patterns:
            # Get all tabs if no patterns specified
            tabs = helper.get_page_tabs()[:max_sources]
        else:
            tabs = helper.find_tabs_by_pattern(patterns)[:max_sources]

        if not tabs:
            return "❌ No tabs found matching patterns"

        output = []
        output.append("=" * 80)
        output.append("🔍 COMPARING SOURCES WITH NLP ANALYSIS")
        output.append("=" * 80)
        output.append("")

        sources = []
        for i, tab in enumerate(tabs, 1):
            content = helper.get_tab_content(tab)

            if "error" in content:
                continue

            sources.append(content)

            # Extract URL and score credibility
            url = content.get('url', '')
            cred = helper.score_source_credibility(url)

            # Extract text and analyze
            text = content.get("text", "")
            keywords = helper.extract_keywords(text, top_n=5)
            sentiment = helper.analyze_sentiment(text)

            output.append(f"📄 SOURCE {i}: {content.get('title', 'Untitled')}")
            output.append(f"   URL: {url}")
            output.append(f"   📊 Credibility: {cred['credibility'].upper()} ({cred['score']}) - {cred['domain']}")
            output.append(f"   💭 Sentiment: {sentiment['sentiment'].upper()} (confidence: {sentiment['confidence']})")
            output.append(f"   🔑 Keywords: {', '.join(keywords)}")
            output.append("")

            # Show preview of content
            preview = text[:300]
            output.append(f"   Preview: {preview}...")
            output.append("")
            output.append("-" * 80)
            output.append("")

        # Summary
        output.append("📊 COMPARISON SUMMARY")
        output.append(f"   Total sources analyzed: {len(sources)}")
        if sources:
            avg_cred = sum(helper.score_source_credibility(s.get('url', ''))['score'] for s in sources) / len(sources)
            output.append(f"   Average credibility: {avg_cred:.2f}")
        output.append("")
        output.append("=" * 80)

        return "\n".join(output)

    except Exception as e:
        logger.error(f"Error comparing sources: {e}")
        return f"❌ Error comparing sources: {str(e)}"


def action_fact_check(helper: ResearchHelper, arguments: dict) -> str:
    """Verify claims across multiple sources with credibility scoring"""
    try:
        claim = arguments.get("claim", "")
        if not claim:
            return "❌ No claim provided. Use 'claim' parameter."

        patterns = arguments.get("patterns", [])
        max_sources = arguments.get("max_sources", 10)  # Configurable

        tabs = helper.find_tabs_by_pattern(patterns) if patterns else helper.get_page_tabs()[:max_sources]

        if not tabs:
            return "❌ No tabs found"

        output = []
        output.append("=" * 80)
        output.append(f"✅ FACT-CHECKING WITH CREDIBILITY ANALYSIS: {claim}")
        output.append("=" * 80)
        output.append("")

        claim_lower = claim.lower()
        matches = []

        for tab in tabs:
            content = helper.get_tab_content(tab)

            if "error" in content:
                continue

            text = content.get("text", "").lower()
            url = content.get("url", "")

            # Enhanced keyword matching
            keywords = claim_lower.split()
            keyword_count = sum(1 for kw in keywords if kw in text and len(kw) > 3)

            if keyword_count >= len(keywords) // 2:  # At least half keywords match
                # Score credibility
                cred = helper.score_source_credibility(url)

                matches.append({
                    "title": content.get("title", "Untitled"),
                    "url": url,
                    "relevance": keyword_count / len(keywords) if keywords else 0,
                    "credibility": cred['score'],
                    "credibility_level": cred['credibility']
                })

        if not matches:
            output.append("❌ No sources found mentioning this claim")
        else:
            output.append(f"✅ Found {len(matches)} sources mentioning related keywords")
            output.append("")

            # Sort by combined relevance and credibility
            matches.sort(key=lambda x: (x["credibility"] * 0.6 + x["relevance"] * 0.4), reverse=True)

            for i, match in enumerate(matches[:5], 1):
                output.append(f"{i}. {match['title']}")
                output.append(f"   URL: {match['url']}")
                output.append(f"   📊 Credibility: {match['credibility_level'].upper()} ({match['credibility']})")
                output.append(f"   🎯 Relevance: {match['relevance']:.0%}")
                output.append(f"   ⭐ Combined Score: {(match['credibility'] * 0.6 + match['relevance'] * 0.4):.2f}")
                output.append("")

            # Calculate weighted average credibility
            avg_cred = sum(m['credibility'] for m in matches) / len(matches)
            output.append(f"Average source credibility: {avg_cred:.2f}")

        output.append("")
        output.append("=" * 80)
        output.append("💡 Note: Uses keyword matching + credibility scoring. Review sources manually.")
        output.append("=" * 80)

        return "\n".join(output)

    except Exception as e:
        logger.error(f"Error fact-checking: {e}")
        return f"❌ Error fact-checking: {str(e)}"


def action_timeline(helper: ResearchHelper, arguments: dict) -> str:
    """Build chronological overview from sources"""
    try:
        patterns = arguments.get("patterns", [])
        tabs = helper.find_tabs_by_pattern(patterns) if patterns else helper.get_page_tabs()[:5]

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
        tabs = helper.find_tabs_by_pattern(patterns) if patterns else helper.get_page_tabs()[:5]

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
    description="Multi-source research with NLP and credibility scoring. Compare tabs with sentiment analysis and keyword extraction, fact-check claims with source credibility, build timelines, extract references. Perfect for in-depth research using open browser tabs.",
    input_schema={
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["compare", "fact_check", "timeline", "references"],
                "description": "Action: compare (NLP analysis + credibility), fact_check (verify with scoring), timeline (chronological), references (extract citations)"
            },
            "patterns": {
                "type": "array",
                "items": {"type": "string"},
                "description": "URL or title patterns to find specific tabs (e.g., ['github', 'docs']). If empty, uses all/recent tabs."
            },
            "claim": {
                "type": "string",
                "description": "For fact_check: the claim to verify across sources"
            },
            "max_sources": {
                "type": "integer",
                "description": "Maximum number of sources to analyze (default: 5 for compare, 10 for fact_check)"
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
