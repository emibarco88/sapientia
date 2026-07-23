from __future__ import annotations
from dataclasses import dataclass
from typing import Any
@dataclass(frozen=True)
class ContextBuildResult:
    project_id:int; understanding_snapshot_id:int; contexts_registered:int; facts_registered:int; warnings:tuple[str,...]=()
    def to_dict(self)->dict[str,Any]: return {"project_id":self.project_id,"understanding_snapshot_id":self.understanding_snapshot_id,"contexts_registered":self.contexts_registered,"facts_registered":self.facts_registered,"warnings":list(self.warnings)}
