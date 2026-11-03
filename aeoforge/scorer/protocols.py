"""Pillar C: Machine Discovery, Protocols & Standards (25 Points Max).
Evaluates llms.txt, llms-full.txt, robots.txt AI crawler policies, and discovery protocols.
"""

from typing import Dict, Any, Optional
from urllib.parse import urlparse
import httpx


async def score_protocols(base_url: str) -> Dict[str, Any]:
    """Audit domain machine discovery protocols (llms.txt, robots.txt, sitemaps)."""
    # shortcut: checks root /llms.txt and /robots.txt; upgrade to recursive sitemap index crawler for 10k+ page catalogs
    score = 0.0
    feedback = []

    parsed = urlparse(base_url)
    origin = f"{parsed.scheme}://{parsed.netloc}"

    has_llmstxt = False
    has_llms_full = False
    ai_crawlers_allowed = False
    has_sitemap = False
    has_indexnow = False

    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        # 1. Check /llms.txt (0 - 10 pts)
        try:
            resp = await client.get(f"{origin}/llms.txt")
            if resp.status_code == 200 and len(resp.text) > 20 and not resp.text.strip().startswith("<!DOCTYPE"):
                has_llmstxt = True
                score += 10.0
                feedback.append("Valid /llms.txt detected at domain root. Excellent agent discoverability.")
            else:
                feedback.append("Missing /llms.txt at root. AI agents lack curated markdown navigation directory.")
        except Exception:
            feedback.append("Failed to fetch /llms.txt.")

        # 2. Check /llms-full.txt (0 - 4 pts)
        try:
            resp = await client.get(f"{origin}/llms-full.txt")
            if resp.status_code == 200 and len(resp.text) > 50 and not resp.text.strip().startswith("<!DOCTYPE"):
                has_llms_full = True
                score += 4.0
                feedback.append("Valid /llms-full.txt detected for complete agent documentation context.")
            else:
                feedback.append("Missing /llms-full.txt for comprehensive agent context.")
        except Exception:
            pass

        # 3. Check robots.txt for AI crawlers (0 - 7 pts)
        try:
            resp = await client.get(f"{origin}/robots.txt")
            if resp.status_code == 200:
                txt = resp.text.lower()
                # Check for explicit AI crawler mentions
                ai_bots = ["meta-externalagent", "gptbot", "claudebot", "perplexitybot", "google-extended"]
                found_bots = [b for b in ai_bots if b in txt]
                # Check if disallowing all bots
                if "user-agent: *" in txt and "disallow: /" in txt:
                    score += 1.0
                    feedback.append("robots.txt actively disallows all web crawlers.")
                elif found_bots:
                    score += 7.0
                    feedback.append(f"robots.txt contains explicit policies for AI agents: {', '.join(found_bots)}.")
                else:
                    score += 4.0
                    feedback.append("robots.txt present but lacks explicit policies for AI crawlers (Meta-ExternalAgent, PerplexityBot).")
            else:
                score += 2.0
                feedback.append("Missing robots.txt file.")
        except Exception:
            score += 2.0

        # 4. Check /sitemap.xml and IndexNow (0 - 4 pts)
        try:
            resp = await client.get(f"{origin}/sitemap.xml")
            if resp.status_code == 200 and ("<urlset" in resp.text or "<sitemapindex" in resp.text):
                has_sitemap = True
                score += 4.0
                feedback.append("Valid sitemap.xml detected.")
            else:
                feedback.append("Missing standard /sitemap.xml file.")
        except Exception:
            pass

    return {
        "pillar": "Pillar C: Machine Protocols & Discovery",
        "score": round(min(25.0, score), 1),
        "max_score": 25.0,
        "details": {
            "has_llms_txt": has_llmstxt,
            "has_llms_full_txt": has_llms_full,
            "has_sitemap_xml": has_sitemap
        },
        "feedback": feedback
    }
