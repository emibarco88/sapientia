import { redirect } from "next/navigation";
export default async function LegacyWorkspacePage({ params }: { params: Promise<{ domain: string }> }) {
  const { domain } = await params;
  redirect(`/domains/${encodeURIComponent(domain.toUpperCase())}`);
}
