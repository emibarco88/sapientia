from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SERVICE = ROOT / "src/sapientia/services/enterprise_intelligence_generation_service.py"

def test_snapshot_uses_repository_connector_schema():
    source = SERVICE.read_text()
    assert "c.connector_type_id" in source
    assert "ct.connector_code" in source
    assert "JOIN ekr_connection.connector_type ct" in source
    assert "c.connector_type," not in source
