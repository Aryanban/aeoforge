"""Playwright UI verification script for AEOForge Studio with Recommendations & Competitor Comparison."""

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

        # 2. Trigger audit
        print("2. Submitting audit for docs.python.org...")
        await page.fill("#targetUrlInput", "docs.python.org")
        await page.click("#auditSubmitBtn")

        # Wait for audit results
        await page.wait_for_selector("#scoreDisplay:not(:has-text('--'))", timeout=45000)
        score_val = await page.inner_text("#scoreDisplay")
        grade_val = await page.inner_text("#gradeBadge")
        print(f"Audited Score: {score_val}, Grade: {grade_val}")

        # Verify Recommendations & Potential Score Simulator
        pot_score = await page.inner_text("#potentialSimScore")
        print(f"Potential Simulated Score: {pot_score}")
        recs_count = await page.evaluate("() => document.querySelectorAll('#recommendationsList input[type=checkbox]').length")
        print(f"Prioritized Recommendations Count: {recs_count}")
        assert recs_count >= 4, "Should render at least 4 prioritized recommendations"

        # Capture Audited UI view with recommendations
        await page.screenshot(path="ui_audited.png", full_page=True)
        print("Captured ui_audited.png")

        # 3. Test Cloudflare WAF Tab
        print("3. Testing Cloudflare WAF Rules Tab...")
        await page.click("#hTab-waf_rules")
        await page.wait_for_timeout(300)
        waf_text = await page.inner_text("#wafCodeView")
        print(f"Cloudflare WAF Rule Sample: {waf_text[:80]}...")
        assert "cf.client.bot" in waf_text

        # 4. Test Competitor Comparison Drawer
        print("4. Testing Competitor Comparison Drawer...")
        await page.click("button:has-text('Competitor Outranking')")
        await page.wait_for_selector("#compareDrawer:not(.hidden)")
        await page.fill("#compareTargetInput", "example.com")
        await page.fill("#compareCompetitorInput", "iana.org")
        await page.click("#compareSubmitBtn")

        await page.wait_for_selector("#compareResults:not(.hidden)", timeout=45000)
        t_score = await page.inner_text("#compareTargetScore")
        c_score = await page.inner_text("#compareCompetitorScore")
        print(f"Comparison Result: Target={t_score} vs Competitor={c_score}")
        await page.screenshot(path="ui_drawer_competitor.png")
        print("Captured ui_drawer_competitor.png")

        await browser.close()

        if console_errors:
            print(f"WARNING: Console errors detected: {console_errors}")
        else:
            print("SUCCESS: 0 console errors detected across all flows!")

if __name__ == "__main__":
    asyncio.run(verify_ui())
