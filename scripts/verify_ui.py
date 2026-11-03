"""Playwright UI verification script for AEOForge Studio with Model Settings & Reactive Loading."""

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

        # 2. Test AI Model & Engine Settings Modal
        print("2. Testing AI Model & Engine Settings Modal...")
        await page.click("#engineStatusBadge")
        await page.wait_for_selector("#modelSettingsModal:not(.hidden)")
        
        # Verify local model options populated
        local_model_val = await page.input_value("#ollamaModelSelect")
        print(f"Selected Local Ollama Model: {local_model_val}")
        assert "llama" in local_model_val.lower()

        # Test model connection
        print("Testing engine connection ping...")
        await page.click("#testConnectionBtn")
        await page.wait_for_selector("#modelTestFeedback:has-text('Connected')", timeout=10000)
        feedback_text = await page.inner_text("#modelTestFeedback")
        print(f"Connection Feedback: {feedback_text}")
        assert "Connected successfully" in feedback_text or "latency" in feedback_text

        # Test switching to Cloud tab
        print("Testing Cloud API tab in modal...")
        await page.click("#mTab-cloud")
        cloud_visible = await page.is_visible("#mView-cloud")
        assert cloud_visible, "Cloud API view should be visible"

        # Close modal
        await page.click("button:has-text('Cancel')")
        await page.wait_for_selector("#modelSettingsModal", state="hidden")

        # 3. Test Multi-Step Reactive Loading during audit
        print("3. Triggering audit for 'docs.python.org' and testing reactive loading steps...")
        await page.click("button:has-text('docs.python.org')")
        
        # Verify loading indicator is active
        loading_active = await page.is_visible("#loadingIndicator")
        assert loading_active, "Loading indicator should be visible"

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

        # 4. Test Handshake Tabs (Cloudflare WAF, agent-spec, llms.txt)
        print("4. Testing Cloudflare WAF Rules Tab...")
        await page.click("#hTab-waf_rules")
        await page.wait_for_timeout(300)
        waf_text = await page.inner_text("#wafCodeView")
        assert "cf.client.bot" in waf_text

        # 5. Test Export Bundle .zip download
        print("5. Testing Export Bundle download button...")
        async with page.expect_download(timeout=10000) as download_info:
            await page.click("button:has-text('Export Bundle')")
        download = await download_info.value
        download_path = await download.path()
        print(f"Successfully downloaded bundle: {download.suggested_filename} at {download_path}")
        assert "bundle.zip" in download.suggested_filename

        # 6. Test Competitor Outranking Drawer
        print("6. Testing Competitor Outranking Lab Drawer...")
        await page.click("button:has-text('Competitor Lab')")
        await page.wait_for_selector("#compareDrawer:not(.hidden)")
        await page.fill("#compareTargetInput", "example.com")
        await page.fill("#compareCompetitorInput", "iana.org")
        await page.click("#compareSubmitBtn")

        await page.wait_for_selector("#compareResults:not(.hidden)", timeout=45000)
        target_score = await page.inner_text("#compareTargetScore")
        comp_score = await page.inner_text("#compareCompetitorScore")
        print(f"Competitor Result: Target={target_score} vs Competitor={comp_score}")

        print(f"Console Errors: {console_errors}")
        assert len(console_errors) == 0, f"Found console errors: {console_errors}"
        print("SUCCESS: 0 console errors detected across all flows!")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(verify_ui())
