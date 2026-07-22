"use client";

import {
  ArrowUp,
  BookOpenCheck,
  CheckCircle2,
  MessageSquareText,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import { useParams } from "next/navigation";
import { FormEvent, useState } from "react";

import AppShell from "@/components/layout/AppShell";
import { apiFetch } from "@/lib/api";

type AdvisorResponse = {
  answer: string;
  concepts_used?: number;
  findings_used?: number;
  fusion_links_used?: number;
  retrieval_mode?: string;
  fallback_used?: boolean;
};

const suggestedQuestions = [
  "What are the most important findings I should review?",
  "Explain how this part of the business works.",
  "Which risks or exceptions need attention?",
  "What evidence supports the latest intelligence?",
];

export default function EnterpriseAgentPage() {
  const params = useParams();
  const domain = String(params.domain).toUpperCase();
  const [question, setQuestion] = useState("");
  const [response, setResponse] = useState<AdvisorResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function ask(event?: FormEvent) {
    event?.preventDefault();
    const cleanQuestion = question.trim();
    if (!cleanQuestion || loading) return;

    setLoading(true);
    setError("");

    try {
      const result = await apiFetch<AdvisorResponse>("/ai-advisor/ask", {
        method: "POST",
        body: JSON.stringify({
          project_id: 1,
          business_domain: domain,
          question: cleanQuestion,
        }),
      });
      setResponse(result);
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "The AI Advisor could not answer this question.",
      );
    } finally {
      setLoading(false);
    }
  }

  function useSuggestion(value: string) {
    setQuestion(value);
    setResponse(null);
    setError("");
  }

  return (
    <AppShell>
      <div className="sap-page ai-advisor-page">
        <header className="sap-page-header ai-advisor-heading">
          <div className="sap-page-header-copy">
            <span className="sap-eyebrow">AI Advisor</span>
            <h1 className="sap-page-title">Ask your enterprise</h1>
            <p className="sap-page-description">
              Explore {domain} using answers grounded in enterprise knowledge,
              intelligence findings and supporting evidence.
            </p>
          </div>
          <span className="ai-ready-pill">
            <CheckCircle2 size={15} aria-hidden="true" /> Ready
          </span>
        </header>

        <section className="ai-composer-panel">
          <div className="ai-composer-intro">
            <span className="ai-orb"><Sparkles size={24} aria-hidden="true" /></span>
            <div>
              <h2>What would you like to understand?</h2>
              <p>Ask about performance, risks, business processes, evidence or change.</p>
            </div>
          </div>

          <form className="ai-composer" onSubmit={ask}>
            <textarea
              aria-label="Question for the AI Advisor"
              placeholder="Ask a business question in plain language..."
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              rows={4}
            />
            <button disabled={loading || !question.trim()} type="submit">
              {loading ? "Thinking" : "Ask Sapientia"}
              <ArrowUp size={17} aria-hidden="true" />
            </button>
          </form>
        </section>

        {error && <div className="friendly-alert">{error}</div>}

        {response ? (
          <section className="ai-answer-panel" aria-live="polite">
            <div className="ai-answer-heading">
              <span><MessageSquareText size={20} aria-hidden="true" /></span>
              <div>
                <span className="sap-eyebrow">Sapientia&apos;s answer</span>
                <h2>Enterprise explanation</h2>
              </div>
            </div>
            <div className="ai-answer-copy">{response.answer}</div>
            <footer className="ai-trust-row">
              <span><ShieldCheck size={15} /> Grounded in enterprise context</span>
              <span><BookOpenCheck size={15} />
                {Number(response.concepts_used || 0) + Number(response.findings_used || 0)} knowledge items considered
              </span>
            </footer>
          </section>
        ) : (
          <section className="ai-suggestions">
            <div>
              <span className="sap-eyebrow">Suggested questions</span>
              <h2>Start with a business question</h2>
            </div>
            <div className="ai-suggestion-grid">
              {suggestedQuestions.map((suggestion) => (
                <button key={suggestion} type="button" onClick={() => useSuggestion(suggestion)}>
                  <MessageSquareText size={17} aria-hidden="true" />
                  <span>{suggestion}</span>
                </button>
              ))}
            </div>
          </section>
        )}
      </div>
    </AppShell>
  );
}
