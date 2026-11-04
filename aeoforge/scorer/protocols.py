"""Pillar C: Machine Discovery, Protocols & Standards (25 Points Max).
Evaluates llms.txt, llms-full.txt, robots.txt AI crawler policies, and discovery protocols.
"""

from typing import Dict, Any, Optional
from urllib.parse import urlparse
import httpx


async def score_protocols(base_url: str) -> Dict[str, Any]:
    """Audit domain machine discovery protocols (llms.txt, robots.txt, sitemaps)."""
    score = 0.0
    feedback = []

    parsed = urlparse(base_url)
    origin = f"{parsed.scheme}://{parsed.netloc}"

    has_llmstxt = False
    has_llms_full = False
    ai_crawlers_allowed = False
    has_sitemap = False

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
                ai_bots = ["meta-externalagent", "gptbot", "claudebot", "perplexitybot", "google-extended"]
                found_bots = [b for b in ai_bots if b in txt]
                
                # Check if disallowing all bots
                if "user-agent: *" in txt and ("disallow: /\n" in txt or "disallow: / " in txt or txt.endswith("disallow: /")):
                    ai_crawlers_allowed = False
                    score += 1.0
                    feedback.append("robots.txt actively disallows all web crawlers.")
                elif found_bots:
                    ai_crawlers_allowed = True
                    score += 7.0
                    feedback.append(f"robots.txt contains explicit policies for AI agents: {', '.join(found_bots)}.")
                else:
                    ai_crawlers_allowed = False
                    score += 4.0
                    feedback.append("robots.txt present but lacks explicit policies for AI crawlers (Meta-ExternalAgent, PerplexityBot).")
            else:
                ai_crawlers_allowed = False
                score += 2.0
                feedback.append("Missing robots.txt file.")
        except Exception:
            ai_crawlers_allowed = False
            score += 2.0

        # 4. Check /sitemap.xml (0 - 4 pts)
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

    deductions = []

    if not has_llmstxt:
        deductions.append({
            "points_lost": 10.0,
            "category": "LLMs Directory",
            "title": "Missing /llms.txt at Domain Root",
            "reason": "AI answer engines and coding agents (Cursor, Claude, Perplexity) lack a curated markdown navigation manifest.",
            "recommendation": "Deploy a standardized /llms.txt at the domain root with markdown links to key documentation."
        })

    if not has_llms_full:
        deductions.append({
            "points_lost": 4.0,
            "category": "Full Documentation",
            "title": "Missing /llms-full.txt Deep Documentation",
            "reason": "Agents performing multi-turn RAG or computer use lack a comprehensive single-file text context.",
            "recommendation": "Generate public/llms-full.txt aggregating complete site documentation."
        })

    if not ai_crawlers_allowed:
        lost = 6.0 if "disallow" in feedback[0].lower() else 3.0
        deductions.append({
            "points_lost": lost,
            "category": "Crawler Directives",
            "title": "Restricted AI Crawler Directives in robots.txt / WAF",
            "reason": "robots.txt or security firewall restricts Meta-ExternalAgent, PerplexityBot, ClaudeBot, or GPTBot from crawling.",
            "recommendation": "Add explicit allow rules for verified AI bots in robots.txt and configure Cloudflare WAF bypass."
        })

    if not has_sitemap:
        deductions.append({
            "points_lost": 4.0,
            "category": "XML Sitemap",
            "title": "Missing or Inaccessible /sitemap.xml",
            "reason": "Search engines and LLM crawlers cannot automatically enumerate new or deeply nested routes.",
            "recommendation": "Publish a standards-compliant XML sitemap at /sitemap.xml."
        })

    return {
        "pillar": "Pillar C: Machine Protocols & Discovery",
        "score": round(min(25.0, score), 1),
        "max_score": 25.0,
        "details": {
            "has_llms_txt": has_llmstxt,
            "has_llms_full_txt": has_llms_full,
            "has_sitemap_xml": has_sitemap,
            "ai_bots_allowed": ai_crawlers_allowed
        },
        "feedback": feedback,
        "deductions": deductions
    }
