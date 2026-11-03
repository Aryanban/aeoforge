"""Unit tests for native Model Context Protocol (MCP) tool handlers."""

import pytest
from aeoforge.mcp_server import handle_tool_call, MCP_TOOLS


def test_mcp_tools_list():
    tool_names = [t["name"] for t in MCP_TOOLS]
    assert "aeoforge_audit" in tool_names
    assert "aeoforge_generate_spec" in tool_names
    assert "aeoforge_verify_citability" in tool_names
    assert "aeoforge_deobfuscate_email" in tool_names


@pytest.mark.asyncio
async def test_mcp_verify_citability():
    res = await handle_tool_call(
        "aeoforge_verify_citability",
        {"text": "AEOForge is an open source platform. It enables agents to navigate sites."}
    )
    assert "score" in res
    assert res["pillar"] == "Pillar A: Citability & Answerability"


@pytest.mark.asyncio
async def test_mcp_deobfuscate():
    res = await handle_tool_call(
        "aeoforge_deobfuscate_email",
        {"cf_hex": "582c3d2b2c183d20393528343d763b3735"}
    )
    assert res["decoded_email"] == "test@example.com"
