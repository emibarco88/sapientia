from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def test_contracts():
 s=(ROOT/'src/sapientia/services/enterprise_intelligence_generation_service.py').read_text()
 assert 'resolve_current' in s and '_get_duplicate_assessment_by_knowledge_version' in s
 k=(ROOT/'src/sapientia/services/knowledge/enterprise_knowledge_version_service.py').read_text()
 assert 'enterprise_knowledge_version' in k and 'ekr_core.column' in k and 'column_semantic' in k
 a=(ROOT/'src/sapientia/services/intelligence/assessment_service.py').read_text()
 assert 'knowledge_version_id' in a
