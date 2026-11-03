"""Set-of-Mark (SoM) visual coordinate grounding and DOM accessibility tree extraction.
Inspired by browser-use (https://github.com/browser-use/browser-use) and Microsoft OmniParser.
"""

from typing import Dict, Any, List, Tuple


# Injected JavaScript that identifies interactive elements, computes bounding boxes,
# and returns a pruned semantic interactive tree.
SOM_EXTRACTION_SCRIPT = """
() => {
    const interactiveTags = new Set(['a', 'button', 'input', 'select', 'textarea', 'details', 'summary']);
    const interactiveRoles = new Set(['button', 'link', 'checkbox', 'radio', 'combobox', 'tab', 'menuitem', 'searchbox']);
    
    const elements = document.querySelectorAll('*');
    const marks = [];
    let markId = 1;

    for (const el of elements) {
        // Skip script, style, noscript, svg internal nodes
        const tag = el.tagName.toLowerCase();
        if (['script', 'style', 'noscript', 'meta', 'link', 'head'].includes(tag)) continue;

        const role = el.getAttribute('role');
        const isInteractive = interactiveTags.has(tag) || 
                              (role && interactiveRoles.has(role)) || 
                              el.hasAttribute('onclick') || 
                              el.getAttribute('tabindex') === '0' ||
                              el.isContentEditable;

        if (!isInteractive) continue;

        // Check visibility and dimensions
        const style = window.getComputedStyle(el);
        if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') continue;

        const rect = el.getBoundingClientRect();
        if (rect.width <= 4 || rect.height <= 4) continue;
        if (rect.bottom < 0 || rect.top > window.innerHeight * 2) continue; // Out of immediate scroll window

        // Determine accessible name
        let name = el.getAttribute('aria-label') || 
                   el.getAttribute('title') || 
                   el.getAttribute('placeholder') || 
                   el.innerText || 
                   el.getAttribute('alt') || '';
        name = name.replace(/\\s+/g, ' ').trim().slice(0, 80);

        marks.push({
            id: markId++,
            tag: tag,
            role: role || tag,
            name: name,
            href: el.getAttribute('href') || null,
            rect: {
                x: Math.round(rect.left),
                y: Math.round(rect.top),
                width: Math.round(rect.width),
                height: Math.round(rect.height)
            }
        });

        if (marks.length >= 100) break; // Limit to 100 interactive elements to fit context limits
    }

    return marks;
}
"""

# Injected JavaScript to draw visible Set-of-Mark badges on the page before screenshot
SOM_INJECT_BADGES_SCRIPT = """
(marks) => {
    // Remove any previous badges
    const existing = document.getElementById('aeoforge-som-container');
    if (existing) existing.remove();

    const container = document.createElement('div');
    container.id = 'aeoforge-som-container';
    container.style.position = 'absolute';
    container.style.top = '0';
    container.style.left = '0';
    container.style.width = '100%';
    container.style.height = '100%';
    container.style.pointerEvents = 'none';
    container.style.zIndex = '999999';

    for (const m of marks) {
        const badge = document.createElement('div');
        badge.innerText = m.id;
        badge.style.position = 'fixed';
        badge.style.left = (m.rect.x) + 'px';
        badge.style.top = (m.rect.y) + 'px';
        badge.style.backgroundColor = '#e11d48';
        badge.style.color = '#ffffff';
        badge.style.fontSize = '10px';
        badge.style.fontWeight = 'bold';
        badge.style.fontFamily = 'monospace';
        badge.style.padding = '1px 3px';
        badge.style.borderRadius = '3px';
        badge.style.border = '1px solid #ffffff';
        badge.style.boxShadow = '0 1px 3px rgba(0,0,0,0.5)';
        badge.style.pointerEvents = 'none';

        // Add outline box
        const outline = document.createElement('div');
        outline.style.position = 'fixed';
        outline.style.left = m.rect.x + 'px';
        outline.style.top = m.rect.y + 'px';
        outline.style.width = m.rect.width + 'px';
        outline.style.height = m.rect.height + 'px';
        outline.style.border = '1px solid #e11d48';
        outline.style.pointerEvents = 'none';

        container.appendChild(outline);
        container.appendChild(badge);
    }

    document.body.appendChild(container);
}
"""

# Script to remove badges after screenshot
SOM_REMOVE_BADGES_SCRIPT = """
() => {
    const existing = document.getElementById('aeoforge-som-container');
    if (existing) existing.remove();
}
"""


async def extract_interactive_marks(page) -> List[Dict[str, Any]]:
    """Extract interactive element bounding boxes and labels."""
    try:
        marks = await page.evaluate(SOM_EXTRACTION_SCRIPT)
        return marks
    except Exception:
        return []


async def inject_som_badges(page, marks: List[Dict[str, Any]]):
    """Superimpose visual bounding box badges on the page."""
    try:
        await page.evaluate(SOM_INJECT_BADGES_SCRIPT, marks)
    except Exception:
        pass


async def remove_som_badges(page):
    """Clean up superimposed badges from DOM."""
    try:
        await page.evaluate(SOM_REMOVE_BADGES_SCRIPT)
    except Exception:
        pass


def build_a11y_tree_representation(marks: List[Dict[str, Any]]) -> str:
    """Format interactive marks into a concise token-efficient string representation for LLMs."""
    lines = ["Accessibility Interactive Tree (Set-of-Mark):"]
    for m in marks:
        name_part = f" \"{m['name']}\"" if m['name'] else " (No Label)"
        href_part = f" -> {m['href']}" if m.get('href') else ""
        lines.append(f"[{m['id']}] <{m['role']}>{name_part}{href_part} at ({m['rect']['x']},{m['rect']['y']})")
    return "\n".join(lines)
