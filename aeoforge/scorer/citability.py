"""Pillar A: Citability, Answerability & Fact-Triplet Scoring (25 Points Max).
Evaluates suitability for AI answer engines (Meta AI, Perplexity, Google AI Overviews).
"""

import re
from typing import Dict, Any
from bs4 import BeautifulSoup

# Comprehensive factual predicate indicators for Subject-Predicate-Object triplets
FACT_VERB_INDICATORS = [
    " is ", " are ", " was ", " were ", " defines ", " enables ", " provides ", 
    " includes ", " consists of ", " produces ", " generates ", " features ", 
    " measures ", " reduces ", " operates ", " connects ", " contains ", 
    " supports ", " powers ", " delivers ", " manufactures ", " serves as "
]

# Numerical, statistical, and empirical claim pattern
NUMERICAL_CLAIM_PATTERN = re.compile(
    r"\b(\$|€|£|₹)?\d+([.,]\d+)?\s*(%|percent|km|kilometer|kilometers|mile|miles|sq\s*km|square\s*kilometers|gb|mb|ms|s|sec|tokens|users|customers|million|billion|trillion|x|pts)?\b",
    re.IGNORECASE
)


def score_citability(html: str, text: str) -> Dict[str, Any]:
    """Score page on AI citability and fact-density (0 - 25 points)."""
    score = 0.0
    feedback = []

    soup = BeautifulSoup(html, "html.parser")

    # 1. Direct Definition & Answer Capsule Detection (0 - 10 pts)
    # Check paragraphs immediately following H1, H2, H3 or structured definition blocks
    headings = soup.find_all(["h1", "h2", "h3"])
    capsule_found = False
    
    for h in headings:
        # Check direct sibling or container child
        target_p = None
        next_sibling = h.find_next_sibling()
        if next_sibling:
            if next_sibling.name == "p":
                target_p = next_sibling
            else:
                target_p = next_sibling.find("p")
        
        if not target_p and h.parent:
            target_p = h.parent.find("p")

        if target_p:
            words = target_p.get_text().strip().split()
            # Optimal answer snippet length is 30 to 70 words
            if 30 <= len(words) <= 70:
                capsule_found = True
                break

    # Also detect structured definition terms or FAQ summaries
    if not capsule_found:
        if soup.find("dt") and soup.find("dd"):
            capsule_found = True
        elif soup.find("details") and soup.find("summary"):
            capsule_found = True

    if capsule_found:
        score += 10.0
        feedback.append("Direct answer capsule detected under heading (30-70 words). Optimal for AI Overviews.")
    else:
        score += 4.0
        feedback.append("Missing concise (30-70 word) answer capsules under headings.")

    # 2. Fact-Triplet & Quantitative Assertion Density (0 - 8 pts)
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if len(s.strip()) > 15]
    fact_sentences = []
    
    for s in sentences:
        s_lower = f" {s.lower()} "
        has_predicate = any(ind in s_lower for ind in FACT_VERB_INDICATORS)
        has_empirical_claim = bool(NUMERICAL_CLAIM_PATTERN.search(s))
        if has_predicate or has_empirical_claim:
            fact_sentences.append(s)

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

    # 3. E-E-A-T & Provenance Signals (0 - 7 pts)
    eeat_score = 0.0
    # Authorship
    if soup.find(attrs={"rel": "author"}) or soup.find(class_=re.compile(r"author|byline", re.I)) or soup.find(attrs={"itemprop": "author"}):
        eeat_score += 2.5
    # Publication Date
    if soup.find("time") or soup.find(attrs={"property": "article:published_time"}) or soup.find(attrs={"name": "publish-date"}):
        eeat_score += 2.5
    # Sources / Citations / Footnotes
    if soup.find("cite") or soup.find(class_=re.compile(r"reference|citation|footnote", re.I)) or soup.find_all("blockquote"):
        eeat_score += 2.0

    score += eeat_score
    if eeat_score >= 5.0:
        feedback.append("Strong E-E-A-T provenance signals (author, date, citations).")
    else:
        feedback.append("Weak E-E-A-T signals. Add explicit author attribution and publication dates.")

    deductions = []

    if not capsule_found:
        deductions.append({
            "points_lost": 6.0,
            "category": "Answer Capsule",
            "title": "Missing Direct Answer Capsule Under Headings",
            "reason": "AI answer engines require 30–70 word direct answer definitions under H1/H2 tags to quote in AI Overviews.",
            "recommendation": "Inject a concise 40-word answer capsule directly beneath your primary hero heading."
        })

    if density < 0.4:
        lost = 3.0 if density >= 0.2 else 6.0
        deductions.append({
            "points_lost": lost,
            "category": "Fact Density",
            "title": "Low Quantitative & Fact-Triplet Statement Density",
            "reason": f"Only {round(density * 100)}% of content contains empirical claims, benchmarks, or Subject-Predicate-Object triplets.",
            "recommendation": "Rephrase marketing claims with verifiable metrics, latencies, dates, and clear active verbs."
        })

    if eeat_score < 7.0:
        lost = round(7.0 - eeat_score, 1)
        deductions.append({
            "points_lost": lost,
            "category": "E-E-A-T Provenance",
            "title": "Missing Author, Publication Date, or Citation Provenance",
            "reason": "Answer engines require verified authorship (rel='author'), publication dates, and citations to assign high citation weight.",
            "recommendation": "Add explicit byline markup, <time datetime='...'> timestamps, and linked citations."
        })

    return {
        "pillar": "Pillar A: Citability & Answerability",
        "score": round(min(25.0, score), 1),
        "max_score": 25.0,
        "details": {
            "has_answer_capsule": capsule_found,
            "fact_density_pct": round(density * 100, 1),
            "eeat_score": round(eeat_score, 1)
        },
        "feedback": feedback,
        "deductions": deductions
    }
