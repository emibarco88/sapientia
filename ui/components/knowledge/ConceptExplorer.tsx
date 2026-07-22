"use client";

import { CheckCircle2, Search, SlidersHorizontal } from "lucide-react";
import { useMemo, useState } from "react";

export type KnowledgeConcept = {
  enterprise_concept_id: number;
  concept_name: string;
  concept_type: string;
  concept_description: string | null;
  confidence_score: number | null;
  evidence_count: number;
};

type ConceptExplorerProps = {
  concepts: KnowledgeConcept[];
};

export default function ConceptExplorer({ concepts }: ConceptExplorerProps) {
  const [query, setQuery] = useState("");
  const [typeFilter, setTypeFilter] = useState("all");

  const types = useMemo(
    () => Array.from(new Set(concepts.map((concept) => concept.concept_type).filter(Boolean))).sort(),
    [concepts],
  );

  const filteredConcepts = useMemo(() => {
    const search = query.trim().toLowerCase();
    return concepts.filter((concept) => {
      const matchesType = typeFilter === "all" || concept.concept_type === typeFilter;
      const matchesSearch = !search || [concept.concept_name, concept.concept_description, concept.concept_type]
        .filter(Boolean)
        .some((value) => String(value).toLowerCase().includes(search));
      return matchesType && matchesSearch;
    });
  }, [concepts, query, typeFilter]);

  return (
    <section className="knowledge-explorer-section">
      <div className="sap-section-header">
        <div>
          <span className="sap-eyebrow">Concept explorer</span>
          <h2 className="sap-section-title">Enterprise concepts</h2>
          <p className="sap-section-description">
            Search the business language Sapientia has identified and review the evidence supporting it.
          </p>
        </div>
        <span className="knowledge-result-count">{filteredConcepts.length} of {concepts.length}</span>
      </div>

      <div className="knowledge-toolbar">
        <label className="knowledge-search">
          <Search size={17} aria-hidden="true" />
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search concepts, descriptions or types"
            aria-label="Search enterprise concepts"
          />
        </label>
        <label className="knowledge-filter">
          <SlidersHorizontal size={16} aria-hidden="true" />
          <select value={typeFilter} onChange={(event) => setTypeFilter(event.target.value)} aria-label="Filter concepts by type">
            <option value="all">All concept types</option>
            {types.map((type) => <option value={type} key={type}>{humanise(type)}</option>)}
          </select>
        </label>
      </div>

      {filteredConcepts.length ? (
        <div className="knowledge-concept-grid">
          {filteredConcepts.map((concept) => {
            const confidence = concept.confidence_score == null
              ? null
              : Math.round(Number(concept.confidence_score) * 100);

            return (
              <article className="knowledge-concept" key={concept.enterprise_concept_id}>
                <div className="knowledge-concept-heading">
                  <span className="knowledge-concept-type">{humanise(concept.concept_type)}</span>
                  <CheckCircle2 size={17} aria-hidden="true" />
                </div>
                <h3>{concept.concept_name}</h3>
                <p>{concept.concept_description || "A recognised concept within the enterprise knowledge model."}</p>
                <div className="knowledge-evidence-row">
                  <span><strong>{concept.evidence_count || 0}</strong> evidence records</span>
                  {confidence != null && <span><strong>{confidence}%</strong> confidence</span>}
                </div>
                {confidence != null && (
                  <div className="knowledge-confidence" aria-label={`${confidence}% confidence`}>
                    <span style={{ width: `${Math.max(0, Math.min(100, confidence))}%` }} />
                  </div>
                )}
              </article>
            );
          })}
        </div>
      ) : (
        <div className="knowledge-empty-filter">
          <Search size={22} aria-hidden="true" />
          <h3>No concepts match your search</h3>
          <p>Try another keyword or remove the concept type filter.</p>
        </div>
      )}
    </section>
  );
}

function humanise(value: string) {
  return value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}
