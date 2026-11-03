"""Unit tests for codebase patcher."""

import os
import tempfile
import json
from aeoforge.patcher.ast_patcher import CodebasePatcher


def test_codebase_patcher():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a mock index.html
        html_file = os.path.join(tmpdir, "index.html")
        with open(html_file, "w") as f:
            f.write("<html><head><title>Test App</title></head><body><h1>Hello</h1></body></html>")

        patcher = CodebasePatcher(tmpdir)
        llms_txt = "# Test App\n> Description\n"
        agent_spec = {"domain": "test.com"}
        schema = {"@context": "https://schema.org", "@type": "WebSite"}

        results = patcher.patch_all(llms_txt, agent_spec, schema)

        assert os.path.exists(os.path.join(tmpdir, "llms.txt"))
        assert os.path.exists(os.path.join(tmpdir, "agent-spec.json"))

        with open(html_file, "r") as f:
            patched_html = f.read()
        assert "application/ld+json" in patched_html
        assert "https://schema.org" in patched_html
