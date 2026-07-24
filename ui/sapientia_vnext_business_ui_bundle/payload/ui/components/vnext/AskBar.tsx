"use client";

import { ArrowRight, Sparkles } from "lucide-react";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

export default function AskBar({ domain, prompt = "What would you like to understand?" }: { domain: string; prompt?: string }) {
  const router = useRouter();
  const [question, setQuestion] = useState("");
  function submit(event: FormEvent) {
    event.preventDefault();
    const value = question.trim();
    const target = `/workspace/${encodeURIComponent(domain)}/ai${value ? `?question=${encodeURIComponent(value)}` : ""}`;
    router.push(target);
  }
  return (
    <form className="vnext-askbar" onSubmit={submit}>
      <Sparkles size={21} />
      <input aria-label="Ask Sapientia" value={question} onChange={(event) => setQuestion(event.target.value)} placeholder={prompt} />
      <button type="submit" aria-label="Ask"><ArrowRight size={18} /></button>
    </form>
  );
}
