# server/tools/devtools_base.py
"""
Shared base class for Chrome DevTools Protocol connections.
Used by chrome_devtools, research_tools, and read_page tools.
"""

import json
import requests
import websocket
import logging
from typing import Optional, List, Dict, Any

# Configure logging
logger = logging.getLogger(__name__)


class DevToolsClient:
    """Base client for Chrome DevTools Protocol"""

    def __init__(self, host: str = "localhost", port: int = 9222, timeout: int = 10):
        """
        Initialize DevTools client.

        Args:
            host: Chrome/Opera DevTools host (default: localhost)
            port: DevTools port (default: 9222)
            timeout: WebSocket timeout in seconds (default: 10)
        """
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self.ws: Optional[websocket.WebSocket] = None
        self.message_id = 0
        self.timeout = timeout

    def get_tabs(self) -> List[Dict[str, Any]]:
        """Get list of all open tabs"""
        try:
            response = requests.get(f"{self.base_url}/json", timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get tabs: {e}")
            raise Exception(f"Failed to get tabs: {str(e)}")

    def find_tab(
        self,
        url: Optional[str] = None,
        title: Optional[str] = None,
        index: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Find tab by URL pattern, title, or index.

        Args:
            url: URL pattern to match (case-insensitive)
            title: Title pattern to match (case-insensitive)
            index: Tab index (0-based)

        Returns:
            Tab dictionary or None if not found
        """
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

    def connect_to_tab(self, tab: Dict[str, Any]) -> None:
        """
        Connect WebSocket to specific tab.

        Args:
            tab: Tab dictionary from get_tabs()

        Raises:
            Exception: If connection fails
        """
        ws_url = tab.get("webSocketDebuggerUrl")
        if not ws_url:
            raise Exception("Tab does not have WebSocket URL")

        try:
            # Close existing connection if any
            if self.ws:
                self.close()

            # Create new connection with timeout
            self.ws = websocket.create_connection(ws_url, timeout=self.timeout)
            logger.debug(f"Connected to tab: {tab.get('title', 'Untitled')}")

        except Exception as e:
            logger.error(f"Failed to connect to tab: {e}")
            raise Exception(f"Failed to connect WebSocket: {str(e)}")

    def send_command(self, method: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Send command to Chrome DevTools.

        Args:
            method: DevTools protocol method (e.g., "Runtime.evaluate")
            params: Method parameters

        Returns:
            Result dictionary from DevTools

        Raises:
            Exception: If not connected or command fails
        """
        if not self.ws:
            raise Exception("Not connected to any tab. Call connect_to_tab() first.")

        self.message_id += 1
        message = {
            "id": self.message_id,
            "method": method,
            "params": params or {}
        }

        try:
            self.ws.send(json.dumps(message))
            self.ws.settimeout(self.timeout)

            # Wait for response with timeout protection
            max_iterations = 100
            iterations = 0

            while iterations < max_iterations:
                try:
                    response = json.loads(self.ws.recv())
                    if response.get("id") == self.message_id:
                        if "error" in response:
                            error_msg = response['error']
                            logger.error(f"DevTools error for {method}: {error_msg}")
                            raise Exception(f"DevTools error: {error_msg}")
                        return response.get("result", {})
                    iterations += 1

                except websocket.WebSocketTimeoutException:
                    logger.error(f"Timeout waiting for response to {method}")
                    raise Exception(f"Timeout waiting for DevTools response to {method}")

            raise Exception(f"Too many messages received without matching ID for {method}")

        except Exception as e:
            logger.error(f"Error sending command {method}: {e}")
            raise

    def execute_js(self, expression: str, return_by_value: bool = True) -> Any:
        """
        Execute JavaScript in the connected tab.

        Args:
            expression: JavaScript code to execute
            return_by_value: Return result by value (default: True)

        Returns:
            Result of JavaScript execution

        Raises:
            Exception: If execution fails
        """
        result = self.send_command("Runtime.evaluate", {
            "expression": expression,
            "returnByValue": return_by_value
        })

        if result.get("exceptionDetails"):
            error = result["exceptionDetails"]
            error_text = error.get("text", "Unknown error")
            logger.error(f"JavaScript execution error: {error_text}")
            raise Exception(f"JavaScript error: {error_text}")

        return result.get("result", {}).get("value")

    def close(self):
        """Close WebSocket connection"""
        if self.ws:
            try:
                self.ws.close()
                logger.debug("WebSocket connection closed")
            except Exception as e:
                logger.debug(f"Error closing WebSocket (may already be closed): {e}")
            finally:
                self.ws = None

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensure cleanup"""
        self.close()
        return False
