"""Generator for the standardized Machine-to-Machine Agent Navigation Spec (agent-spec.json)."""

from datetime import datetime, timezone
from typing import Dict, Any, List
from urllib.parse import urlparse
from bs4 import BeautifulSoup


def generate_agent_spec(
    url: str,
    aeo_score: float,
    html: str,
    traps: List[Dict[str, Any]],
    interactive_marks: List[Dict[str, Any]],
    discovered_endpoints: List[str]
) -> Dict[str, Any]:
    """Synthesize a machine-executable Agent Navigation Spec."""
    parsed = urlparse(url)
    domain = parsed.netloc
    soup = BeautifulSoup(html, "html.parser")

    # Determine optimal primary content selector
    content_sel = "body"
    if soup.find("main", id=True):
        content_sel = f"main#{soup.find('main')['id']}"
    elif soup.find("main"):
        content_sel = "main"
    elif soup.find("article"):
        content_sel = "article"
    elif soup.find(attrs={"role": "main"}):
        content_sel = "[role='main']"

    # Identify search action
    search_info = None
    search_form = soup.find("form", attrs={"action": True})
    if search_form:
        search_input = search_form.find("input", attrs={"name": True})
        param_name = search_input["name"] if search_input else "q"
        search_info = {
            "endpoint": search_form["action"],
            "query_parameter": param_name,
            "fallback_selector": "input[type='search']"
        }

    # Filter navigation traps for agent pre-action bypass
    known_traps = []
    for t in traps:
        known_traps.append({
            "trap_type": t.get("category", "modal_overlay"),
            "trigger_selector": t.get("active_selector"),
            "dismiss_selector": t.get("dismiss_selector"),
            "recommended_action": "click" if t.get("dismiss_selector") else "escape_key"
        })

    # Curate high-value navigation targets from interactive marks
    high_value_actions = {}
    for m in interactive_marks[:20]:
        name_lower = (m.get("name") or "").lower()
        if "pricing" in name_lower and "pricing" not in high_value_actions:
            high_value_actions["pricing_link"] = m.get("href") or f"[{m['id']}]"
        elif "doc" in name_lower and "documentation" not in high_value_actions:
            high_value_actions["docs_link"] = m.get("href") or f"[{m['id']}]"
        elif "contact" in name_lower and "contact" not in high_value_actions:
            high_value_actions["contact_link"] = m.get("href") or f"[{m['id']}]"
        elif "login" in name_lower or "sign in" in name_lower and "auth" not in high_value_actions:
            high_value_actions["auth_link"] = m.get("href") or f"[{m['id']}]"

    return {
        "$schema": "https://aeoforge.dev/schemas/agent-spec-v1.json",
        "domain": domain,
        "entry_url": url,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "aeo_score": aeo_score,
        "agent_instructions": {
            "recommended_mode": "accessibility_tree",
            "primary_content_selector": content_sel,
            "token_budget_hint": f"Strip script and style tags. Target content length: ~{len(html) // 4} tokens.",
            "known_navigation_traps": known_traps,
            "action_map": {
                "search": search_info or {"fallback_selector": "input[type='search']"},
                "key_actions": high_value_actions
            },
            "direct_api_alternatives": [
                {"description": "Discovered endpoint", "url": ep} for ep in discovered_endpoints[:3]
            ]
        }
    }
