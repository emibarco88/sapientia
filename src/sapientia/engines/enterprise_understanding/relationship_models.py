from __future__ import annotations
from dataclasses import dataclass,field
from typing import Any
@dataclass(frozen=True)
class ObjectReference:
 project_id:int; object_type_code:str; source_schema:str; source_table:str; source_object_id:int; canonical_name:str; canonical_key:str
 description:str|None=None; business_domain:str|None=None; metadata:dict[str,Any]=field(default_factory=dict)
@dataclass(frozen=True)
class EvidenceCandidate:
 evidence_type:str; evidence_key:str; evidence_score:float; reasoning:str
 source_schema:str|None=None; source_table:str|None=None; source_record_id:int|None=None; evidence:dict[str,Any]=field(default_factory=dict)
@dataclass(frozen=True)
class RelationshipCandidate:
 source:ObjectReference; target:ObjectReference; relationship_type_code:str; generation_method:str; confidence_score:float; reasoning:str
 discovery_class:str='DISCOVERED'; metadata:dict[str,Any]=field(default_factory=dict); evidence:tuple[EvidenceCandidate,...]=()
@dataclass(frozen=True)
class RelationshipBuildResult:
 understanding_run_id:int; understanding_snapshot_id:int; project_id:int; objects_registered:int; relationships_registered:int; evidence_registered:int; strategy_counts:dict[str,int]; warnings:tuple[str,...]=()
 def to_dict(self)->dict[str,Any]: return {'understanding_run_id':self.understanding_run_id,'understanding_snapshot_id':self.understanding_snapshot_id,'project_id':self.project_id,'objects_registered':self.objects_registered,'relationships_registered':self.relationships_registered,'evidence_registered':self.evidence_registered,'strategy_counts':dict(self.strategy_counts),'warnings':list(self.warnings)}
