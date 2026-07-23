"use client";

import { useCallback, useEffect, useState } from "react";

import { loadEnterpriseGraph } from "@/features/explorer/lib/explorer-api";
import type { EnterpriseGraphResponse } from "@/features/explorer/types/explorer";

export function useEnterpriseGraph({
  projectId,
  domain,
  minimumConfidence,
}: {
  projectId: number;
  domain: string;
  minimumConfidence: number;
}) {
  const [graph, setGraph] = useState<EnterpriseGraphResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const refresh = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      setGraph(
        await loadEnterpriseGraph({
          projectId,
          domain,
          minimumConfidence,
        }),
      );
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "The enterprise graph could not be loaded.",
      );
    } finally {
      setLoading(false);
    }
  }, [domain, minimumConfidence, projectId]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return { graph, loading, error, refresh };
}
