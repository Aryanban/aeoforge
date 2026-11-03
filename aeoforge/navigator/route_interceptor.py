"""Playwright route interception for turbo-speed agent traversal.
Ported and adapted from LeadForge (https://github.com/Aryanban/leadforge).
"""

from typing import Set

# Asset types and URL substrings to abort for maximum speed
BLOCKED_RESOURCE_TYPES: Set[str] = {
    "font",
    "media",
}

BLOCKED_URL_PATTERNS: Set[str] = {
    # Analytics & tracking scripts
    "google-analytics.com",
    "googletagmanager.com",
    "doubleclick.net",
    "connect.facebook.net",
    "facebook.com/tr",
    "hotjar.com",
    "segment.io",
    "mixpanel.com",
    "intercom.io",
    "drift.com",
    "clarity.ms",
    "fullstory.com",
    "scorecardresearch.com",
    "bat.bing.com",
    # Ad networks
    "adnxs.com",
    "criteo.com",
    "outbrain.com",
    "taboola.com",
    "adroll.com",
}


async def setup_route_interception(page, block_images: bool = False):
    """Attach route handler to intercept and drop non-essential agent traffic."""
    async def route_handler(route):
        request = route.request
        url_lower = request.url.lower()
        resource_type = request.resource_type

        # Check resource type
        if resource_type in BLOCKED_RESOURCE_TYPES:
            await route.abort()
            return

        if block_images and resource_type == "image":
            # Only block if explicitly requested (we might want screenshots for vision)
            await route.abort()
            return

        # Check tracking and heavy patterns
        for pattern in BLOCKED_URL_PATTERNS:
            if pattern in url_lower:
                await route.abort()
                return

        await route.continue_()

    await page.route("**/*", route_handler)
