"""Playwright UI verification script for AEOForge Studio (De-Slopified Edition)."""

import asyncio
from playwright.async_api import async_playwright

async def verify_ui():
    console_errors = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1600, "height": 1050}, accept_downloads=True)
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

        # Capture initial de-slopified state
        await page.screenshot(path="ui_deslopified_initial.png")
        print("Captured ui_deslopified_initial.png")

        # 2. Trigger audit via Quick Benchmark Preset button
        print("2. Clicking 'docs.python.org' benchmark preset...")
        await page.click("button:has-text('docs.python.org')")

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

        # Verify Grounded Marks & Test Interactive Cross-Highlighting
        marks_rows = await page.query_selector_all("#interactiveMarksScroll > div")
        print(f"Grounded Marks count in UI: {len(marks_rows)}")
        assert len(marks_rows) > 0, "Should list grounded interactive marks"

        # Hover first grounded mark and verify pin appears
        await marks_rows[0].hover()
        await page.wait_for_timeout(300)
        pin_hidden = await page.evaluate("() => document.getElementById('coordinateHighlightPin').classList.contains('hidden')")
        print(f"Coordinate pin visible on hover: {not pin_hidden}")
        assert not pin_hidden, "Coordinate pin should become visible on hovering landmark row"

        # Capture Audited UI view
        await page.screenshot(path="ui_deslopified_audited.png")
        print("Captured ui_deslopified_audited.png")

        # 3. Test Handshake Tabs (Cloudflare WAF, agent-spec, llms.txt)
        print("3. Testing Cloudflare WAF Rules Tab...")
        await page.click("#hTab-waf_rules")
        await page.wait_for_timeout(300)
        waf_text = await page.inner_text("#wafCodeView")
        print(f"Cloudflare WAF Rule Sample: {waf_text[:80]}...")
        assert "cf.client.bot" in waf_text

        print("Testing agent-spec.json tab...")
        await page.click("#hTab-agent_spec")
        await page.wait_for_timeout(200)
        spec_text = await page.inner_text("#handshakeCodeView")
        assert "schema" in spec_text or "domain" in spec_text

        # 4. Test Export Bundle .zip download
        print("4. Testing Export Bundle download button...")
        async with page.expect_download(timeout=10000) as download_info:
            await page.click("button:has-text('Export Bundle')")
        download = await download_info.value
        download_path = await download.path()
        print(f"Successfully downloaded bundle: {download.suggested_filename} at {download_path}")
        assert "bundle.zip" in download.suggested_filename

        # 5. Test Competitor Outranking Drawer
        print("5. Testing Competitor Outranking Lab Drawer...")
        await page.click("button:has-text('Competitor Lab')")
        await page.wait_for_selector("#compareDrawer:not(.hidden)")
        await page.fill("#compareTargetInput", "example.com")
        await page.fill("#compareCompetitorInput", "iana.org")
        await page.click("#compareSubmitBtn")

        await page.wait_for_selector("#compareResults:not(.hidden)", timeout=45000)
        target_score = await page.inner_text("#compareTargetScore")
        comp_score = await page.inner_text("#compareCompetitorScore")
        print(f"Competitor Result: Target={target_score} vs Competitor={comp_score}")

        await page.screenshot(path="ui_deslopified_competitor.png")
        print("Captured ui_deslopified_competitor.png")

        print(f"Console Errors: {console_errors}")
        assert len(console_errors) == 0, f"Found console errors: {console_errors}"
        print("SUCCESS: 0 console errors detected across all flows!")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(verify_ui())
