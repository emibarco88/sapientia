"use client";

import { usePathname, useRouter } from "next/navigation";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

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

function destinationFor(pathname: string, domainCode: string): string | null {
  const code = encodeURIComponent(domainCode.toUpperCase());

  if (/^\/workspace\/[^/]+\/reports(?:\/|$)/i.test(pathname)) {
    return `/workspace/${code}/reports`;
  }

  if (/^\/workspace\/[^/]+\/ai(?:\/|$)/i.test(pathname)) {
    return `/workspace/${code}/ai`;
  }

  if (/^\/domains\/[^/]+\/ask(?:\/|$)/i.test(pathname)) {
    return `/domains/${code}/ask`;
  }

  if (/^\/domains\/[^/]+(?:\/|$)/i.test(pathname)) {
    return `/domains/${code}`;
  }

  if (/^\/workspace\/[^/]+(?:\/|$)/i.test(pathname)) {
    return `/workspace/${code}`;
  }

  return null;
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
        ? response
            .filter((area) => Boolean(area?.domain_code))
            .map((area) => ({
              ...area,
              domain_code: area.domain_code.toUpperCase(),
            }))
        : [];

      setBusinessAreas(areas);

      const codeFromRoute = routeDomain(pathname);
      const storedCode = typeof window !== "undefined"
        ? window.localStorage.getItem(STORAGE_KEY)?.toUpperCase() || ""
        : "";
      const preferredCode = codeFromRoute || storedCode;
      const validPreferred = areas.find((area) => area.domain_code === preferredCode);
      const nextCode = validPreferred?.domain_code || areas[0]?.domain_code || "";

      setSelectedCode(nextCode);
      if (nextCode && typeof window !== "undefined") {
        window.localStorage.setItem(STORAGE_KEY, nextCode);
      }
    } catch (cause) {
      setBusinessAreaError(
        cause instanceof Error ? cause.message : "Business areas could not be loaded.",
      );
      setBusinessAreas([]);
    } finally {
      setLoadingBusinessAreas(false);
    }
  }, [pathname]);

  useEffect(() => {
    void refreshBusinessAreas();
  }, [refreshBusinessAreas]);

  useEffect(() => {
    const codeFromRoute = routeDomain(pathname);
    if (!codeFromRoute) return;

    setSelectedCode(codeFromRoute);
    if (typeof window !== "undefined") {
      window.localStorage.setItem(STORAGE_KEY, codeFromRoute);
    }
  }, [pathname]);

  const selectBusinessArea = useCallback(
    (domainCode: string, navigate = true) => {
      const code = domainCode.toUpperCase();
      setSelectedCode(code);

      if (typeof window !== "undefined") {
        window.localStorage.setItem(STORAGE_KEY, code);
      }

      if (!navigate) return;
      const destination = destinationFor(pathname, code);
      if (destination && destination !== pathname) {
        router.push(destination);
      }
    },
    [pathname, router],
  );

  const selectedBusinessArea = useMemo(
    () => businessAreas.find((area) => area.domain_code === selectedCode) || null,
    [businessAreas, selectedCode],
  );

  const value = useMemo<EnterpriseContextValue>(
    () => ({
      enterpriseName: "Sapientia Enterprise",
      businessAreas,
      selectedBusinessArea,
      loadingBusinessAreas,
      businessAreaError,
      selectBusinessArea,
      refreshBusinessAreas,
    }),
    [
      businessAreas,
      businessAreaError,
      loadingBusinessAreas,
      refreshBusinessAreas,
      selectBusinessArea,
      selectedBusinessArea,
    ],
  );

  return <EnterpriseContext.Provider value={value}>{children}</EnterpriseContext.Provider>;
}

export function useEnterprise() {
  const context = useContext(EnterpriseContext);
  if (!context) {
    throw new Error("useEnterprise must be used within EnterpriseProvider.");
  }
  return context;
}
