"""Unit tests for Ollama local Meta Llama 3.2 inference client."""

import pytest
from aeoforge.models.meta_client import MetaAIClient


@pytest.mark.asyncio
async def test_ollama_model_resolution():
    """Verify that MetaAIClient detects local Ollama or gracefully falls back when offline."""
    client = MetaAIClient()
    is_available = await client._check_ollama_available()
    model, has_vis = await client._resolve_ollama_model()
    if is_available:
        assert model is not None, "Ollama model should be resolved when daemon is online"
        assert "llama" in model.lower() or "latest" in model.lower()
    else:
        assert model is None, "Model should be None when daemon is offline"


@pytest.mark.asyncio
async def test_ollama_local_citability_analysis():
    """Verify on-device citability analysis using local Llama 3.2."""
    client = MetaAIClient()
    sample_text = (
        "AEOForge provides automated evaluation of website agent-readiness. "
        "It generates machine-actionable specifications for LLMs and autonomous browsing agents."
    )
    res = await client.analyze_citability(sample_text)
    assert isinstance(res, dict)
    assert "citability_score" in res
    assert 0 <= res["citability_score"] <= 100
    assert "recommended_aeo_snippet" in res


@pytest.mark.asyncio
async def test_ollama_local_navigation_reasoning():
    """Verify on-device visual/structural navigation evaluation using local Llama 3.2."""
    client = MetaAIClient()
    a11y_tree = (
        "[1] <button class=\"cookie-accept\">Accept All Cookies</button>\n"
        "[2] <div class=\"modal-backdrop\">Promo banner</div>\n"
        "[3] <main><h1>Developer Docs</h1></main>"
    )
    traps = [{"name": "Cookie Banner", "severity": "medium", "active_selector": ".cookie-accept"}]
    res = await client.analyze_visual_navigation(
        screenshot_base64=None,
        a11y_tree=a11y_tree,
        traps=traps
    )
    assert isinstance(res, dict)
    assert "visual_navigability_score" in res
    assert 0 <= res["visual_navigability_score"] <= 100
    assert "agent_navigation_advice" in res
