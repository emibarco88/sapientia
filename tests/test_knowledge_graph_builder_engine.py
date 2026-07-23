from sapientia.engines.knowledge_graph_builder.knowledge_graph_builder_engine import (
    KnowledgeGraphBuilderEngine,
)


def test_stable_bigint_is_deterministic():
    first = KnowledgeGraphBuilderEngine._stable_bigint("business:finance:invoice")
    second = KnowledgeGraphBuilderEngine._stable_bigint("business:finance:invoice")
    assert first == second
    assert first > 0


def test_candidate_detection_groups_business_objects():
    engine = KnowledgeGraphBuilderEngine()
    rows = [
        {
            "column_id": 1,
            "column_name": "INVOICE_AMOUNT",
            "dataset_name": "THREE_WAY_MATCH",
            "semantic_type": "AMOUNT",
            "business_meaning": "Invoice amount",
        },
        {
            "column_id": 2,
            "column_name": "PO_NUMBER",
            "dataset_name": "THREE_WAY_MATCH",
            "semantic_type": "PURCHASE_ORDER_IDENTIFIER",
            "business_meaning": "Purchase order number",
        },
        {
            "column_id": 3,
            "column_name": "CURRENCY",
            "dataset_name": "THREE_WAY_MATCH",
            "semantic_type": "CURRENCY_CODE",
            "business_meaning": "Transaction currency",
        },
    ]
    candidates = engine._identify_candidates(rows)
    assert "INVOICE" in candidates
    assert "PURCHASE_ORDER" in candidates
    assert "CURRENCY" in candidates
