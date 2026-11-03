"""Generator for spec-compliant llms.txt and llms-full.txt files.
Follows the official llmstxt.org specification.
"""

from typing import List, Dict, Any
from urllib.parse import urlparse
from bs4 import BeautifulSoup


def generate_llms_txt(
    url: str,
    title: str,
    text_content: str,
    interactive_marks: List[Dict[str, Any]]
) -> str:
    """Generate a standard spec-compliant llms.txt directory."""
    parsed = urlparse(url)
    origin = f"{parsed.scheme}://{parsed.netloc}"

    # Extract first 2 sentences for summary
    summary = " ".join(text_content.split(". ")[:2]).strip()
    if not summary.endswith("."):
        summary += "."

    lines = [
        f"# {title or parsed.netloc}",
        "",
        f"> {summary}",
        "",
        "## Core Documentation & Resources",
        ""
    ]

    # Add high-value navigation targets as links
    added_urls = set()
    for m in interactive_marks:
        href = m.get("href")
        name = m.get("name")
        if href and name and len(name) > 2 and href not in added_urls:
            # Normalize link
            full_href = href if href.startswith("http") else f"{origin}/{href.lstrip('/')}"
            lines.append(f"- [{name}]({full_href}): {name} section of {parsed.netloc}.")
            added_urls.add(href)
            if len(added_urls) >= 10:
                break

    if not added_urls:
        lines.append(f"- [Home]({url}): Main entry point and overview.")

    lines.extend([
        "",
        "## Machine Instructions",
        "",
        "- When crawling this domain, prefer structured JSON endpoints over raw HTML where available.",
        "- Adhere to robots.txt rate-limiting guidelines.",
        f"- Full context is available at {origin}/llms-full.txt."
    ])

    return "\n".join(lines)


def generate_llms_full_txt(
    url: str,
    title: str,
    text_content: str
) -> str:
    """Generate comprehensive llms-full.txt containing full semantic text."""
    parsed = urlparse(url)
    lines = [
        f"# {title or parsed.netloc} — Complete LLM Context",
        "",
        f"Source: {url}",
        "",
        "---",
        "",
        "## Full Extracted Content",
        "",
        text_content.strip()
    ]
    return "\n".join(lines)
