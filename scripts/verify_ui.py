"""Playwright UI verification script for AEOForge Ultra-Premium Studio."""

import asyncio
from playwright.async_api import async_playwright

async def verify_ui():
    console_errors = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1600, "height": 1000})
        page = await context.new_page()

        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

        print("1. Navigating to http://127.0.0.1:8000...")
        await page.goto("http://127.0.0.1:8000", wait_until="networkidle")

        title = await page.title()
        print(f"Page Title: {title}")
        assert "AEOForge" in title

        # Check engine badge
        badge_text = await page.inner_text("#engineStatusLabel")
        print(f"Engine status badge: {badge_text}")

        # Capture initial state
        await page.screenshot(path="ui_initial.png", full_page=True)
        print("Captured ui_initial.png")

        # 2. Trigger audit
        print("2. Submitting audit for docs.python.org...")
        await page.fill("#targetUrlInput", "docs.python.org")
        await page.click("#auditSubmitBtn")

        # Wait for audit results
        await page.wait_for_selector("#scoreDisplay:not(:has-text('--'))", timeout=45000)
        score_val = await page.inner_text("#scoreDisplay")
        grade_val = await page.inner_text("#gradeBadge")
        print(f"Audited Score: {score_val}, Grade: {grade_val}")

        # Check Set-of-Mark screenshot and elements
        som_img = await page.query_selector("#screenshotImg")
        is_visible = await som_img.is_visible()
        marks_text = await page.inner_text("#marksBadgeCount")
        print(f"Set-of-Mark Screenshot visible: {is_visible}, Marks: {marks_text}")

        # Check Meta Llama 3.2 Advice
        advice = await page.inner_text("#agentAdviceText")
        print(f"Meta Llama 3.2 Advice: {advice[:80]}...")

        # Capture Audited UI view
        await page.screenshot(path="ui_audited.png", full_page=True)
        print("Captured ui_audited.png")

        # 3. Test Drawer (Deobfuscator)
        print("3. Testing Deobfuscator Drawer...")
        await page.click("button:has-text('Deobfuscator')")
        await page.wait_for_selector("#deobfuscatorDrawer:not(.hidden)")
        await page.screenshot(path="ui_drawer_deobfuscate.png")
        await page.click("#deobfuscatorDrawer button:has-text('Decode String')")
        await page.wait_for_timeout(500)
        decoded = await page.inner_text("#deobfuscateOutput")
        print(f"Deobfuscate Output: {decoded}")
        await page.click("#deobfuscatorDrawer button:has(svg.lucide-x)")

        # 4. Test Handshake Tabs (llms.txt, schema.jsonld)
        print("4. Testing Handshake Tabs...")
        await page.click("#hTab-llms_txt")
        await page.wait_for_timeout(300)
        llms_code = await page.inner_text("#handshakeCodeView")
        print(f"llms.txt Code Sample: {llms_code[:60]}...")

        await page.click("#hTab-blockers")
        await page.wait_for_timeout(300)
        blockers_visible = await page.is_visible("#blockersView")
        print(f"Blockers View visible: {blockers_visible}")

        await page.screenshot(path="ui_handshake.png", full_page=True)
        print("Captured ui_handshake.png")

        await browser.close()

        if console_errors:
            print(f"WARNING: Console errors detected: {console_errors}")
        else:
            print("SUCCESS: 0 console errors detected!")

if __name__ == "__main__":
    asyncio.run(verify_ui())
