"""Playwright route interception for turbo-speed agent traversal.
Ported and adapted from LeadForge (https://github.com/Aryanban/leadforge).
"""

import re
from typing import Set

# Asset types to abort for maximum speed and zero token/bandwidth waste
BLOCKED_RESOURCE_TYPES: Set[str] = {
    "font",
    "media",
    "websocket",
}

# Precompiled regex pattern of top tracker, analytics, and telemetry networks
TRACKER_PATTERN = re.compile(
    r"(google-analytics\.com|googletagmanager\.com|doubleclick\.net|connect\.facebook\.net|"
    r"facebook\.com/tr|hotjar\.com|segment\.io|mixpanel\.com|intercom\.io|drift\.com|"
    r"clarity\.ms|fullstory\.com|scorecardresearch\.com|bat\.bing\.com|adnxs\.com|"
    r"criteo\.com|outbrain\.com|taboola\.com|adroll\.com|googlesyndication\.com|"
    r"adservice\.google\.com|amazon-adsystem\.com|cdn\.amplitude\.com|heapanalytics\.com|"
    r"pixel\.wp\.com|chartbeat\.com|mouseflow\.com|luckyorange\.com)",
    re.IGNORECASE
)


async def setup_route_interception(page, block_images: bool = False):
    """Attach route handler to intercept and drop non-essential agent traffic."""
    async def route_handler(route):
        request = route.request
        resource_type = request.resource_type

        # 1. Abort heavy non-DOM resource types immediately
        if resource_type in BLOCKED_RESOURCE_TYPES:
            await route.abort()
            return

        if block_images and resource_type == "image":
            await route.abort()
            return

        # 2. Abort analytics, ads, and telemetry via compiled automaton
        if TRACKER_PATTERN.search(request.url):
            await route.abort()
            return

        await route.continue_()

    await page.route("**/*", route_handler)
