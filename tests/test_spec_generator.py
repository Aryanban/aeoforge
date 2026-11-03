"""Unit tests for Agent Navigation Spec and llms.txt generators."""

from aeoforge.spec.spec_generator import generate_agent_spec
from aeoforge.spec.llmstxt_gen import generate_llms_txt, generate_llms_full_txt
from aeoforge.spec.schema_gen import generate_schema_jsonld


def test_generate_agent_spec():
    html = """
    <html>
        <body>
            <main id="main-content">
                <h1>Pricing & Docs</h1>
                <form action="/api/v1/search">
                    <input type="text" name="query">
                </form>
            </main>
        </body>
    </html>
    """
    marks = [
        {"id": 1, "tag": "a", "role": "link", "name": "Pricing", "href": "/pricing"},
        {"id": 2, "tag": "a", "role": "link", "name": "Documentation", "href": "/docs"}
    ]
    spec = generate_agent_spec(
        url="https://aeoforge.dev",
        aeo_score=88.5,
        html=html,
        traps=[],
        interactive_marks=marks,
        discovered_endpoints=["/api/v1/search"]
    )

    assert spec["domain"] == "aeoforge.dev"
    assert spec["aeo_score"] == 88.5
    assert spec["agent_instructions"]["primary_content_selector"] == "main#main-content"
    assert spec["agent_instructions"]["action_map"]["key_actions"]["pricing_link"] == "/pricing"


def test_generate_llms_txt():
    marks = [
        {"id": 1, "name": "API Reference", "href": "/docs/api"},
        {"id": 2, "name": "Quickstart", "href": "/docs/quickstart"}
    ]
    llms_txt = generate_llms_txt(
        url="https://aeoforge.dev",
        title="AEOForge Platform",
        text_content="AEOForge is the autonomous agent auditor. It evaluates websites for AEO readiness.",
        interactive_marks=marks
    )

    assert "# AEOForge Platform" in llms_txt
    assert "[API Reference]" in llms_txt
    assert "https://aeoforge.dev/docs/api" in llms_txt
    assert "llms-full.txt" in llms_txt


def test_generate_schema_jsonld():
    html = """
    <html>
        <body>
            <h2>How does AEO work?</h2>
            <p>AEO structures facts and semantic graphs so that AI agents can cite websites accurately.</p>
        </body>
    </html>
    """
    schema = generate_schema_jsonld(
        url="https://aeoforge.dev",
        title="AEOForge",
        description="AEO Auditor for AI Agents",
        html=html
    )

    assert schema["@context"] == "https://schema.org"
    graph_types = [item["@type"] for item in schema["@graph"]]
    assert "WebSite" in graph_types
    assert "Organization" in graph_types
    assert "FAQPage" in graph_types
