"""Pillar A: Citability, Answerability & Fact-Triplet Scoring (25 Points Max).
Evaluates suitability for AI answer engines (Meta AI, Perplexity, Google AI Overviews).
"""

import re
from typing import Dict, Any
from bs4 import BeautifulSoup


def score_citability(html: str, text: str) -> Dict[str, Any]:
    """Score page on AI citability and fact-density (0 - 25 points)."""
    score = 0.0
    feedback = []

    soup = BeautifulSoup(html, "html.parser")

    # 1. Direct Definition & Answer Capsule Detection (0 - 10 pts)
    # Check paragraphs immediately following H2 or H3
    headings = soup.find_all(["h1", "h2", "h3"])
    capsule_found = False
    for h in headings:
        next_sibling = h.find_next_sibling()
        if next_sibling and next_sibling.name == "p":
            words = next_sibling.get_text().strip().split()
            # Optimal answer snippet length is 35 to 65 words
            if 35 <= len(words) <= 65:
                capsule_found = True
                break

    if capsule_found:
        score += 10.0
        feedback.append("Direct answer capsule detected under heading (35-65 words). Optimal for AI Overviews.")
    else:
        score += 4.0
        feedback.append("Missing concise (35-65 word) answer capsules under headings.")

    # 2. Fact-Triplet Density (<Subject, Predicate, Object>) (0 - 8 pts)
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if len(s.strip()) > 20]
    # Simple POS/relation pattern matching for factual assertions
    fact_indicators = [" is ", " are ", " was ", " were ", " defines ", " enables ", " provides ", " includes ", " consists of "]
    fact_sentences = [s for s in sentences if any(ind in s.lower() for ind in fact_indicators)]
    density = len(fact_sentences) / max(1, len(sentences))

    if density >= 0.4:
        score += 8.0
        feedback.append(f"High factual statement density ({round(density * 100)}%).")
    elif density >= 0.2:
        score += 5.0
        feedback.append(f"Moderate factual statement density ({round(density * 100)}%).")
    else:
        score += 2.0
        feedback.append("Low factual statement density. Consider rephrasing with clear Subject-Predicate-Object clauses.")

    # 3. E-E-A-T & Authority Signals (0 - 7 pts)
    eeat_score = 0.0
    # Authorship
    if soup.find(attrs={"rel": "author"}) or soup.find(class_=re.compile(r"author", re.I)):
        eeat_score += 2.5
    # Publication Date
    if soup.find("time") or soup.find(attrs={"property": "article:published_time"}):
        eeat_score += 2.5
    # Sources / Citations
    if soup.find("cite") or soup.find(class_=re.compile(r"reference|citation", re.I)) or soup.find_all("blockquote"):
        eeat_score += 2.0

    score += eeat_score
    if eeat_score >= 5.0:
        feedback.append("Strong E-E-A-T provenance signals (author, date, citations).")
    else:
        feedback.append("Weak E-E-A-T signals. Add explicit author attribution and publication dates.")

    return {
        "pillar": "Pillar A: Citability & Answerability",
        "score": round(min(25.0, score), 1),
        "max_score": 25.0,
        "details": {
            "has_answer_capsule": capsule_found,
            "fact_density_pct": round(density * 100, 1),
            "eeat_score": round(eeat_score, 1)
        },
        "feedback": feedback
    }
