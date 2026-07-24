import { apiFetch } from "@/lib/api";

export type EvidenceReference = {
  evidence_id: number | string;
  evidence_type: string;
  support_status: string;
  title: string;
  excerpt?: string | null;
  source?: string | null;
  confidence?: number | null;
  enterprise_object_id?: number | null;
  dataset_id?: number | null;
  column_id?: number | null;
  knowledge_item_id?: number | null;
};

export type NarrativeStatement = {
  statement_id: string;
  section: string;
  headline: string;
  text: string;
  support_status: string;
  generated_by: string;
  confidence?: number | null;
  intelligence_object_ids: number[];
  business_object_ids: number[];
  evidence: EvidenceReference[];
};

export type IntelligenceObject = {
  intelligence_object_id: number;
  assessment_id: number;
  object_type: string;
  object_key: string;
  title: string;
  description?: string | null;
  interpretation?: string | null;
  status: string;
  severity?: string | null;
  priority?: string | null;
  confidence_score?: number | null;
  impact_score?: number | null;
  enterprise_object_id?: number | null;
  evidence_count: number;
};

export type BusinessHealth = {
  label: string;
  score?: number | null;
  explanation: string;
  confidence: number;
  evidence_coverage: number;
  positive_drivers: NarrativeStatement[];
  negative_drivers: NarrativeStatement[];
};

export type NarrativePayload = {
  experience_version: string;
  narrative_schema_version: string;
  project_id: number;
  business_domain: string;
  assessment: {
    assessment_id: number;
    assessment_version: number;
    assessment_status: string;
    assessment_title: string;
    generated_at: string;
    overall_confidence?: number | null;
  };
  executive_summary: NarrativeStatement;
  business_health: BusinessHealth;
  sections: {
    current_state: NarrativeStatement[];
    what_changed: NarrativeStatement[];
    why_it_changed: NarrativeStatement[];
    risks: IntelligenceObject[];
    opportunities: IntelligenceObject[];
    recommendations: IntelligenceObject[];
  };
  provenance: {
    generated_by: string;
    generated_at: string;
    source: string;
    intelligence_object_count: number;
  };
};

export type TimelineEvent = {
  timeline_event_id: string;
  assessment_id: number;
  assessment_version?: number | null;
  event_type: string;
  title: string;
  description: string;
  occurred_at: string;
  confidence?: number | null;
  object_count: number;
  changes: { new?: number | null; changed?: number | null; resolved?: number | null; confidence_delta?: number | null };
};

export type TimelinePayload = { project_id: number; business_domain: string; timeline: TimelineEvent[] };

export type BusinessObjectProfile = {
  experience_version: string;
  project_id: number;
  business_domain: string;
  enterprise_object_id: number;
  name: string;
  description?: string | null;
  object_type: string;
  confidence?: number | null;
  current_assessment_id?: number | null;
  intelligence_objects: IntelligenceObject[];
  evidence: EvidenceReference[];
  summary: string;
};

const q = (value: string) => encodeURIComponent(value);

export const intelligenceExperienceApi = {
  narrative: (domain: string, projectId = 1) =>
    apiFetch<NarrativePayload>(`/intelligence-experience/domains/${q(domain)}/narrative?project_id=${projectId}`),
  refreshStory: (domain: string, projectId = 1) =>
    apiFetch<NarrativePayload>(`/intelligence-experience/domains/${q(domain)}/story?project_id=${projectId}`, {
      method: "POST",
      body: JSON.stringify({ force_refresh: true, tone: "executive", ai_mode: "deterministic" }),
    }),
  health: (domain: string, projectId = 1) =>
    apiFetch<BusinessHealth>(`/intelligence-experience/domains/${q(domain)}/health?project_id=${projectId}`),
  timeline: (domain: string, projectId = 1, limit = 30) =>
    apiFetch<TimelinePayload>(`/intelligence-experience/domains/${q(domain)}/timeline?project_id=${projectId}&limit=${limit}`),
  profile: (domain: string, objectId: number, projectId = 1) =>
    apiFetch<BusinessObjectProfile>(`/intelligence-experience/business-objects/${objectId}/profile?domain_code=${q(domain)}&project_id=${projectId}`),
  explain: (statementId: string) =>
    apiFetch<{ statement: NarrativeStatement; evidence: EvidenceReference[] }>(`/intelligence-experience/statements/${q(statementId)}/explain`, { method: "POST" }),
};
