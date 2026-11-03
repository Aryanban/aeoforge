"""Playwright UI verification script for AEOForge."""

import asyncio
from playwright.async_api import async_playwright

async def verify_ui():
    console_errors = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await context.new_page()

        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

        print("1. Navigating to http://127.0.0.1:8000...")
        await page.goto("http://127.0.0.1:8000", wait_until="networkidle")

        # Verify page title
        title = await page.title()
        print(f"Page Title: {title}")
        assert "AEOForge" in title

        # Wait for system status to resolve
        await page.wait_for_selector("#engineStatusText")
        status_text = await page.inner_text("#engineStatusText")
        print(f"System Status Badge: {status_text}")

        # Capture Initial UI
        await page.screenshot(path="ui_initial.png", full_page=True)
        print("Captured ui_initial.png")

        # Trigger audit
        print("2. Submitting audit for https://example.com...")
        await page.click("#auditSubmitBtn")

        # Wait for results container to become visible
        await page.wait_for_selector("#resultsContainer:not(.hidden)", timeout=35000)
        print("Results container visible!")

        # Verify score display has a number
        score_val = await page.inner_text("#scoreDisplay")
        grade_val = await page.inner_text("#gradeBadge")
        print(f"Audited Score: {score_val}, Grade: {grade_val}")

        # Check Set-of-Mark image
        som_img = await page.query_selector("#screenshotImg")
        is_visible = await som_img.is_visible()
        print(f"Set-of-Mark Screenshot visible: {is_visible}")

        # Check Meta Llama 3.2 advice
        advice = await page.inner_text("#agentAdviceText")
        print(f"Meta Llama 3.2 Advice: {advice[:80]}...")

        # Capture Audited UI
        await page.screenshot(path="ui_audited.png", full_page=True)
        print("Captured ui_audited.png")

        # Switch to Handshake Studio
        print("3. Switching to Handshake Studio...")
        await page.click("#tab-handshake")
        await page.wait_for_timeout(1000)
        code_text = await page.inner_text("#handshakeCodeView")
        print(f"Handshake Code Sample: {code_text[:60]}...")
        await page.screenshot(path="ui_handshake.png", full_page=True)
        print("Captured ui_handshake.png")

        # Switch to Crawler Tab
        print("4. Switching to Crawler Tab...")
        await page.click("#tab-crawler")
        await page.wait_for_timeout(500)
        await page.screenshot(path="ui_crawler.png", full_page=True)
        print("Captured ui_crawler.png")

        await browser.close()

        if console_errors:
            print(f"WARNING: Console errors detected: {console_errors}")
        else:
            print("SUCCESS: 0 console errors detected!")

if __name__ == "__main__":
    asyncio.run(verify_ui())
