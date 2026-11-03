"""Native Model Context Protocol (MCP) Server for AEOForge.
Enables Meta AI, Claude, Antigravity, and Cursor agents to invoke AEO audits autonomously.
"""

import asyncio
import json
import sys
from typing import Dict, Any, List

from aeoforge import __version__
from aeoforge.navigator.browser import BrowserNavigator
from aeoforge.scorer.engine import AEOScoringEngine
from aeoforge.scorer.citability import score_citability
from aeoforge.spec.spec_generator import generate_agent_spec
from aeoforge.spec.llmstxt_gen import generate_llms_txt
from aeoforge.utils.deobfuscator import deobfuscate_cloudflare_email, extract_obfuscated_emails

MCP_TOOLS = [
    {
        "name": "aeoforge_audit",
        "description": "Run a full 0-100 AEO & Agent-Readiness audit on any website, identifying navigation traps, token bloat, and citation signals.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Target website URL to audit"}
            },
            "required": ["url"]
        }
    },
    {
        "name": "aeoforge_generate_spec",
        "description": "Generate an agent-spec.json (machine navigation manifest) and spec-compliant llms.txt for any website.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Target website URL"}
            },
            "required": ["url"]
        }
    },
    {
        "name": "aeoforge_verify_citability",
        "description": "Evaluate text passages or HTML for fact-triplets, direct answer capsules, and E-E-A-T citation readiness.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text content to evaluate"},
                "html": {"type": "string", "description": "Optional raw HTML content", "default": ""}
            },
            "required": ["text"]
        }
    },
    {
        "name": "aeoforge_deobfuscate_email",
        "description": "Decode Cloudflare data-cfemail XOR tokens or extract mutated emails from HTML.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "cf_hex": {"type": "string", "description": "Cloudflare data-cfemail hex string"},
                "html": {"type": "string", "description": "HTML containing obfuscated emails"}
            }
        }
    }
]


async def handle_tool_call(name: str, arguments: Dict[str, Any]) -> Any:
    """Execute requested MCP tool."""
    navigator = BrowserNavigator()
    scorer = AEOScoringEngine()

    if name == "aeoforge_audit":
        url = arguments.get("url")
        nav_data = await navigator.inspect_url(url, capture_screenshot=False)
        result = await scorer.audit(
            url=nav_data.final_url,
            html=nav_data.html,
            text_content=nav_data.text_content,
            raw_html_tokens=nav_data.raw_html_tokens,
            text_tokens=nav_data.text_tokens,
            traps=nav_data.traps,
            interactive_marks=nav_data.interactive_marks,
            a11y_tree=nav_data.a11y_tree
        )
        return result.model_dump()

    elif name == "aeoforge_generate_spec":
        url = arguments.get("url")
        nav_data = await navigator.inspect_url(url, capture_screenshot=False)
        audit = await scorer.audit(
            url=nav_data.final_url,
            html=nav_data.html,
            text_content=nav_data.text_content,
            raw_html_tokens=nav_data.raw_html_tokens,
            text_tokens=nav_data.text_tokens,
            traps=nav_data.traps,
            interactive_marks=nav_data.interactive_marks,
            a11y_tree=nav_data.a11y_tree
        )
        endpoints = audit.pillars["pillar_d_structured_data"]["details"].get("discovered_endpoints", [])
        spec = generate_agent_spec(
            url=nav_data.final_url,
            aeo_score=audit.overall_score,
            html=nav_data.html,
            traps=nav_data.traps,
            interactive_marks=nav_data.interactive_marks,
            discovered_endpoints=endpoints
        )
        llms_txt = generate_llms_txt(
            url=nav_data.final_url,
            title=nav_data.title,
            text_content=nav_data.text_content,
            interactive_marks=nav_data.interactive_marks
        )
        return {
            "agent_spec": spec,
            "llms_txt": llms_txt
        }

    elif name == "aeoforge_verify_citability":
        text = arguments.get("text", "")
        html = arguments.get("html", f"<p>{text}</p>")
        return score_citability(html, text)

    elif name == "aeoforge_deobfuscate_email":
        cf_hex = arguments.get("cf_hex")
        html = arguments.get("html")
        if cf_hex:
            return {"decoded_email": deobfuscate_cloudflare_email(cf_hex)}
        elif html:
            return {"extracted_emails": extract_obfuscated_emails(html)}
        return {"error": "Missing cf_hex or html argument"}

    else:
        raise ValueError(f"Unknown MCP tool: {name}")


async def run_mcp_server():
    """Run JSON-RPC 2.0 stdio server loop."""
    loop = asyncio.get_event_loop()
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    await loop.connect_read_pipe(lambda: protocol, sys.stdin)

    while True:
        line = await reader.readline()
        if not line:
            break
        try:
            req = json.loads(line.decode("utf-8"))
            msg_id = req.get("id")
            method = req.get("method")

            if method == "initialize":
                resp = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "serverInfo": {"name": "aeoforge", "version": __version__},
                        "capabilities": {"tools": {}}
                    }
                }
            elif method == "tools/list":
                resp = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {"tools": MCP_TOOLS}
                }
            elif method == "tools/call":
                params = req.get("params", {})
                name = params.get("name")
                args = params.get("arguments", {})
                result = await handle_tool_call(name, args)
                resp = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "content": [{"type": "text", "text": json.dumps(result, indent=2)}]
                    }
                }
            else:
                resp = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {"code": -32601, "message": f"Method not found: {method}"}
                }

            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()
        except Exception as e:
            err_resp = {
                "jsonrpc": "2.0",
                "id": req.get("id") if "req" in locals() else None,
                "error": {"code": -32603, "message": str(e)}
            }
            sys.stdout.write(json.dumps(err_resp) + "\n")
            sys.stdout.flush()


def main():
    asyncio.run(run_mcp_server())


if __name__ == "__main__":
    main()
