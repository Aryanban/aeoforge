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

        # Close compare drawer
        await page.keyboard.press("Escape")
        await page.wait_for_selector("#compareDrawer", state="hidden")

        # 7. Test Theme Switcher (Dark -> Light -> System -> Dark)
        print("7. Testing Theme Switcher...")
        await page.click("#themeBtn-light")
        await page.wait_for_timeout(200)
        is_light = await page.evaluate("() => !document.documentElement.classList.contains('dark') && document.documentElement.getAttribute('data-theme') === 'light'")
        assert is_light, "Light theme should remove .dark class and set data-theme='light'"
        print("✓ Switched to Light Theme successfully")

        await page.click("#themeBtn-dark")
        await page.wait_for_timeout(200)
        is_dark = await page.evaluate("() => document.documentElement.classList.contains('dark') && document.documentElement.getAttribute('data-theme') === 'dark'")
        assert is_dark, "Dark theme should add .dark class and set data-theme='dark'"
        print("✓ Switched back to Dark Theme successfully")

        await page.click("#themeBtn-system")
        await page.wait_for_timeout(200)
        system_stored = await page.evaluate("() => localStorage.getItem('aeoforge-theme') === 'system'")
        assert system_stored, "System theme preference should be stored in localStorage"
        print("✓ System Theme preference set successfully")

        # Switch back to dark for standard look
        await page.click("#themeBtn-dark")

        # 8. Test Accessibility (WCAG 2.1 AA Skip Link & Reduced Motion)
        print("8. Testing Accessibility Features...")
        skip_href = await page.get_attribute(".skip-to-content-link", "href")
        assert skip_href == "#mainWorkspace", "Skip link must point to #mainWorkspace"
        
        await page.focus(".skip-to-content-link")
        is_focused = await page.evaluate("() => document.activeElement.classList.contains('skip-to-content-link')")
        assert is_focused, "Skip link must be keyboard focusable"
        print("✓ WCAG Skip to Main Content link verified")

        # Test Reduced Motion toggle in Preferences modal
        await page.click("#engineStatusBadge")
        await page.wait_for_selector("#modelSettingsModal:not(.hidden)")
        await page.click("#mTab-preferences")
        await page.wait_for_selector("#mView-preferences:not(.hidden)")

        await page.check("#reduceMotionToggle")
        has_reduced_motion = await page.evaluate("() => document.documentElement.classList.contains('reduce-motion')")
        assert has_reduced_motion, "Enabling reduceMotionToggle should add .reduce-motion to html"
        print("✓ Reduced motion toggle activated")

        await page.uncheck("#reduceMotionToggle")
        no_reduced_motion = await page.evaluate("() => !document.documentElement.classList.contains('reduce-motion')")
        assert no_reduced_motion, "Disabling reduceMotionToggle should remove .reduce-motion from html"
        print("✓ Reduced motion toggle deactivated")

        await page.keyboard.press("Escape")
        await page.wait_for_selector("#modelSettingsModal", state="hidden")

        # 9. Test Persistent History Drawer & Progression Lab
        print("9. Testing Persistent History Drawer & Progression Lab...")
        await page.click("#historyDrawerBtn")
        await page.wait_for_selector("#historyDrawer:not(.hidden)")
        await page.wait_for_timeout(300)

        history_items = await page.query_selector_all("#historyListContainer > div")
        print(f"Historical audit records found in SQLite: {len(history_items)}")
        assert len(history_items) > 0, "Persistent SQLite history must display recorded audits"

        # Check domain progression card
        prog_visible = await page.is_visible("#historyProgressionCard")
        print(f"Domain progression card visible: {prog_visible}")

        # Close history drawer
        await page.keyboard.press("Escape")
        await page.wait_for_selector("#historyDrawer", state="hidden")

        # 10. Test Technical Setup & In-UI Codebase AST Patcher
        print("10. Testing Technical Setup & In-UI Codebase AST Patcher...")
        await page.click("#technicalSetupBtn")
        await page.wait_for_selector("#modelSettingsModal:not(.hidden)")
        
        # Switch to Patcher tab
        await page.click("#mTab-patcher")
        await page.wait_for_selector("#mView-patcher:not(.hidden)")

        # Run In-UI Patch
        await page.click("#runPatchBtn")
        await page.wait_for_selector("#patchExecutionOutput:has-text('Successful')", timeout=10000)
        patch_text = await page.inner_text("#patchExecutionOutput")
        print(f"Codebase Patch Output: {patch_text[:80]}...")
        assert "Successful" in patch_text

        # Switch to Crawler & Anti-Block tab
        await page.click("#mTab-crawler")
        await page.wait_for_selector("#mView-crawler:not(.hidden)")
        print("✓ Crawler & Anti-Block settings view verified")

        await page.keyboard.press("Escape")
        await page.wait_for_selector("#modelSettingsModal", state="hidden")

        print(f"Console Errors: {console_errors}")
        assert len(console_errors) == 0, f"Found console errors: {console_errors}"
        print("SUCCESS: 0 console errors detected across all flows!")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(verify_ui())
