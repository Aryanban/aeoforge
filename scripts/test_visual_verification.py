"""
Visual Verification Script for AEOForge New Capabilities:
- Full Rendering of Visual Agent Perception (No white screen on SPAs like Cerebral Valley)
- Clickable Pillar Drilldown Drawer with Point Deductions & Reasons
- Custom URL List Batch Audit Matrix
- High Crawler BFS Limit
"""

import asyncio
import os
from playwright.async_api import async_playwright

SCREENSHOTS_DIR = "/Users/aryanbansal/.gemini/antigravity/brain/23a05fa8-37e4-4796-8231-43578f60c020"

async def run_verification():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1440, "height": 960})
        page = await context.new_page()

        errors = []
        page.on("pageerror", lambda err: errors.append(f"PageError: {err}"))
        page.on("console", lambda msg: errors.append(f"ConsoleError: {msg.text}") if msg.type == "error" else None)

        print("1. Loading AEOForge Studio at http://127.0.0.1:8000...")
        await page.goto("http://127.0.0.1:8000", wait_until="networkidle")

        # 2. Test Audit on Cerebral Valley AI
        print("2. Auditing https://cerebralvalley.ai...")
        await page.fill("#targetUrlInput", "https://cerebralvalley.ai")
        await page.click("#auditSubmitBtn")

        # Wait for audit results to complete
        await page.wait_for_selector("#scoreDisplay:not(:has-text('--'))", timeout=45000)
        await page.wait_for_timeout(1000)

        score = await page.inner_text("#scoreDisplay")
        grade = await page.inner_text("#gradeBadge")
        print(f"Audited cerebralvalley.ai Score: {score} / 100 (Grade: {grade})")

        # Verify Visual Agent Perception Canvas is NOT blank
        shot_img = page.locator("#screenshotImg")
        is_visible = await shot_img.is_visible()
        src = await shot_img.get_attribute("src")
        print(f"Set-of-Mark Screenshot Rendered: {is_visible}, src length: {len(src) if src else 0}")
        assert is_visible, "Screenshot image must be visible!"
        assert src and len(src) > 5000, "Screenshot image must not be empty base64!"

        # Capture Set-of-Mark Perception Canvas Screenshot
        await shot_img.screenshot(path=os.path.join(SCREENSHOTS_DIR, "verified_som_perception_canvas.png"))
        print("✓ Verified Visual Perception Canvas captured: verified_som_perception_canvas.png")

        # 3. Test Clicking on Pillar A (Citability)
        print("3. Clicking Pillar A (Citability) to open drilldown drawer...")
        pillar_a = page.locator("#scorePillarA").locator("xpath=..").locator("xpath=..")
        await pillar_a.click()
        await page.wait_for_selector("#pillarDrilldownDrawer:not(.hidden)", timeout=5000)
        await page.wait_for_timeout(500)

        drawer_title = await page.inner_text("#drilldownTitle")
        drawer_lost = await page.inner_text("#drilldownPointsLostBadge")
        print(f"Drilldown Drawer Open: '{drawer_title}', Lost: '{drawer_lost}'")
        assert "Citability" in drawer_title

        # Capture Pillar A Drawer Screenshot
        drawer_box = page.locator("#pillarDrilldownDrawer > div.absolute.right-0")
        await drawer_box.screenshot(path=os.path.join(SCREENSHOTS_DIR, "verified_citability_drilldown_drawer.png"))
        print("✓ Captured Citability Drilldown: verified_citability_drilldown_drawer.png")

        # Test switching tab to Overall Loss & Roadmap to 100 inside drawer
        print("4. Switching to 'Overall Loss' tab inside drawer...")
        await page.click("#dTab-overall")
        await page.wait_for_timeout(400)
        overall_title = await page.inner_text("#drilldownTitle")
        print(f"Drilldown View: '{overall_title}'")
        assert "Sitewide AEO Loss" in overall_title

        await drawer_box.screenshot(path=os.path.join(SCREENSHOTS_DIR, "verified_overall_loss_drilldown.png"))
        print("✓ Captured Overall Loss Drilldown: verified_overall_loss_drilldown.png")

        # Close drilldown drawer
        await page.click("#pillarDrilldownDrawer button[onclick='closePillarDrilldown()']")
        await page.wait_for_selector("#pillarDrilldownDrawer", state="hidden", timeout=5000)
        print("✓ Closed drilldown drawer.")

        # 4. Test Custom URL List Mode
        print("5. Testing Custom URL List Mode...")
        await page.click("#modeBtn-batch")
        await page.wait_for_selector("#batchAuditForm:not(.hidden)", timeout=5000)

        # Pre-fill custom URLs
        urls_to_test = "https://cerebralvalley.ai\nhttps://docs.python.org/3/tutorial/\nhttps://example.com"
        await page.fill("#batchUrlsTextarea", urls_to_test)
        print("Submitting batch custom URL list scoring...")
        await page.click("#batchAuditSubmitBtn")

        # Wait for batch results matrix
        await page.wait_for_selector("#batchResultsCard:not(.hidden)", timeout=60000)
        await page.wait_for_timeout(1000)

        avg_score = await page.inner_text("#batchAvgScoreDisplay")
        avg_grade = await page.inner_text("#batchAvgGradeBadge")
        print(f"Batch Custom URLs Averaged: {avg_score} / 100 ({avg_grade})")

        rows = await page.locator("#batchResultsTbody tr").count()
        print(f"Batch Matrix Rows Count: {rows}")
        assert rows == 3, f"Expected 3 rows, found {rows}"

        # Capture Custom URL List Matrix Screenshot
        batch_card = page.locator("#batchResultsCard")
        await batch_card.screenshot(path=os.path.join(SCREENSHOTS_DIR, "verified_batch_url_matrix.png"))
        print("✓ Captured Custom URL Matrix: verified_batch_url_matrix.png")

        # 5. Check Crawler BFS Max Limit
        print("6. Verifying Sitewide Crawler Max Limit...")
        await page.evaluate("() => toggleDrawer('crawlerDrawer')")
        await page.wait_for_selector("#crawlerDrawer:not(.hidden)", timeout=5000)
        max_limit = await page.get_attribute("#crawlMaxPagesInput", "max")
        print(f"Sitewide Crawler Input max attribute: {max_limit}")
        assert max_limit == "1000", f"Expected max=1000, got {max_limit}"
        await page.evaluate("() => toggleDrawer('crawlerDrawer')")

        # Check for any console errors
        print(f"Console errors during execution: {errors}")
        assert len(errors) == 0, f"Found console errors: {errors}"
        print("\n==========================================")
        print("ALL VISUAL & FUNCTIONAL CHECKS PASSED 100%!")
        print("==========================================")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_verification())
