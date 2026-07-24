"use client";

import { ArrowUp, Sparkles } from "lucide-react";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

export default function ContextualAsk({ domain, prompt = "Ask Sapientia about this business area…", compact = false }: { domain: string; prompt?: string; compact?: boolean }) {
  const router = useRouter();
  const [question, setQuestion] = useState("");

  function submit(event: FormEvent) {
    event.preventDefault();
    const value = question.trim();
    const target = `/workspace/${domain.toUpperCase()}/ai${value ? `?q=${encodeURIComponent(value)}` : ""}`;
    router.push(target);
  }

  return (
    <form className={`ux-ask ${compact ? "ux-ask-compact" : ""}`} onSubmit={submit}>
      <span className="ux-ask-mark"><Sparkles size={17} aria-hidden="true" /></span>
      <input aria-label="Ask Sapientia" value={question} onChange={(event) => setQuestion(event.target.value)} placeholder={prompt} />
      <button aria-label="Ask Sapientia" disabled={!question.trim()} type="submit"><ArrowUp size={17} /></button>
    </form>
  );
}
