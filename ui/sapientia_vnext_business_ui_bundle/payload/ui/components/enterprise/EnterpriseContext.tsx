"use client";

import { usePathname, useRouter } from "next/navigation";
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { apiFetch } from "@/lib/api";

export type BusinessArea = {
  business_domain_id?: number;
  domain_code: string;
  domain_name?: string;
  description?: string | null;
  datasets?: number;
  concepts?: number;
  intelligence_reports?: number;
};

type EnterpriseContextValue = {
  enterpriseName: string;
  businessAreas: BusinessArea[];
  selectedBusinessArea: BusinessArea | null;
  loadingBusinessAreas: boolean;
  businessAreaError: string;
  selectBusinessArea: (domainCode: string, navigate?: boolean) => void;
  refreshBusinessAreas: () => Promise<void>;
};

const EnterpriseContext = createContext<EnterpriseContextValue | null>(null);
const STORAGE_KEY = "sapientia.selectedBusinessArea";

function routeDomain(pathname: string): string | null {
  const match = pathname.match(/^\/(?:workspace|domains)\/([^/]+)/i);
  return match?.[1] ? decodeURIComponent(match[1]).toUpperCase() : null;
}

function destinationFor(pathname: string, domainCode: string): string {
  const code = encodeURIComponent(domainCode.toUpperCase());
  if (/\/explorer(?:\/|$)/i.test(pathname)) return `/workspace/${code}/explorer`;
  if (/\/(?:ai|ask)(?:\/|$)/i.test(pathname)) return `/workspace/${code}/ai`;
  if (/\/reports(?:\/|$)/i.test(pathname)) return `/workspace/${code}/reports`;
  if (/\/intelligence(?:\/|$)/i.test(pathname)) return `/workspace/${code}/intelligence`;
  return `/domains/${code}`;
}

export function EnterpriseProvider({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [businessAreas, setBusinessAreas] = useState<BusinessArea[]>([]);
  const [selectedCode, setSelectedCode] = useState("");
  const [loadingBusinessAreas, setLoadingBusinessAreas] = useState(true);
  const [businessAreaError, setBusinessAreaError] = useState("");

  const refreshBusinessAreas = useCallback(async () => {
    setLoadingBusinessAreas(true);
    setBusinessAreaError("");
    try {
      const response = await apiFetch<BusinessArea[]>("/domains");
      const areas = Array.isArray(response)
        ? response.filter((area) => Boolean(area?.domain_code)).map((area) => ({ ...area, domain_code: area.domain_code.toUpperCase() }))
        : [];
      setBusinessAreas(areas);
      const routeCode = routeDomain(pathname);
      const storedCode = typeof window !== "undefined" ? window.localStorage.getItem(STORAGE_KEY)?.toUpperCase() || "" : "";
      const nextCode = areas.find((area) => area.domain_code === (routeCode || storedCode))?.domain_code || areas[0]?.domain_code || "";
      setSelectedCode(nextCode);
      if (nextCode && typeof window !== "undefined") window.localStorage.setItem(STORAGE_KEY, nextCode);
    } catch (cause) {
      setBusinessAreaError(cause instanceof Error ? cause.message : "Business domains could not be loaded.");
      setBusinessAreas([]);
    } finally {
      setLoadingBusinessAreas(false);
    }
  }, [pathname]);

  useEffect(() => { void refreshBusinessAreas(); }, [refreshBusinessAreas]);
  useEffect(() => {
    const code = routeDomain(pathname);
    if (!code) return;
    setSelectedCode(code);
    if (typeof window !== "undefined") window.localStorage.setItem(STORAGE_KEY, code);
  }, [pathname]);

  const selectBusinessArea = useCallback((domainCode: string, navigate = true) => {
    const code = domainCode.toUpperCase();
    setSelectedCode(code);
    if (typeof window !== "undefined") window.localStorage.setItem(STORAGE_KEY, code);
    if (navigate) router.push(destinationFor(pathname, code));
  }, [pathname, router]);

  const selectedBusinessArea = useMemo(
    () => businessAreas.find((area) => area.domain_code === selectedCode) || null,
    [businessAreas, selectedCode],
  );

  return (
    <EnterpriseContext.Provider value={{
      enterpriseName: "Sapientia Enterprise",
      businessAreas,
      selectedBusinessArea,
      loadingBusinessAreas,
      businessAreaError,
      selectBusinessArea,
      refreshBusinessAreas,
    }}>
      {children}
    </EnterpriseContext.Provider>
  );
}

export function useEnterprise() {
  const context = useContext(EnterpriseContext);
  if (!context) throw new Error("useEnterprise must be used within EnterpriseProvider.");
  return context;
}
