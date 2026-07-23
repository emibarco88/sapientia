from __future__ import annotations
from collections import defaultdict, deque
from sapientia.db.connection import get_engine
from sapientia.engines.enterprise_reasoning.models import DependencyEdge, DependencyPath, ImpactResult
from sapientia.repositories.reasoning.reasoning_repository import ReasoningRepository

class EnterpriseReasoningEngine:
    """Deterministic graph reasoning over enterprise objects and relationships."""
    def __init__(self, database_engine=None):
        self.database_engine = database_engine or get_engine()

    @staticmethod
    def _critical_nodes(edges: list[DependencyEdge]) -> set[int]:
        incoming: dict[int,int] = defaultdict(int); outgoing: dict[int,int] = defaultdict(int)
        for edge in edges:
            outgoing[edge.source_id] += 1; incoming[edge.target_id] += 1
        all_nodes = set(incoming) | set(outgoing)
        if not all_nodes: return set()
        scores = {n: incoming[n] + outgoing[n] for n in all_nodes}
        threshold = max(2, sorted(scores.values())[max(0, int(len(scores) * .75) - 1)])
        return {n for n, score in scores.items() if score >= threshold}

    @staticmethod
    def _paths(origin: int, edges: list[DependencyEdge], direction: str, max_depth: int) -> list[DependencyPath]:
        adjacency: dict[int,list[tuple[int,DependencyEdge]]] = defaultdict(list)
        for edge in edges:
            if direction in ('DOWNSTREAM','BOTH'): adjacency[edge.source_id].append((edge.target_id, edge))
            if direction in ('UPSTREAM','BOTH'): adjacency[edge.target_id].append((edge.source_id, edge))
        paths: list[DependencyPath] = []
        queue = deque([(origin, (origin,), tuple(), 1.0)])
        while queue:
            current, nodes, edge_ids, confidence = queue.popleft()
            if len(nodes) - 1 >= max_depth: continue
            for nxt, edge in adjacency.get(current, []):
                if nxt in nodes: continue
                next_nodes = nodes + (nxt,)
                next_edge_ids = edge_ids + ((edge.relationship_id or 0),)
                next_confidence = round(confidence * edge.confidence, 6)
                paths.append(DependencyPath(next_nodes, next_edge_ids, next_confidence))
                queue.append((nxt, next_nodes, next_edge_ids, next_confidence))
        return sorted(paths, key=lambda p: (p.depth, -p.confidence, p.object_ids))

    @staticmethod
    def _root_causes(origin: int, paths: list[DependencyPath], edges: list[DependencyEdge], names: dict[int,str], limit: int=10):
        evidence_by_pair = {(e.source_id,e.target_id): e.evidence_count for e in edges}
        best: dict[int,dict] = {}
        for path in paths:
            candidate_id = path.object_ids[-1]
            evidence_count = sum(evidence_by_pair.get(pair,0) + evidence_by_pair.get((pair[1],pair[0]),0)
                                 for pair in zip(path.object_ids, path.object_ids[1:]))
            score = round(path.confidence * (1 / max(1,path.depth)) * min(1.0, .5 + .1 * evidence_count), 4)
            if candidate_id not in best or score > best[candidate_id]['confidence']:
                best[candidate_id] = {
                    "candidate_id": candidate_id, "confidence": score, "evidence_count": evidence_count,
                    "reasoning": f"{names.get(candidate_id,candidate_id)} reaches {names.get(origin,origin)} through a {path.depth}-step upstream dependency path.",
                    "path_object_ids": list(path.object_ids)
                }
        ranked = sorted(best.values(), key=lambda x: (-x['confidence'], x['candidate_id']))[:limit]
        for rank, item in enumerate(ranked, 1): item['rank'] = rank
        return ranked


    def analyse_domain(
        self,
        project_id: int,
        business_domain: str,
        max_depth: int = 6,
    ) -> dict:
        """
        Build one evidence-backed reasoning run for every active object
        in a business domain.

        Run metrics are stored in reasoning_run.summary_json so the
        implementation remains compatible with the current database
        schema.
        """
        normalized_domain = str(business_domain or "").strip().upper()
        if not normalized_domain:
            raise ValueError("A business domain is required.")
        if max_depth < 1 or max_depth > 25:
            raise ValueError("max_depth must be between 1 and 25")

        run_id = None
        try:
            with self.database_engine.begin() as connection:
                repo = ReasoningRepository(connection)
                snapshot_id = repo.latest_published_snapshot_id(project_id)
                if snapshot_id is None:
                    raise ValueError(
                        f"No published understanding snapshot found for project {project_id}."
                    )

                run_id = repo.create_run(
                    project_id=project_id,
                    snapshot_id=snapshot_id,
                    business_domain=normalized_domain,
                    run_type="DOMAIN_REASONING",
                )

                edges = repo.load_edges(project_id, normalized_domain)
                names = repo.object_names(project_id)
                domain_object_ids = sorted(
                    {
                        edge.source_id for edge in edges
                    }
                    | {
                        edge.target_id for edge in edges
                    }
                )

                critical_ids = self._critical_nodes(edges)
                repo.persist_edges(run_id, edges, critical_ids)

                total_paths = 0
                total_impacted = 0
                total_root_causes = 0
                confidence_values: list[float] = []

                for origin_id in domain_object_ids:
                    downstream_paths = self._paths(
                        origin_id,
                        edges,
                        "DOWNSTREAM",
                        max_depth,
                    )
                    impacted_ids = {
                        node
                        for path in downstream_paths
                        for node in path.object_ids[1:]
                    }
                    relevant_critical_ids = impacted_ids & critical_ids
                    confidence = (
                        round(
                            sum(path.confidence for path in downstream_paths)
                            / len(downstream_paths),
                            4,
                        )
                        if downstream_paths
                        else 0.0
                    )

                    repo.persist_impact(
                        run_id=run_id,
                        origin_id=origin_id,
                        direction="DOWNSTREAM",
                        max_depth=max_depth,
                        paths=downstream_paths,
                        impacted_ids=impacted_ids,
                        critical_ids=relevant_critical_ids,
                        confidence=confidence,
                        names=names,
                    )

                    upstream_paths = self._paths(
                        origin_id,
                        edges,
                        "UPSTREAM",
                        max_depth,
                    )
                    root_causes = self._root_causes(
                        origin_id,
                        upstream_paths,
                        edges,
                        names,
                    )
                    repo.persist_root_causes(
                        run_id,
                        origin_id,
                        root_causes,
                    )

                    total_paths += len(downstream_paths)
                    total_impacted += len(impacted_ids)
                    total_root_causes += len(root_causes)
                    if confidence > 0:
                        confidence_values.append(confidence)

                overall_confidence = (
                    round(
                        sum(confidence_values) / len(confidence_values),
                        4,
                    )
                    if confidence_values
                    else 0.0
                )

                summary = {
                    "project_id": project_id,
                    "business_domain": normalized_domain,
                    "understanding_snapshot_id": snapshot_id,
                    "object_count": len(domain_object_ids),
                    "edge_count": len(edges),
                    "impact_analysis_count": len(domain_object_ids),
                    "impacted_object_references": total_impacted,
                    "root_cause_candidate_count": total_root_causes,
                    "critical_object_count": len(critical_ids),
                    "path_count": total_paths,
                    "confidence": overall_confidence,
                }

                repo.complete_run(run_id, summary)

                return {
                    "reasoning_run_id": run_id,
                    "status": "COMPLETED",
                    **summary,
                }

        except Exception as exc:
            # The failed work transaction has already been rolled back.
            # Record the failure through a fresh transaction so PostgreSQL
            # never receives the update inside an aborted transaction.
            if run_id is not None:
                with self.database_engine.begin() as failure_connection:
                    ReasoningRepository(
                        failure_connection
                    ).fail_run(run_id, str(exc))
            raise

    def analyse(self, project_id: int, origin_object_id: int, direction: str='BOTH', max_depth: int=6,
                business_domain: str | None=None) -> ImpactResult:
        direction = direction.upper()
        if direction not in {'UPSTREAM','DOWNSTREAM','BOTH'}: raise ValueError('direction must be UPSTREAM, DOWNSTREAM or BOTH')
        if max_depth < 1 or max_depth > 25: raise ValueError('max_depth must be between 1 and 25')
        with self.database_engine.begin() as connection:
            repo = ReasoningRepository(connection)
            snapshot_id = repo.latest_published_snapshot_id(project_id)
            if snapshot_id is None: raise ValueError(f'No published understanding snapshot found for project {project_id}.')
            run_id = repo.create_run(project_id, snapshot_id, business_domain)
            try:
                edges = repo.load_edges(project_id, business_domain)
                names = repo.object_names(project_id)
                if origin_object_id not in names: raise ValueError(f'Enterprise object {origin_object_id} is not active for project {project_id}.')
                critical_ids = self._critical_nodes(edges)
                paths = self._paths(origin_object_id, edges, direction, max_depth)
                impacted_ids = {node for path in paths for node in path.object_ids if node != origin_object_id}
                relevant_critical = impacted_ids & critical_ids
                confidence = round(sum(p.confidence for p in paths) / len(paths), 4) if paths else 0.0
                repo.persist_edges(run_id, edges, critical_ids)
                repo.persist_impact(run_id, origin_object_id, direction, max_depth, paths, impacted_ids, relevant_critical, confidence, names)
                root_causes = self._root_causes(origin_object_id, self._paths(origin_object_id, edges, 'UPSTREAM', max_depth), edges, names)
                repo.persist_root_causes(run_id, origin_object_id, root_causes)
                result = ImpactResult(run_id, origin_object_id, direction, tuple(paths), tuple(sorted(impacted_ids)), tuple(sorted(relevant_critical)), confidence, tuple(root_causes))
                repo.complete_run(run_id, result.to_dict())
                return result
            except Exception as exc:
                repo.fail_run(run_id, str(exc)); raise