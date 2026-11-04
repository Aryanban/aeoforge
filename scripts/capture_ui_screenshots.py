"""Playwright script to capture screenshots of AEOForge for visual quality inspection."""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

ARTIFACTS_DIR = Path("/Users/aryanbansal/.gemini/antigravity/brain/23a05fa8-37e4-4796-8231-43578f60c020")
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

async def capture_screenshots():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=2)
        page = await context.new_page()

        print("1. Navigating to AEOForge UI...")
        await page.goto("http://127.0.0.1:8000", wait_until="networkidle")

        # Capture initial state
        header_el = await page.query_selector("header")
        if header_el:
            await header_el.screenshot(path=str(ARTIFACTS_DIR / "header_deslopified.png"))
            print("Captured header_deslopified.png")

        # Audit cerebralvalley.ai
        print("2. Auditing cerebralvalley.ai...")
        await page.click("button:has-text('cerebralvalley.ai')")
        await page.wait_for_selector("#scoreDisplay:not(:has-text('--'))", timeout=45000)
        await page.wait_for_timeout(1000)

        # Full page screenshot
        await page.screenshot(path=str(ARTIFACTS_DIR / "cerebralvalley_audit_full.png"), full_page=True)
        print("Captured cerebralvalley_audit_full.png")

        # Roadmap to 100 / Recommendations panel screenshot
        recs_panel = await page.query_selector("#handshakeSection")
        if recs_panel:
            await recs_panel.screenshot(path=str(ARTIFACTS_DIR / "roadmap_to_100_panel.png"))
            print("Captured roadmap_to_100_panel.png")

        # Score & Telemetry HUD screenshot
        hud_el = await page.query_selector("#resultsContainer > div:first-child")
        if hud_el:
            await hud_el.screenshot(path=str(ARTIFACTS_DIR / "telemetry_hud.png"))
            print("Captured telemetry_hud.png")

        # Audit docs.python.org
        print("3. Auditing docs.python.org for Set-of-Mark visual grounding...")
        await page.click("button:has-text('docs.python.org')")
        # Wait for loading indicator to appear then disappear
        await page.wait_for_selector("#loadingIndicator:not(.hidden)", timeout=5000)
        await page.wait_for_selector("#loadingIndicator", state="hidden", timeout=45000)
        await page.wait_for_timeout(1000)

        # Full page screenshot of docs.python.org
        await page.screenshot(path=str(ARTIFACTS_DIR / "docs_python_audit_full.png"), full_page=True)
        print("Captured docs_python_audit_full.png")

        # Set-of-Mark visual perception canvas
        som_el = await page.query_selector("#screenshotViewport")
        if som_el:
            await som_el.screenshot(path=str(ARTIFACTS_DIR / "som_perception_canvas.png"))
            print("Captured som_perception_canvas.png")

        await browser.close()
        print("Done capturing screenshots.")

if __name__ == "__main__":
    asyncio.run(capture_screenshots())
