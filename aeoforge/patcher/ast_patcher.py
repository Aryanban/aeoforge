"""AST and file patcher to automatically remediate AEO and agentic issues in local codebases.
Adapted and modernized from SEOForge (https://github.com/Aryanban/seoforge).
"""

import os
import json
from typing import Dict, Any, List


class CodebasePatcher:
    """Automated patcher to inject llms.txt, agent-spec.json, and Schema.org metadata."""

    def __init__(self, target_dir: str):
        self.target_dir = os.path.abspath(target_dir)

    def patch_all(
        self,
        llms_txt_content: str,
        agent_spec_data: Dict[str, Any],
        schema_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Apply all generated AEO artifacts to the target project directory."""
        results: List[Dict[str, Any]] = []

        if not os.path.exists(self.target_dir):
            return [{"status": "error", "message": f"Target directory not found: {self.target_dir}"}]

        # 1. Determine public assets folder (e.g. public/ for Next.js/Vite or root)
        public_dir = os.path.join(self.target_dir, "public")
        if not os.path.exists(public_dir):
            public_dir = self.target_dir

        # 2. Write llms.txt
        llms_path = os.path.join(public_dir, "llms.txt")
        try:
            with open(llms_path, "w", encoding="utf-8") as f:
                f.write(llms_txt_content)
            results.append({
                "file": llms_path,
                "action": "created" if not os.path.exists(llms_path) else "overwritten",
                "artifact": "llms.txt"
            })
        except Exception as e:
            results.append({"file": llms_path, "action": "error", "error": str(e)})

        # 3. Write agent-spec.json
        spec_path = os.path.join(public_dir, "agent-spec.json")
        try:
            with open(spec_path, "w", encoding="utf-8") as f:
                json.dump(agent_spec_data, f, indent=2)
            results.append({
                "file": spec_path,
                "action": "created" if not os.path.exists(spec_path) else "overwritten",
                "artifact": "agent-spec.json"
            })
        except Exception as e:
            results.append({"file": spec_path, "action": "error", "error": str(e)})

        # 4. Inject Schema.org JSON-LD into index.html if present
        index_html_path = os.path.join(self.target_dir, "index.html")
        if not os.path.exists(index_html_path):
            index_html_path = os.path.join(public_dir, "index.html")

        if os.path.exists(index_html_path):
            try:
                with open(index_html_path, "r", encoding="utf-8") as f:
                    content = f.read()

                script_tag = f'\n    <script type="application/ld+json">\n{json.dumps(schema_data, indent=6)}\n    </script>\n'
                if "application/ld+json" not in content and "</head>" in content:
                    patched = content.replace("</head>", f"{script_tag}</head>", 1)
                    with open(index_html_path, "w", encoding="utf-8") as f:
                        f.write(patched)
                    results.append({
                        "file": index_html_path,
                        "action": "injected",
                        "artifact": "Schema.org JSON-LD"
                    })
            except Exception as e:
                results.append({"file": index_html_path, "action": "error", "error": str(e)})

        return results
