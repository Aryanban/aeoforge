"""Unit tests for the 4-Pillar AEO Scoring modules."""

import pytest
from aeoforge.scorer.citability import score_citability
from aeoforge.scorer.navigability import score_navigability
from aeoforge.scorer.api_discovery import score_api_and_data
from aeoforge.scorer.engine import calculate_grade


def test_score_citability_high():
    html = """
    <html>
        <body>
            <h1>What is Answer Engine Optimization?</h1>
            <p>Answer Engine Optimization is the practice of structuring digital content with unambiguous factual statements and explicit semantic relationships so that autonomous artificial intelligence answer engines can accurately cite, ground, and synthesize key information for end users without hallucination.</p>
            <div class="author" rel="author">Aryan Bansal</div>
            <time datetime="2026-11-03">November 3, 2026</time>
            <cite>Meta AI Research 2026</cite>
        </body>
    </html>
    """
    text = "Answer Engine Optimization is the practice of structuring digital content with unambiguous factual statements. AEO enables autonomous agents to cite information accurately. The framework includes fact triplets and schema graphs."
    res = score_citability(html, text)
    assert res["score"] >= 20.0
    assert res["details"]["has_answer_capsule"] is True
    assert res["details"]["fact_density_pct"] > 50


def test_score_navigability():
    html = """
    <html>
        <body>
            <header><nav><a href="/">Home</a></nav></header>
            <main id="content">
                <h1>Autonomous Agent Platform</h1>
                <p>Simple content with high text ratio.</p>
            </main>
        </body>
    </html>
    """
    marks = [
        {"id": 1, "tag": "a", "role": "link", "name": "Home", "href": "/"}
    ]
    res = score_navigability(
        html=html,
        raw_html_tokens=100,
        text_tokens=40,
        traps=[],
        interactive_marks=marks
    )
    assert res["score"] >= 18.0
    assert res["details"]["traps_detected_count"] == 0


def test_score_api_and_data():
    html = """
    <html>
        <head>
            <title>AEOForge</title>
            <meta property="og:title" content="AEOForge">
            <meta property="og:description" content="Autonomous Meta AI Agent">
            <meta property="og:type" content="website">
            <script type="application/ld+json">
            {
                "@context": "https://schema.org",
                "@type": "WebSite",
                "url": "https://aeoforge.dev"
            }
            </script>
            <script type="application/ld+json">
            {
                "@context": "https://schema.org",
                "@type": "Organization",
                "name": "AEOForge"
            }
            </script>
        </head>
        <body>
            <form action="/search">
                <input type="search" name="q">
            </form>
        </body>
    </html>
    """
    res = score_api_and_data(html)
    assert res["score"] >= 18.0
    assert "WebSite" in res["details"]["schema_types"]
    assert "Organization" in res["details"]["schema_types"]


def test_calculate_grade():
    assert calculate_grade(95)[0] == "A+"
    assert calculate_grade(85)[0] == "A"
    assert calculate_grade(75)[0] == "B"
    assert calculate_grade(55)[0] == "C"
    assert calculate_grade(40)[0] == "F"
