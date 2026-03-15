"""Tests for the knowledge base tool."""

from src.tools.knowledge_base import KnowledgeBaseTool, TACTICS_LIBRARY, _FIELD_TESTED_IDS


def test_tactics_library_size():
    """Should have 18 original + 26 field-tested = 44 tactics."""
    assert len(TACTICS_LIBRARY) == 44


def test_field_tested_count():
    assert len(_FIELD_TESTED_IDS) == 26


def test_all_tactics_have_required_fields():
    for tactic in TACTICS_LIBRARY:
        assert "id" in tactic
        assert "framework" in tactic
        assert "stage" in tactic
        assert "tactic" in tactic
        assert "best_for" in tactic


def test_no_duplicate_ids():
    ids = [t["id"] for t in TACTICS_LIBRARY]
    assert len(ids) == len(set(ids))


def test_query_returns_results():
    kb = KnowledgeBaseTool()
    results = kb.query("champion burnout support")
    assert len(results) > 0
    assert len(results) <= 3  # default max_results


def test_query_max_results():
    kb = KnowledgeBaseTool()
    results = kb.query("adoption metrics engagement", max_results=5)
    assert len(results) <= 5


def test_query_no_match():
    kb = KnowledgeBaseTool()
    results = kb.query("xyznonexistent")
    assert len(results) == 0


def test_field_tested_boost():
    """Field-tested entries should rank higher than generic ones for matching queries."""
    kb = KnowledgeBaseTool()
    results = kb.query("champion burnout isolation executive recognition")
    # The field-tested champion_isolation entry should appear
    ids = [r["id"] for r in results]
    assert "field_champion_isolation" in ids


def test_query_stall_detection():
    kb = KnowledgeBaseTool()
    results = kb.query("stall metrics dip engagement week 8")
    ids = [r["id"] for r in results]
    # Should find the field-tested stall detection entries
    assert any("field" in id for id in ids)


def test_query_industry_specific():
    kb = KnowledgeBaseTool()
    results = kb.query("financial services compliance security gate")
    ids = [r["id"] for r in results]
    assert any("fs" in id or "compliance" in id.lower() for id in ids)
