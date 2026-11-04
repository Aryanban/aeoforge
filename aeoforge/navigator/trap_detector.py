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
    },
    {
        "name": "Cloudflare Turnstile Challenge",
        "selectors": ["iframe[src*='challenges.cloudflare.com']", ".cf-turnstile", "#cf-turnstile-wrapper"],
        "dismiss_selectors": [],
        "category": "bot_challenge",
        "severity": "critical"
    },
    {
        "name": "Google reCAPTCHA Challenge",
        "selectors": ["iframe[src*='google.com/recaptcha']", ".g-recaptcha"],
        "dismiss_selectors": [],
        "category": "bot_challenge",
        "severity": "critical"
    },
    {
        "name": "hCaptcha Challenge",
        "selectors": ["iframe[src*='hcaptcha.com']", ".h-captcha"],
        "dismiss_selectors": [],
        "category": "bot_challenge",
        "severity": "critical"
    },
    {
        "name": "Cloudflare WAF Access Block",
        "selectors": ["#cf-error-details", ".cf-error-overview", "#challenge-error-text"],
        "dismiss_selectors": [],
        "category": "firewall_block",
        "severity": "critical"
    },
    {
        "name": "Vercel Security Checkpoint",
        "selectors": ["#vercel-challenge", "[data-vercel-challenge]"],
        "dismiss_selectors": [],
        "category": "firewall_block",
        "severity": "critical"
    }
]


# Unified single-pass browser DOM evaluator for instant sub-3ms trap detection
TRAP_EVALUATION_SCRIPT = """
(signatures) => {
    const detected = [];
    const isVisible = (el) => {
        if (!el) return false;
        const style = window.getComputedStyle(el);
        if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') return false;
        const rect = el.getBoundingClientRect();
        return rect.width > 0 && rect.height > 0;
    };

    // 1. Check known signatures in a single loop
    for (const sig of signatures) {
        for (const sel of sig.selectors) {
            try {
                const el = document.querySelector(sel);
                if (el && isVisible(el)) {
                    let dismissFound = null;
                    for (const dSel of sig.dismiss_selectors) {
                        try {
                            const dEl = document.querySelector(dSel);
                            if (dEl && isVisible(dEl)) {
                                dismissFound = dSel;
                                break;
                            }
                        } catch (e) {}
                    }
                    detected.push({
                        name: sig.name,
                        category: sig.category,
                        severity: sig.severity,
                        active_selector: sel,
                        dismiss_selector: dismissFound,
                        recommendation: dismissFound 
                            ? `Add an automated pre-interaction dismissal using '${dismissFound}'.`
                            : `Add an automated pre-interaction dismissal using '${sel}'.`
                    });
                    break;
                }
            } catch (e) {}
        }
    }

    // 2. High Z-Index Viewport Overlay Heuristic
    try {
        const elements = document.querySelectorAll('div, section, aside, dialog');
        const vw = window.innerWidth;
        const vh = window.innerHeight;

        for (const el of elements) {
            const style = window.getComputedStyle(el);
            if (style.position === 'fixed' || style.position === 'absolute') {
                const z = parseInt(style.zIndex, 10);
                if (z >= 999) {
                    const rect = el.getBoundingClientRect();
                    if (rect.width >= vw * 0.5 && rect.height >= vh * 0.5 && isVisible(el)) {
                        const sel = el.id ? '#' + el.id : (el.className ? '.' + el.className.toString().trim().split(/\\s+/).join('.') : el.tagName.toLowerCase());
                        if (!detected.some(t => t.active_selector === sel)) {
                            const btn = el.querySelector('button, a[role="button"], input[type="submit"]');
                            detected.push({
                                name: "High Z-Index Viewport Overlay",
                                category: "viewport_obstruction",
                                severity: "medium",
                                active_selector: sel,
                                dismiss_selector: btn ? `${sel} button` : null,
                                recommendation: `Ensure overlay at '${sel}' does not hijack click events or obscure primary content.`
                            });
                        }
                    }
                }
            }
        }
    } catch (e) {}

    return detected;
}
"""


async def detect_navigation_traps(page) -> List[Dict[str, Any]]:
    """Scan the rendered DOM for active modal overlays, cookie walls, and agent blockers in a single batch pass."""
    detected_traps: List[Dict[str, Any]] = []

    # 0. Check page title for WAF challenges
    try:
        title = await page.title()
        if "Attention Required! | Cloudflare" in title or "Just a moment..." in title:
            detected_traps.append({
                "name": "Cloudflare Bot Management Challenge",
                "category": "firewall_block",
                "severity": "critical",
                "active_selector": "html",
                "dismiss_selector": None,
                "recommendation": "Configure Cloudflare WAF: Enable 'Allow Verified AI Bots' under Security -> Bots."
            })
        elif "Vercel Security Checkpoint" in title:
            detected_traps.append({
                "name": "Vercel Security Checkpoint Block",
                "category": "firewall_block",
                "severity": "critical",
                "active_selector": "html",
                "dismiss_selector": None,
                "recommendation": "Configure Vercel Firewall: Whitelist AI crawler user-agents or publish static /llms.txt."
            })
    except Exception:
        pass

    # 1 & 2. Execute single-trip batch evaluation
    try:
        dom_traps = await page.evaluate(TRAP_EVALUATION_SCRIPT, KNOWN_TRAP_SIGNATURES)
        if dom_traps:
            detected_traps.extend(dom_traps)
    except Exception:
        pass

    return detected_traps
