"""Schema.org JSON-LD generator for AEO entity graphs."""

import json
from typing import Dict, Any, List
from urllib.parse import urlparse
from bs4 import BeautifulSoup


def generate_schema_jsonld(url: str, title: str, description: str, html: str) -> Dict[str, Any]:
    """Generate a rich Schema.org JSON-LD graph."""
    parsed = urlparse(url)
    origin = f"{parsed.scheme}://{parsed.netloc}"

    soup = BeautifulSoup(html, "html.parser")

    # Extract candidate FAQs if headings have question marks
    faq_elements = []
    headings = soup.find_all(["h2", "h3", "h4"])
    for h in headings:
        htext = h.get_text().strip()
        if "?" in htext:
            next_p = h.find_next_sibling("p")
            if next_p:
                answer = next_p.get_text().strip()
                if len(answer) > 20:
                    faq_elements.append({
                        "@type": "Question",
                        "name": htext,
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": answer
                        }
                    })

    graph: List[Dict[str, Any]] = [
        {
            "@type": "WebSite",
            "@id": f"{origin}/#website",
            "url": origin,
            "name": title or parsed.netloc,
            "description": description or f"Official website of {parsed.netloc}",
            "potentialAction": {
                "@type": "SearchAction",
                "target": f"{origin}/search?q={{search_term_string}}",
                "query-input": "required name=search_term_string"
            }
        },
        {
            "@type": "Organization",
            "@id": f"{origin}/#organization",
            "name": title or parsed.netloc,
            "url": origin
        }
    ]

    if faq_elements:
        graph.append({
            "@type": "FAQPage",
            "@id": f"{url}#faq",
            "mainEntity": faq_elements[:5]
        })

    return {
        "@context": "https://schema.org",
        "@graph": graph
    }
