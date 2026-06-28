"""
Module: knowledge.py

Purpose:
Defines models used by the Knowledge Acquisition Engine.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DocumentChunk:
    chunk_number: int
    content: str
    heading: Optional[str] = None
    start_line_number: Optional[int] = None
    end_line_number: Optional[int] = None


@dataclass
class KnowledgeEvidence:
    evidence_text: str
    extraction_method: str = "RULE_BASED"
    rule_name: Optional[str] = None
    rule_version: Optional[str] = None
    extractor_name: Optional[str] = None
    start_line_number: Optional[int] = None
    end_line_number: Optional[int] = None
    evidence_json: dict = field(default_factory=dict)


@dataclass
class KnowledgeConfidence:
    rule_score: float = 0.0
    context_score: float = 0.0
    structure_score: float = 0.0
    frequency_score: float = 0.0
    metadata_match_score: float = 0.0
    semantic_match_score: float = 0.0
    ai_validation_score: Optional[float] = None
    final_score: float = 0.0
    confidence_json: dict = field(default_factory=dict)


@dataclass
class KnowledgeItem:
    knowledge_type: str
    name: str
    description: Optional[str] = None
    status: str = "ACTIVE"
    canonical_flag: bool = True
    knowledge_json: dict = field(default_factory=dict)
    evidence: list[KnowledgeEvidence] = field(default_factory=list)
    confidence: KnowledgeConfidence = field(default_factory=KnowledgeConfidence)


@dataclass
class AcquiredDocument:
    title: str
    document_type: str
    source_type: str
    source_location: str
    content_hash: str
    chunks: list[DocumentChunk] = field(default_factory=list)
    knowledge_items: list[KnowledgeItem] = field(default_factory=list)