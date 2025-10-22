# server/tools/playwright_session.py
from typing import Optional, Dict
from playwright.sync_api import Browser, Page, sync_playwright
import atexit
import time
import logging

# Configure logging
logger = logging.getLogger(__name__)


class PlaywrightSession:
    """Manages a single Playwright browser session"""

    # Session timeout in seconds (30 minutes)
    SESSION_TIMEOUT = 1800

    def __init__(self):
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.session_id: Optional[str] = None
        self.last_activity: float = 0  # Track last activity time
        self.created_at: float = 0  # Track session creation time
    
    def is_active(self) -> bool:
        """Check if session is active and not expired"""
        if self.browser is None or self.page is None:
            return False

        # Check if session has expired
        if time.time() - self.last_activity > self.SESSION_TIMEOUT:
            logger.info(f"Session {self.session_id} expired due to inactivity")
            self.cleanup()
            return False

        return True

    def _update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = time.time()
    
    def launch(self, headless: bool = True, browser_type: str = "chromium") -> dict:
        """Launch browser and create page"""
        if self.is_active():
            return {
                "success": False,
                "error": "Session already active. Close existing session first."
            }

        try:
            import uuid
            self.session_id = str(uuid.uuid4())[:8]

            # Initialize timestamps
            current_time = time.time()
            self.created_at = current_time
            self.last_activity = current_time

            self.playwright = sync_playwright().start()

            # Select browser
            if browser_type == "firefox":
                browser_launcher = self.playwright.firefox
            elif browser_type == "webkit":
                browser_launcher = self.playwright.webkit
            else:
                browser_launcher = self.playwright.chromium

            self.browser = browser_launcher.launch(headless=headless)
            self.page = self.browser.new_page()

            # Set default timeout
            self.page.set_default_timeout(30000)  # 30 seconds

            logger.info(f"Playwright session {self.session_id} launched successfully")

            return {
                "success": True,
                "session_id": self.session_id,
                "browser": browser_type,
                "headless": headless
            }

        except Exception as e:
            logger.error(f"Failed to launch Playwright session: {e}")
            self.cleanup()
            return {
                "success": False,
                "error": str(e)
            }
    
    def close(self) -> dict:
        """Close browser and cleanup"""
        if not self.is_active():
            return {
                "success": False,
                "error": "No active session to close"
            }
        
        try:
            self.cleanup()
            return {
                "success": True,
                "message": "Session closed and cleaned up"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def cleanup(self):
        """Internal cleanup method"""
        try:
            if self.page:
                self.page.close()
                self.page = None
            
            if self.browser:
                self.browser.close()
                self.browser = None
            
            if self.playwright:
                self.playwright.stop()
                self.playwright = None
            
            self.session_id = None
        except:
            pass
    
    def get_page(self) -> Optional[Page]:
        """Get current page instance"""
        if self.is_active():
            self._update_activity()  # Update activity on page access
            return self.page
        return None


# Global session instance
_session = PlaywrightSession()


# Cleanup on exit
def _cleanup_on_exit():
    _session.cleanup()


atexit.register(_cleanup_on_exit)


def get_session() -> PlaywrightSession:
    """Get the global session instance"""
    return _session
