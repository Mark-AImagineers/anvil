# server/playwright_config.py
"""
Playwright safety configuration

WHITELIST: Only these domains are allowed (if not empty)
BLACKLIST: These domains are blocked (checked first)

Leave both empty for no restrictions (use with caution!)
"""

# Blocked domains - these will NEVER be accessible
PLAYWRIGHT_BLACKLIST = [
    # Add domains to block, e.g.:
    # "malicious-site.com",
    # "spam-domain.net",
]

# Allowed domains - if not empty, ONLY these domains are accessible
# Empty list = all domains allowed (except blacklisted)
PLAYWRIGHT_WHITELIST = [
    # Add domains to allow, e.g.:
    # "localhost",
    # "127.0.0.1",
    # "github.com",
    # "your-domain.com",
]

# Auto-allow localhost by default (set to False to disable)
ALLOW_LOCALHOST = True
