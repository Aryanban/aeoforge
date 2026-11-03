"""Pillar B: Agent Navigability, Token Efficiency & Trap Avoidance (25 Points Max).
Evaluates how smoothly autonomous AI agents can parse and interact with the page.
"""

from typing import Dict, Any, List
from bs4 import BeautifulSoup


def score_navigability(
    html: str,
    raw_html_tokens: int,
    text_tokens: int,
    traps: List[Dict[str, Any]],
    interactive_marks: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Score page on agent navigability, token bloat, and affordance clarity (0 - 25 points)."""
    score = 0.0
    feedback = []

    soup = BeautifulSoup(html, "html.parser")

    # 1. DOM Token Efficiency & Content Ratio (0 - 8 pts)
    # Token ratio = text_tokens / raw_html_tokens
    token_ratio = text_tokens / max(1, raw_html_tokens)
    if token_ratio >= 0.15:
        score += 8.0
        feedback.append(f"High token efficiency ({round(token_ratio * 100, 1)}% text-to-DOM). Minimal LLM context waste.")
    elif token_ratio >= 0.05:
        score += 5.0
        feedback.append(f"Moderate token efficiency ({round(token_ratio * 100, 1)}% text-to-DOM).")
    else:
        score += 2.0
        feedback.append(f"Heavy DOM bloat ({round(token_ratio * 100, 1)}% text-to-DOM). Raw HTML consumes excessive agent context.")

    # 2. Semantic Landmarks & Structure (0 - 7 pts)
    landmark_score = 0.0
    if soup.find("main") or soup.find(attrs={"role": "main"}):
        landmark_score += 2.5
    if soup.find("nav") or soup.find(attrs={"role": "navigation"}):
        landmark_score += 1.5
    if soup.find("article"):
        landmark_score += 1.5
    if soup.find("h1"):
        landmark_score += 1.5

    score += landmark_score
    if landmark_score >= 5.5:
        feedback.append("Excellent semantic landmarks (<main>, <nav>, <article>, <h1>).")
    else:
        feedback.append("Missing standard ARIA/<main> landmarks, making DOM traversal ambiguous for agents.")

    # 3. Interactive Affordance Labeling (0 - 6 pts)
    # Check how many interactive marks have accessible names vs empty
    if interactive_marks:
        labelled = sum(1 for m in interactive_marks if m.get("name") and len(m["name"].strip()) > 1)
        label_ratio = labelled / len(interactive_marks)
        if label_ratio >= 0.85:
            score += 6.0
            feedback.append(f"High interactive labeling ({round(label_ratio * 100)}% of buttons/links have accessible names).")
        elif label_ratio >= 0.6:
            score += 4.0
            feedback.append(f"Moderate interactive labeling ({round(label_ratio * 100)}% labelled).")
        else:
            score += 2.0
            feedback.append(f"Poor interactive labeling ({round(label_ratio * 100)}% labelled). Anonymous buttons/links confuse visual agents.")
    else:
        score += 3.0

    # 4. Absence of Navigation Traps & Modal Blockers (0 - 4 pts)
    trap_penalty = sum(2.0 if t.get("severity") == "critical" else 1.0 for t in traps)
    trap_score = max(0.0, 4.0 - trap_penalty)
    score += trap_score

    if not traps:
        feedback.append("Zero navigation traps or modal overlays detected.")
    else:
        for t in traps:
            feedback.append(f"Blocker detected: {t['name']} ({t['severity']}). Causes agent navigation loops.")

    return {
        "pillar": "Pillar B: Agent Navigability & Token Cost",
        "score": round(min(25.0, score), 1),
        "max_score": 25.0,
        "details": {
            "token_ratio_pct": round(token_ratio * 100, 2),
            "raw_html_tokens": raw_html_tokens,
            "text_tokens": text_tokens,
            "traps_detected_count": len(traps),
            "interactive_elements_count": len(interactive_marks)
        },
        "feedback": feedback
    }
