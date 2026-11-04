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
    """Generate a high-density, spec-compliant llms.txt directory for AI agents."""
    parsed = urlparse(url)
    origin = f"{parsed.scheme}://{parsed.netloc}"

    # Clean text content from markdown headings or excessive whitespace
    clean_lines = [
        line.lstrip("#- *").strip() 
        for line in text_content.splitlines() 
        if line.strip() and not line.strip().startswith(("#", "!", "["))
    ]
    flat_text = " ".join(clean_lines) if clean_lines else text_content
    summary_sentences = [s.strip() for s in flat_text.split(". ") if len(s.strip()) > 10]
    summary = " ".join(summary_sentences[:2]).strip()
    if summary and not summary.endswith("."):
        summary += "."

    lines = [
        f"# {title or parsed.netloc}",
        "",
        f"> {summary or 'Official machine-readable LLM navigation directory.'}",
        "",
        "## Core Documentation & Resources",
        ""
    ]

    # Add curated navigation targets as links
    added_urls = set()
    for m in interactive_marks:
        href = m.get("href")
        name = m.get("name")
        if href and name and len(name) > 2 and href not in added_urls:
            # Skip anchor fragments or javascript pseudo-links
            if href.startswith(("#", "javascript:")):
                continue
            full_href = href if href.startswith("http") else f"{origin}/{href.lstrip('/')}"
            lines.append(f"- [{name}]({full_href}): Direct entry point for {name}.")
            added_urls.add(href)
            if len(added_urls) >= 12:
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
