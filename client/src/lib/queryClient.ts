import { QueryClient, QueryFunction } from "@tanstack/react-query";

const configuredApiBase = (import.meta.env.VITE_API_BASE_URL || "").trim();
const SWA_HOST_SUFFIX = ".azurestaticapps.net";
const SWA_FALLBACK_API_BASE = "https://careorbit-api-dev.azurewebsites.net";

const PATIENT_ID_STORAGE_KEY = "careorbit_active_patient_id";

function getToken(): string | null {
  return localStorage.getItem("careorbit_token");
}

function clearAuthState() {
  localStorage.removeItem("careorbit_token");
  localStorage.removeItem("careorbit_refresh_token");
  localStorage.removeItem("careorbit_user");
}

function trimTrailingSlash(url: string): string {
  return url.endsWith("/") ? url.slice(0, -1) : url;
}

export function getApiBaseUrl(): string {
  const host = window.location.hostname.toLowerCase();
  if (host.endsWith(SWA_HOST_SUFFIX)) {
    return SWA_FALLBACK_API_BASE;
  }

  if (configuredApiBase) {
    return trimTrailingSlash(configuredApiBase);
  }

  return "";
}

export function toApiUrl(url: string): string {
  if (!url.startsWith("/")) {
    return url;
  }
  const base = getApiBaseUrl();
  return base ? `${base}${url}` : url;
}

function maybeAppendPatientId(url: string): string {
  if (!url.startsWith("/api/")) return url;
  if (url.startsWith("/api/auth/")) return url;
  if (url.includes("patient_id=")) return url;

  const patientId = localStorage.getItem(PATIENT_ID_STORAGE_KEY);
  if (!patientId) return url;

  const separator = url.includes("?") ? "&" : "?";
  return `${url}${separator}patient_id=${encodeURIComponent(patientId)}`;
}

async function throwIfResNotOk(res: Response) {
  if (res.status === 401) {
    clearAuthState();
    // Redirect to login so the user can obtain a fresh token after deployments/secret rotations.
    if (window.location.pathname !== "/") {
      window.location.assign("/");
    }
    throw new Error("Session expired. Please log in again.");
  }

  if (!res.ok) {
    const text = (await res.text()) || res.statusText;
    throw new Error(`${res.status}: ${text}`);
  }
}

export async function apiRequest(
  method: string,
  url: string,
  data?: unknown | undefined,
): Promise<Response> {
  const headers: Record<string, string> = {};
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (data) headers["Content-Type"] = "application/json";

  const urlWithPatient = maybeAppendPatientId(url);

  const res = await fetch(toApiUrl(urlWithPatient), {
    method,
    headers,
    body: data ? JSON.stringify(data) : undefined,
  });

  await throwIfResNotOk(res);
  return res;
}

type UnauthorizedBehavior = "returnNull" | "throw";
export const getQueryFn: <T>(options: {
  on401: UnauthorizedBehavior;
}) => QueryFunction<T> =
  ({ on401: unauthorizedBehavior }) =>
  async ({ queryKey }) => {
    const headers: Record<string, string> = {};
    const token = getToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;

    const endpoint = maybeAppendPatientId(queryKey[0] as string);

    const res = await fetch(toApiUrl(endpoint), {
      headers,
    });

    if (unauthorizedBehavior === "returnNull" && res.status === 401) {
      return null;
    }

    await throwIfResNotOk(res);
    return await res.json();
  };

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      queryFn: getQueryFn({ on401: "throw" }),
      refetchInterval: false,
      refetchOnWindowFocus: false,
      staleTime: Infinity,
      retry: false,
    },
    mutations: {
      retry: false,
    },
  },
});
