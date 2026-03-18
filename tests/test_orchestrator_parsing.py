"""Tests for orchestrator JSON extraction — pure string parsing, no LLM calls."""

from src.agents.orchestrator import OrchestratorAgent
from src.models import InterventionType, PersonaType


# ── _find_json_array ──────────────────────────────────────────

def test_find_json_array_fenced_json():
    """Pattern 1: ```json [...] ```"""
    text = 'Here is my plan:\n```json\n[{"intervention_type": "workshop"}]\n```\nDone.'
    result = OrchestratorAgent._find_json_array(text)
    assert result is not None
    assert '"intervention_type"' in result


def test_find_json_array_fenced_no_lang():
    """Pattern 2: ``` [...] ``` with intervention_type keyword."""
    text = 'Plan:\n```\n[{"intervention_type": "workshop", "target_persona": "skeptical_ic"}]\n```'
    result = OrchestratorAgent._find_json_array(text)
    assert result is not None
    assert "workshop" in result


def test_find_json_array_bare():
    """Pattern 3: Bare JSON array in text."""
    text = 'I recommend: [{"intervention_type": "tool_demo", "target_persona": "skeptical_ic"}] and that is all.'
    result = OrchestratorAgent._find_json_array(text)
    assert result is not None
    assert "tool_demo" in result


def test_find_json_array_no_match():
    """No JSON array → None."""
    assert OrchestratorAgent._find_json_array("No interventions this week.") is None


def test_find_json_array_empty_array():
    """An empty array should not match (no intervention_type)."""
    text = "```json\n[]\n```"
    # Pattern 1 matches any array in ```json, including empty
    result = OrchestratorAgent._find_json_array(text)
    assert result is not None  # pattern 1 does match
    assert result.strip() == "[]"


def test_find_json_array_prefers_fenced_json():
    """Pattern 1 (```json) should take precedence."""
    text = (
        'Some text [{"intervention_type": "workshop"}]\n'
        '```json\n[{"intervention_type": "tool_demo"}]\n```'
    )
    result = OrchestratorAgent._find_json_array(text)
    assert "tool_demo" in result


def test_find_json_array_multiline():
    """Multi-line JSON in fenced block."""
    text = '```json\n[\n  {\n    "intervention_type": "workshop",\n    "target_persona": "skeptical_ic",\n    "content": "test",\n    "rationale": "testing"\n  }\n]\n```'
    result = OrchestratorAgent._find_json_array(text)
    assert result is not None
    assert "workshop" in result


# ── _extract_json_objects ─────────────────────────────────────

def test_extract_json_objects_single():
    raw = '[{"intervention_type": "workshop", "target_persona": "skeptical_ic"}]'
    result = OrchestratorAgent._extract_json_objects(raw)
    assert len(result) == 1
    assert result[0]["intervention_type"] == "workshop"


def test_extract_json_objects_multiple():
    raw = (
        '[{"intervention_type": "workshop", "target_persona": "skeptical_ic"}, '
        '{"intervention_type": "tool_demo", "target_persona": "risk_averse_vp"}]'
    )
    result = OrchestratorAgent._extract_json_objects(raw)
    assert len(result) == 2


def test_extract_json_objects_with_control_chars():
    """Control characters should be cleaned before parsing."""
    raw = '[{"intervention_type": "workshop",\x00 "target_persona": "skeptical_ic"}]'
    result = OrchestratorAgent._extract_json_objects(raw)
    assert len(result) == 1


def test_extract_json_objects_trailing_comma():
    """Trailing commas before } should be cleaned."""
    raw = '[{"intervention_type": "workshop", "target_persona": "skeptical_ic",}]'
    result = OrchestratorAgent._extract_json_objects(raw)
    assert len(result) == 1


def test_extract_json_objects_completely_invalid():
    raw = "this is not json at all"
    result = OrchestratorAgent._extract_json_objects(raw)
    assert result == []


# ── _extract_interventions (end-to-end parsing) ──────────────

