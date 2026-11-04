"""Browser automation controller using Playwright Stealth.
Integrates route interception, Set-of-Mark grounding, and navigation trap detection.
"""

import base64
import os
import platform
import re
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup
from pydantic import BaseModel

from aeoforge.config import settings
from aeoforge.navigator.route_interceptor import setup_route_interception
from aeoforge.navigator.trap_detector import detect_navigation_traps
from aeoforge.navigator.som_grounding import (
    extract_interactive_marks,
    inject_som_badges,
    remove_som_badges,
    build_a11y_tree_representation,
)
from aeoforge.utils.deobfuscator import extract_obfuscated_emails

# Cross-platform environment resolution (macOS, Linux, Windows)
HOST_OS = platform.system()
if HOST_OS == "Linux":
    DEFAULT_UA_PLATFORM = '"Linux"'
    DEFAULT_USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
elif HOST_OS == "Windows":
    DEFAULT_UA_PLATFORM = '"Windows"'
    DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
else:
    DEFAULT_UA_PLATFORM = '"macOS"'
    DEFAULT_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"

# Ultra-hardened, low-latency Chromium launch arguments across Mac, Windows, and Linux
CROSS_PLATFORM_CHROMIUM_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--disable-infobars",
    "--window-size=1280,800",
    "--disable-dev-shm-usage",  # Crucial for Linux & Docker containers to eliminate /dev/shm OOM crashes
    "--disable-gpu",            # Essential for headless Linux/Windows WSL environments
    "--no-first-run",
    "--no-default-browser-check",
    "--disable-background-networking",
    "--disable-background-timer-throttling",
    "--disable-backgrounding-occluded-windows",
    "--disable-breakpad",
    "--disable-component-extensions-with-background-pages",
    "--disable-extensions",
    "--disable-features=Translate,BackForwardCache,AcceptCHFrame,MediaRouter,OptimizationHints",
    "--disable-ipc-flooding-protection",
    "--disable-renderer-backgrounding",
    "--force-color-profile=srgb",
    "--metrics-recording-only",
    "--mute-audio",
]


class NavigatedPageData(BaseModel):
    url: str
    final_url: str
    title: str
    html: str
    text_content: str
    dom_element_count: int
    raw_html_tokens: int
    text_tokens: int
    token_ratio: float
    screenshot_base64: Optional[str] = None
    traps: list
    interactive_marks: list
    a11y_tree: str
    emails: list


class BrowserNavigator:
    """Headless browser engine for agentic web inspection."""

    def __init__(self, headless: bool = True, timeout_ms: int = 30000):
        self.headless = headless
        self.timeout_ms = timeout_ms

    async def inspect_url(self, url: str, capture_screenshot: bool = True) -> NavigatedPageData:
        """Navigate to URL, detect traps, ground interactive elements, and capture state."""
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=self.headless,
                args=CROSS_PLATFORM_CHROMIUM_ARGS
            )
            context = await browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent=DEFAULT_USER_AGENT,
                locale="en-US",
                extra_http_headers={
                    "Accept-Language": "en-US,en;q=0.9",
                    "Upgrade-Insecure-Requests": "1"
                }
            )

            # Mask headless artifacts (inspired by playwright-stealth)
            # shortcut: masks webdriver and languages; upgrade to full WebGL/Canvas fingerprint spoofer if specialized fraud systems target tests
            await context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
                window.chrome = { runtime: {} };
            """)

            page = await context.new_page()

            # Attach route interception to block bloat
            if settings.playwright_fast_route_filter:
                await setup_route_interception(page, block_images=not capture_screenshot)

            http_status = 200
            try:
                response = await page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)
                if response:
                    http_status = response.status
                
                # Dynamic hydration for modern SPAs (Next.js, React, Vue):
                # Wait for network stabilization and document rendering with fallback debounce
                try:
                    await page.wait_for_load_state("networkidle", timeout=3500)
                except Exception:
                    pass
                
                # Verify body has rendered content
                try:
                    await page.wait_for_function("() => document.body && document.body.innerText.trim().length > 20", timeout=2000)
                except Exception:
                    pass
                await page.wait_for_timeout(300)
            except Exception as e:
                pass

            final_url = page.url
            title = await page.title()
            html = await page.content()

            # Detect traps, captchas, and WAF firewalls
            traps = await detect_navigation_traps(page)
            if http_status in (403, 429, 503):
                traps.append({
                    "name": f"HTTP {http_status} WAF / Rate-Limit Block",
                    "category": "firewall_block",
                    "severity": "critical",
                    "active_selector": "http_status",
                    "dismiss_selector": None,
                    "recommendation": f"Server returned HTTP {http_status}. Check Cloudflare/Vercel firewall rate-limits."
                })

            # Extract Set-of-Mark interactive elements
            marks = await extract_interactive_marks(page)
            a11y_tree = build_a11y_tree_representation(marks)

            # Screenshot with Set-of-Mark visual bounding boxes
            screenshot_b64 = None
            if capture_screenshot:
                try:
                    await inject_som_badges(page, marks)
                    screenshot_bytes = await page.screenshot(type="jpeg", quality=75)
                    screenshot_b64 = base64.b64encode(screenshot_bytes).decode("utf-8")
                    await remove_som_badges(page)
                except Exception:
                    pass

            await browser.close()

            # Text analysis & metrics
            soup = BeautifulSoup(html, "html.parser")
            # Strip script and style tags for clean text calculation
            for tag in soup(["script", "style", "noscript", "svg"]):
                tag.decompose()
            clean_text = soup.get_text(separator=" ", strip=True)

            dom_elements = len(soup.find_all())
            raw_html_tokens = max(1, len(html) // 4)
            text_tokens = max(1, len(clean_text) // 4)
            token_ratio = round(text_tokens / raw_html_tokens, 4)

            emails = extract_obfuscated_emails(html)

            return NavigatedPageData(
                url=url,
                final_url=final_url,
                title=title,
                html=html,
                text_content=clean_text[:10000],  # Cap sample for downstream evaluation
                dom_element_count=dom_elements,
                raw_html_tokens=raw_html_tokens,
                text_tokens=text_tokens,
                token_ratio=token_ratio,
                screenshot_base64=screenshot_b64,
                traps=traps,
                interactive_marks=marks,
                a11y_tree=a11y_tree,
                emails=emails
            )
