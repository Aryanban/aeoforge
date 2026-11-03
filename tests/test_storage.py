import os
import tempfile
import pytest
from aeoforge.storage import AEOStorage


def test_storage_crud_and_progression():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        temp_db = f.name

    try:
        store = AEOStorage(db_path=temp_db)

        # 1. First audit baseline
        res1 = {
            "overall_score": 45.0,
            "grade": "F",
            "title": "Example Domain",
            "pillars": {
                "pillar_a_citability": {"score": 10.0},
                "pillar_b_navigability": {"score": 12.0},
                "pillar_c_protocols": {"score": 8.0},
                "pillar_d_structured_data": {"score": 15.0}
            },
            "recommendations": [{"id": "rec1"}]
        }
        id1, prog1 = store.save_audit("https://example.com", res1)
        assert id1.startswith("audit_")
        assert prog1["audit_count"] == 1
        assert prog1["initial_score"] == 45.0
        assert prog1["latest_score"] == 45.0
        assert prog1["delta_since_previous"] == 0.0

        # 2. Second audit (improvement)
        res2 = {
            "overall_score": 75.5,
            "grade": "B",
            "title": "Example Domain",
            "pillars": {
                "pillar_a_citability": {"score": 18.0},
                "pillar_b_navigability": {"score": 20.0},
                "pillar_c_protocols": {"score": 18.0},
                "pillar_d_structured_data": {"score": 19.5}
            },
            "recommendations": []
        }
        id2, prog2 = store.save_audit("https://example.com", res2)
        assert prog2["audit_count"] == 2
        assert prog2["initial_score"] == 45.0
        assert prog2["latest_score"] == 75.5
        assert prog2["delta_since_previous"] == 30.5
        assert prog2["delta_since_first"] == 30.5
        assert prog2["trend"] == "improving"

        # 3. Retrieve audit snapshot
        fetched = store.get_audit(id1)
        assert fetched is not None
        assert fetched["overall_score"] == 45.0

        # 4. List audits
        all_audits = store.list_audits()
        assert len(all_audits) == 2
        assert all_audits[0]["id"] == id2  # most recent first

        # 5. Settings
        store.set_setting("groq_api_key", "gsk_test123")
        assert store.get_setting("groq_api_key") == "gsk_test123"

        # 6. Delete
        assert store.delete_audit(id1) is True
        assert len(store.list_audits()) == 1

        # 7. Clear history
        assert store.clear_history() == 1
        assert len(store.list_audits()) == 0

    finally:
        if os.path.exists(temp_db):
            os.remove(temp_db)