def test_extract_interventions_valid_fenced():
    agent = OrchestratorAgent.__new__(OrchestratorAgent)
    text = '''Here is my plan:
```json
[
  {
    "intervention_type": "workshop",
    "target_persona": "skeptical_ic",
    "content": "Hands-on coding session",
    "rationale": "Build trust through evidence"
  },
  {
    "intervention_type": "executive_briefing",
    "target_persona": "risk_averse_vp",
    "content": "ROI presentation",
    "rationale": "Address budget concerns"
  }
]
```'''
    result = agent._extract_interventions(text)
    assert len(result) == 2
    assert result[0].intervention_type == InterventionType.WORKSHOP
    assert result[0].target_persona == PersonaType.SKEPTICAL_IC
    assert result[1].intervention_type == InterventionType.EXECUTIVE_BRIEFING
    assert result[1].target_persona == PersonaType.RISK_AVERSE_VP


def test_extract_interventions_all_types():
    """Each intervention type should parse correctly."""
    agent = OrchestratorAgent.__new__(OrchestratorAgent)
    for itype in InterventionType:
        text = f'''```json
[{{"intervention_type": "{itype.value}", "target_persona": "skeptical_ic", "content": "test", "rationale": "test"}}]
```'''
        result = agent._extract_interventions(text)
        assert len(result) == 1
        assert result[0].intervention_type == itype


def test_extract_interventions_all_personas():
    """Each persona type should parse correctly."""
    agent = OrchestratorAgent.__new__(OrchestratorAgent)
    for ptype in PersonaType:
        text = f'''```json
[{{"intervention_type": "workshop", "target_persona": "{ptype.value}", "content": "test", "rationale": "test"}}]
```'''
        result = agent._extract_interventions(text)
        assert len(result) == 1
        assert result[0].target_persona == ptype


def test_extract_interventions_no_json():
    agent = OrchestratorAgent.__new__(OrchestratorAgent)
    result = agent._extract_interventions("I'll skip this week. No actions needed.")
    assert result == []


def test_extract_interventions_invalid_enum():
    """Invalid intervention_type or target_persona should be skipped."""
    agent = OrchestratorAgent.__new__(OrchestratorAgent)
    text = '''```json
[
  {"intervention_type": "invalid_type", "target_persona": "skeptical_ic", "content": "x", "rationale": "x"},
  {"intervention_type": "workshop", "target_persona": "skeptical_ic", "content": "y", "rationale": "y"}
]
```'''
    result = agent._extract_interventions(text)
    assert len(result) == 1  # invalid one skipped
    assert result[0].content == "y"


def test_extract_interventions_trailing_comma():
    """Trailing commas in LLM output should be handled."""
    agent = OrchestratorAgent.__new__(OrchestratorAgent)
    text = '''```json
[
  {
    "intervention_type": "workshop",
    "target_persona": "skeptical_ic",
    "content": "test",
    "rationale": "test",
  },
]
```'''
    result = agent._extract_interventions(text)
    assert len(result) == 1


def test_extract_interventions_control_characters():
    """Control characters embedded in strings should be cleaned."""
    agent = OrchestratorAgent.__new__(OrchestratorAgent)
    text = '```json\n[{"intervention_type": "workshop", "target_persona":\x01 "skeptical_ic", "content": "test\x02", "rationale": "test"}]\n```'
    result = agent._extract_interventions(text)
    assert len(result) == 1


def test_extract_interventions_missing_optional_fields():
    """content and rationale should default to empty string if missing."""
    agent = OrchestratorAgent.__new__(OrchestratorAgent)
    text = '''```json
[{"intervention_type": "workshop", "target_persona": "skeptical_ic"}]
```'''
    result = agent._extract_interventions(text)
    assert len(result) == 1
    assert result[0].content == ""
    assert result[0].rationale == ""


def test_extract_interventions_bare_json():
    """Bare JSON (no fences) should be extracted."""
    agent = OrchestratorAgent.__new__(OrchestratorAgent)
    text = 'My recommendation: [{"intervention_type": "one_on_one", "target_persona": "overwhelmed_it_admin", "content": "check-in", "rationale": "reduce load"}] as planned.'
    result = agent._extract_interventions(text)
    assert len(result) == 1
    assert result[0].intervention_type == InterventionType.ONE_ON_ONE
    assert result[0].target_persona == PersonaType.OVERWHELMED_IT_ADMIN
