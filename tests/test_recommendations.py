"""Unit tests for Cloudflare-grade AEO recommendations, WAF rules, and competitor comparison."""

import pytest
from aeoforge.scorer.recommendations import generate_recommendations
from aeoforge.scorer.waf_rules import generate_waf_rules
from aeoforge.scorer.competitor import compare_competitors


def test_recommendation_generation():
    """Verify that 5-6 prioritized recommendations with score boosts are generated."""
    sample_pillars = {
        "pillar_a_citability": {"score": 10.0, "details": {"has_answer_capsule": False, "fact_density_pct": 20.0}},
        "pillar_b_navigability": {"score": 14.0, "details": {"token_ratio_pct": 12.0, "traps_detected_count": 1}},
        "pillar_c_protocols": {"score": 2.0, "details": {"has_llms_txt": False, "ai_bots_allowed": False}},
        "pillar_d_structured_data": {"score": 0.0, "details": {"schema_types": []}}
    }
    traps = [{"name": "OneTrust Cookie Consent", "category": "cookie_consent", "severity": "critical"}]
    marks = [{"id": 1, "tag": "a", "role": "link", "name": "Docs"}]

    recs, potential_score = generate_recommendations(
        url="https://example.com",
        overall_score=26.0,
        pillars=sample_pillars,
        traps=traps,
        interactive_marks=marks
    )

    assert len(recs) >= 5, "Must produce at least 5 prioritized recommendations"
    assert potential_score > 26.0, "Potential score must reflect simulated improvement"
    
    # Check for specific Cloudflare and protocol recommendations
    rec_ids = [r.id for r in recs]
    assert "publish_llms_txt" in rec_ids
    assert "allow_ai_bots_waf" in rec_ids
    assert "add_answer_capsules" in rec_ids
    assert "inject_schema_jsonld" in rec_ids


def test_waf_rules_generation():
    """Verify Cloudflare, Nginx, and Vercel AI bot allow rules."""
    rules = generate_waf_rules("example.com")
    assert "cloudflare" in rules
    assert "nginx" in rules
    assert "vercel" in rules
    
    # Cloudflare rule should target Meta-ExternalAgent and PerplexityBot
    assert "Meta-ExternalAgent" in rules["cloudflare"]
    assert "PerplexityBot" in rules["cloudflare"]
    assert "cf.client.bot" in rules["cloudflare"]
