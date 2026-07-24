import { redirect } from "next/navigation";

export default async function ExecutiveIntelligenceRedirect({ params }: { params: Promise<{ domain: string }> }) {
  const { domain } = await params;
  redirect(`/workspace/${encodeURIComponent(domain)}/intelligence`);
}
