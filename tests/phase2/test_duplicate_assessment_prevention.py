from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def test_backend_duplicate_guard_is_present():
    source = (ROOT / "src/sapientia/services/enterprise_intelligence_generation_service.py").read_text()
    assert '"status": "NO_CHANGE"' in source
    assert '"duplicate_prevented": True' in source
    assert "knowledge_fingerprint" in source
    assert "if duplicate and not force" in source

def test_force_flag_is_exposed():
    router = (ROOT / "api/routers/intelligence.py").read_text()
    assert "force: bool = False" in router
    assert "force=payload.force" in router

def test_assessment_records_input_fingerprint():
    source = (ROOT / "src/sapientia/services/intelligence/assessment_service.py").read_text()
    assert '"knowledge_fingerprint"' in source
    assert '"knowledge_snapshot"' in source
    assert '"generation_reason"' in source
