"""Navigation trap and modal overlay detector for autonomous web agents.
Inspired by Skyvern (https://github.com/Skyvern-AI/skyvern) and Stagehand.
"""

from typing import Dict, Any, List


KNOWN_TRAP_SIGNATURES = [
    {
        "name": "OneTrust Cookie Consent",
        "selectors": ["#onetrust-banner-sdk", "#onetrust-consent-sdk", ".onetrust-pc-dark-filter"],
        "dismiss_selectors": ["#onetrust-accept-btn-handler", "#onetrust-reject-all-handler"],
        "category": "cookie_consent",
        "severity": "critical"
    },
    {
        "name": "Cookiebot Consent Dialog",
        "selectors": ["#CybotCookiebotDialog", "#CybotCookiebotDialogBody"],
        "dismiss_selectors": ["#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll", "#CybotCookiebotDialogBodyButtonAccept"],
        "category": "cookie_consent",
        "severity": "critical"
    },
    {
        "name": "Klaro Consent Manager",
        "selectors": [".klaro .cookie-modal", ".klaro .cookie-notice"],
        "dismiss_selectors": [".klaro .cm-btn-accept", ".klaro .cm-btn-accept-all"],
        "category": "cookie_consent",
        "severity": "critical"
    },
    {
        "name": "Didomi Consent Notice",
        "selectors": ["#didomi-host", "#didomi-notice"],
        "dismiss_selectors": ["#didomi-notice-agree-button"],
        "category": "cookie_consent",
        "severity": "critical"
    },
    {
        "name": "Generic Fullscreen Overlay Modal",
        "selectors": ["[aria-modal='true']", "dialog[open]", ".modal.show", ".modal.is-active"],
        "dismiss_selectors": ["button[aria-label*='close' i]", "button[class*='close' i]", ".modal-close", ".btn-close"],
        "category": "modal_overlay",
        "severity": "high"
    }
]


async def detect_navigation_traps(page) -> List[Dict[str, Any]]:
    """Scan the rendered DOM for active modal overlays, cookie walls, and agent blockers."""
    detected_traps: List[Dict[str, Any]] = []

    # 1. Check known signature selectors
    for sig in KNOWN_TRAP_SIGNATURES:
        for sel in sig["selectors"]:
            try:
                elem = await page.query_selector(sel)
                if elem:
                    is_visible = await elem.is_visible()
                    if is_visible:
                        # Find candidate dismiss button
                        dismiss_sel_found = None
                        for d_sel in sig["dismiss_selectors"]:
                            d_elem = await page.query_selector(d_sel)
                            if d_elem and await d_elem.is_visible():
                                dismiss_sel_found = d_sel
                                break

                        detected_traps.append({
                            "name": sig["name"],
                            "category": sig["category"],
                            "severity": sig["severity"],
                            "active_selector": sel,
                            "dismiss_selector": dismiss_sel_found,
                            "recommendation": f"Add an automated pre-interaction dismissal using '{dismiss_sel_found or sel}'."
                        })
                        break
            except Exception:
                continue

    # 2. Heuristic check: Generic fixed/sticky full-viewport overlays
    try:
        heuristic_traps = await page.evaluate("""() => {
            const traps = [];
            const elements = document.querySelectorAll('div, section, aside, dialog');
            const vw = window.innerWidth;
            const vh = window.innerHeight;

            for (const el of elements) {
                const style = window.getComputedStyle(el);
                if (style.position === 'fixed' || style.position === 'absolute') {
                    const z = parseInt(style.zIndex, 10);
                    if (z >= 999) {
                        const rect = el.getBoundingClientRect();
                        // Covers more than 50% of the viewport width and height
                        if (rect.width >= vw * 0.5 && rect.height >= vh * 0.5) {
                            // Find any button inside
                            const btn = el.querySelector('button, a[role="button"], input[type="submit"]');
                            const btnText = btn ? btn.innerText.trim().slice(0, 30) : null;
                            traps.push({
                                tagName: el.tagName.toLowerCase(),
                                id: el.id ? '#' + el.id : null,
                                className: el.className ? '.' + el.className.toString().split(' ').join('.') : null,
                                zIndex: z,
                                candidateButtonText: btnText
                            });
                        }
                    }
                }
            }
            return traps.slice(0, 3);
        }""")

        for ht in heuristic_traps:
            # Check if not already matched
            sel = ht["id"] or ht["className"] or ht["tagName"]
            if not any(t["active_selector"] == sel for t in detected_traps):
                detected_traps.append({
                    "name": "High Z-Index Viewport Overlay",
                    "category": "viewport_obstruction",
                    "severity": "medium",
                    "active_selector": sel,
                    "dismiss_selector": f"{sel} button" if ht["candidateButtonText"] else None,
                    "recommendation": f"Ensure overlay at '{sel}' doesn't hijack click events or obscure primary content."
                })
    except Exception:
        pass

    return detected_traps
