"""Persistent Storage Engine for AEOForge.
Backs audit histories, domain progression timelines, technical settings, and codebase patch records using SQLite.
"""

import os
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse


def get_default_db_path() -> str:
    """Return persistent SQLite database path with fallback to workspace."""
    env_path = os.environ.get("AEOFORGE_DB_PATH")
    if env_path:
        os.makedirs(os.path.dirname(os.path.abspath(env_path)), exist_ok=True)
        return env_path

    # Check local workspace data directory first
    if os.path.isdir("data"):
        return os.path.abspath("data/aeoforge.db")

    base_dir = os.path.expanduser("~/.aeoforge")
    try:
        os.makedirs(base_dir, exist_ok=True)
        return os.path.join(base_dir, "aeoforge.db")
    except Exception:
        return os.path.abspath(".aeoforge.db")


class AEOStorage:
    """Thread-safe SQLite persistent store for audits, settings, and progression."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or get_default_db_path()
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=15.0, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        return conn

    def _init_db(self):
        """Create tables and performance indices if they do not exist."""
        with self._get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS audits (
                    id TEXT PRIMARY KEY,
                    url TEXT NOT NULL,
                    domain TEXT NOT NULL,
                    overall_score REAL NOT NULL,
                    grade TEXT NOT NULL,
                    visual_score REAL,
                    semantic_score REAL,
                    protocol_score REAL,
                    citability_score REAL,
                    potential_score REAL,
                    title TEXT,
                    recommendations_count INTEGER DEFAULT 0,
                    result_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_audits_domain ON audits(domain, created_at DESC);
                CREATE INDEX IF NOT EXISTS idx_audits_created ON audits(created_at DESC);

                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS codebase_patches (
                    id TEXT PRIMARY KEY,
                    domain TEXT NOT NULL,
                    target_dir TEXT NOT NULL,
                    patched_files TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
            """)

    @staticmethod
    def extract_domain(url: str) -> str:
        parsed = urlparse(url)
        return parsed.netloc or parsed.path or url

    def save_audit(self, url: str, result_dict: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
        """Persist an audit result and calculate domain progression metrics."""
        now = datetime.now(timezone.utc)
        iso_now = now.isoformat()
        audit_id = f"audit_{now.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        domain = self.extract_domain(url)
        overall_score = float(result_dict.get("overall_score", 0.0))
        grade = str(result_dict.get("grade", "F"))
        title = result_dict.get("title") or domain

        pillars = result_dict.get("pillars", {})
        cit = float(pillars.get("pillar_a_citability", {}).get("score", 0.0))
        nav = float(pillars.get("pillar_b_navigability", {}).get("score", 0.0))
        proto = float(pillars.get("pillar_c_protocols", {}).get("score", 0.0))
        sem = float(pillars.get("pillar_d_structured_data", {}).get("score", 0.0))
        potential = float(result_dict.get("potential_score") or overall_score)
        recs = result_dict.get("recommendations") or []

        # Get existing audits for progression calculation before inserting
        progression = self.get_domain_progression(domain)
        prev_score = progression["latest_score"] if progression["audit_count"] > 0 else None
        first_score = progression["initial_score"] if progression["audit_count"] > 0 else overall_score

        # Ensure result_dict is JSON-serializable
        result_json = json.dumps(result_dict, default=str)

        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO audits (
                    id, url, domain, overall_score, grade,
                    visual_score, semantic_score, protocol_score, citability_score,
                    potential_score, title, recommendations_count, result_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                audit_id, url, domain, overall_score, grade,
                nav, sem, proto, cit,
                potential, title, len(recs), result_json, iso_now
            ))

        # Re-fetch progression with new audit included
        updated_progression = self.get_domain_progression(domain)
        if prev_score is not None:
            updated_progression["delta_since_previous"] = round(overall_score - prev_score, 1)
            updated_progression["delta_since_first"] = round(overall_score - first_score, 1)
        else:
            updated_progression["delta_since_previous"] = 0.0
            updated_progression["delta_since_first"] = 0.0

        return audit_id, updated_progression

    def get_audit(self, audit_id: str) -> Optional[Dict[str, Any]]:
        """Fetch full audit snapshot by ID."""
        with self._get_connection() as conn:
            row = conn.execute("SELECT result_json FROM audits WHERE id = ?", (audit_id,)).fetchone()
            if row:
                data = json.loads(row["result_json"])
                data["id"] = audit_id
                return data
            return None

    def list_audits(self, domain: Optional[str] = None, limit: int = 25) -> List[Dict[str, Any]]:
        """List audit summaries ordered by most recent first."""
        with self._get_connection() as conn:
            if domain:
                cursor = conn.execute("""
                    SELECT id, url, domain, overall_score, grade,
                           visual_score, semantic_score, protocol_score, citability_score,
                           potential_score, title, recommendations_count, created_at
                    FROM audits
                    WHERE domain = ?
                    ORDER BY created_at DESC, rowid DESC
                    LIMIT ?
                """, (domain, limit))
            else:
                cursor = conn.execute("""
                    SELECT id, url, domain, overall_score, grade,
                           visual_score, semantic_score, protocol_score, citability_score,
                           potential_score, title, recommendations_count, created_at
                    FROM audits
                    ORDER BY created_at DESC, rowid DESC
                    LIMIT ?
                """, (limit,))

            results = []
            for r in cursor.fetchall():
                results.append({
                    "id": r["id"],
                    "url": r["url"],
                    "domain": r["domain"],
                    "overall_score": r["overall_score"],
                    "grade": r["grade"],
                    "visual_score": r["visual_score"],
                    "semantic_score": r["semantic_score"],
                    "protocol_score": r["protocol_score"],
                    "citability_score": r["citability_score"],
                    "potential_score": r["potential_score"],
                    "title": r["title"],
                    "recommendations_count": r["recommendations_count"],
                    "created_at": str(r["created_at"])
                })
            return results

    def get_domain_progression(self, domain: str) -> Dict[str, Any]:
        """Compute progression points, trend, and score delta for a given domain."""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT id, overall_score, grade, created_at
                FROM audits
                WHERE domain = ?
                ORDER BY created_at ASC, rowid ASC
            """, (domain,))
            rows = cursor.fetchall()

        if not rows:
            return {
                "domain": domain,
                "audit_count": 0,
                "initial_score": 0.0,
                "latest_score": 0.0,
                "delta_since_previous": 0.0,
                "delta_since_first": 0.0,
                "trend": "baseline",
                "points": []
            }

        points = [{
            "id": r["id"],
            "score": r["overall_score"],
            "grade": r["grade"],
            "created_at": str(r["created_at"])
        } for r in rows]

        initial_score = points[0]["score"]
        latest_score = points[-1]["score"]
        prev_score = points[-2]["score"] if len(points) > 1 else initial_score

        delta_prev = round(latest_score - prev_score, 1)
        delta_first = round(latest_score - initial_score, 1)

        trend = "improving" if delta_first > 0.5 else ("regressing" if delta_first < -0.5 else "steady")

        return {
            "domain": domain,
            "audit_count": len(points),
            "initial_score": initial_score,
            "latest_score": latest_score,
            "delta_since_previous": delta_prev,
            "delta_since_first": delta_first,
            "trend": trend,
            "points": points
        }

    def delete_audit(self, audit_id: str) -> bool:
        """Delete an audit by ID."""
        with self._get_connection() as conn:
            cur = conn.execute("DELETE FROM audits WHERE id = ?", (audit_id,))
            return cur.rowcount > 0

    def clear_history(self) -> int:
        """Clear all audit history."""
        with self._get_connection() as conn:
            cur = conn.execute("DELETE FROM audits")
            return cur.rowcount

    # Settings & Technical Configurations
    def get_setting(self, key: str, default: Any = None) -> Any:
        with self._get_connection() as conn:
            row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
            if row:
                try:
                    return json.loads(row["value"])
                except Exception:
                    return row["value"]
            return default

    def set_setting(self, key: str, value: Any):
        iso_now = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            val_str = json.dumps(value) if not isinstance(value, str) else value
            conn.execute("""
                INSERT INTO settings (key, value, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
            """, (key, val_str, iso_now))

    def get_all_settings(self) -> Dict[str, Any]:
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT key, value FROM settings")
            res = {}
            for r in cursor.fetchall():
                try:
                    res[r["key"]] = json.loads(r["value"])
                except Exception:
                    res[r["key"]] = r["value"]
            return res

    # Codebase Patch Log
    def log_patch(self, domain: str, target_dir: str, patched_files: List[str]) -> str:
        now = datetime.now(timezone.utc)
        patch_id = f"patch_{now.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:4]}"
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO codebase_patches (id, domain, target_dir, patched_files, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (patch_id, domain, target_dir, json.dumps(patched_files), now.isoformat()))
        return patch_id


# Global Singleton instance
storage = AEOStorage()
