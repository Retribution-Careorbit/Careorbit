import { QueryClient, QueryFunction } from "@tanstack/react-query";

function getToken(): string | null {
  return localStorage.getItem("careorbit_token");
}

function clearAuthState() {
  localStorage.removeItem("careorbit_token");
  localStorage.removeItem("careorbit_refresh_token");
  localStorage.removeItem("careorbit_user");
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

  const res = await fetch(url, {
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

    const res = await fetch(queryKey[0] as string, {
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
