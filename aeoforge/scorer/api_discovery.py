"""Pillar D: Structured Data & API Exposeability (25 Points Max).
Evaluates Schema.org JSON-LD graphs, machine-readable feeds, and direct API endpoints.
"""

import json
import re
from typing import Dict, Any, List
from bs4 import BeautifulSoup


def score_api_and_data(html: str) -> Dict[str, Any]:
    """Score page on structured data completeness and machine API discovery (0 - 25 points)."""
    score = 0.0
    feedback = []

    soup = BeautifulSoup(html, "html.parser")

    # 1. Schema.org JSON-LD Completeness (0 - 10 pts)
    jsonld_tags = soup.find_all("script", attrs={"type": "application/ld+json"})
    valid_schemas = []
    schema_types = []

    for tag in jsonld_tags:
        try:
            data = json.loads(tag.string or "{}")
            if isinstance(data, dict):
                stype = data.get("@type")
                if stype:
                    schema_types.append(stype)
                valid_schemas.append(data)
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and item.get("@type"):
                        schema_types.append(item.get("@type"))
                valid_schemas.extend(data)
        except Exception:
            pass

    if valid_schemas:
        if len(schema_types) >= 2:
            score += 10.0
            feedback.append(f"Rich Schema.org JSON-LD graph detected: {', '.join(set(schema_types))}.")
        else:
            score += 6.0
            feedback.append(f"Basic Schema.org JSON-LD detected: {', '.join(set(schema_types))}. Consider adding WebSite or FAQPage.")
    else:
        feedback.append("Missing Schema.org JSON-LD structured data. Answer engines cannot verify semantic entity connections.")

    # 2. OpenGraph & Semantic Metadata (0 - 5 pts)
    og_title = soup.find("meta", property="og:title")
    og_desc = soup.find("meta", property="og:description")
    og_type = soup.find("meta", property="og:type")
    meta_desc = soup.find("meta", attrs={"name": "description"})

    meta_score = 0.0
    if og_title: meta_score += 1.5
    if og_desc or meta_desc: meta_score += 2.0
    if og_type: meta_score += 1.5

    score += meta_score
    if meta_score >= 4.0:
        feedback.append("Complete OpenGraph metadata tags present.")
    else:
        feedback.append("Incomplete OpenGraph tags. Add og:title, og:description, and og:type.")

    # 3. Direct Search & API Action Endpoints (0 - 7 pts)
    # shortcut: scans HTML links and script strings; upgrade to dynamic CDP fetch interception for runtime RPC calls
    api_score = 0.0
    discovered_endpoints: List[str] = []
    has_webmcp = False

    # Check for WebMCP link rel or window.modelContext indicators
    webmcp_link = soup.find("link", attrs={"rel": re.compile(r"webmcp|agent-spec", re.I)})
    if webmcp_link:
        has_webmcp = True
        api_score += 4.0
        discovered_endpoints.append(f"WebMCP Manifest: {webmcp_link.get('href')}")

    # Check search forms
    search_forms = soup.find_all("form", attrs={"action": True})
    for f in search_forms:
        action = f.get("action", "")
        if "search" in action.lower() or "query" in action.lower():
            api_score += 3.5
            discovered_endpoints.append(f"Search Action: {action}")
            break

    # Check for direct API links or JSON endpoints (OpenAPI, Swagger, ai-plugin)
    json_links = soup.find_all("link", attrs={"type": re.compile(r"json", re.I)})
    for l in json_links:
        href = l.get("href")
        if href:
            api_score += 3.5
            discovered_endpoints.append(f"JSON Resource: {href}")

    # Regex scan script contents for API routes like /api/v1/ or WebMCP tool declarations
    scripts = soup.find_all("script")
    found_api_route = False
    for s in scripts:
        if s.string:
            if "modelContext.registerTool" in s.string or "window.modelContext" in s.string:
                has_webmcp = True
                api_score += 4.0
                discovered_endpoints.append("WebMCP Native Browser Tool Registered")
            matches = re.findall(r'["\'](/api/v[0-9]/[a-zA-Z0-9_\-/]+)["\']', s.string)
            if matches:
                found_api_route = True
                discovered_endpoints.extend(matches[:3])
                break

    if found_api_route and api_score < 7.0:
        api_score += 3.5

    score += min(7.0, api_score)
    if has_webmcp:
        feedback.append("WebMCP (Web Model Context Protocol) agent tooling detected.")
    if discovered_endpoints:
        feedback.append(f"Discovered machine action/API endpoints: {', '.join(discovered_endpoints[:3])}.")
    else:
        feedback.append("No direct machine-callable search or REST API endpoints identified.")

    # 4. Machine Feeds (RSS / Atom) (0 - 3 pts)
    feeds = soup.find_all("link", attrs={"type": re.compile(r"rss|atom", re.I)})
    if feeds:
        score += 3.0
        feedback.append("RSS/Atom syndication feed available for automated content ingestion.")
    else:
        feedback.append("No syndication feeds detected.")

    return {
        "pillar": "Pillar D: Structured Data & API Exposeability",
        "score": round(min(25.0, score), 1),
        "max_score": 25.0,
        "details": {
            "schema_types": list(set(schema_types)),
            "discovered_endpoints": discovered_endpoints
        },
        "feedback": feedback
    }
