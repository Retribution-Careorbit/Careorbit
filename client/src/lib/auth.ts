import { create } from "zustand";

interface User {
  id: string;
  email: string;
  name?: string;
  onboardingComplete?: boolean;
  preferredLanguage?: string;
}

interface AuthState {
  token: string | null;
  refreshToken: string | null;
  user: User | null;
  isAuthenticated: boolean;
  setAuth: (token: string, refreshToken: string, user: User) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  token: localStorage.getItem("careorbit_token"),
  refreshToken: localStorage.getItem("careorbit_refresh_token"),
  user: JSON.parse(localStorage.getItem("careorbit_user") || "null"),
  isAuthenticated: !!localStorage.getItem("careorbit_token"),
  setAuth: (token, refreshToken, user) => {
    localStorage.setItem("careorbit_token", token);
    localStorage.setItem("careorbit_refresh_token", refreshToken);
    localStorage.setItem("careorbit_user", JSON.stringify(user));
    set({ token, refreshToken, user, isAuthenticated: true });
  },
  logout: () => {
    localStorage.removeItem("careorbit_token");
    localStorage.removeItem("careorbit_refresh_token");
    localStorage.removeItem("careorbit_user");
    set({ token: null, refreshToken: null, user: null, isAuthenticated: false });
  },
}));

export async function authFetch(url: string, options: RequestInit = {}): Promise<Response> {
  const token = useAuthStore.getState().token;
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string> || {}),
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  if (!(options.body instanceof FormData)) {
    headers["Content-Type"] = headers["Content-Type"] || "application/json";
  }
  const response = await fetch(url, { ...options, headers });
  if (response.status === 401) {
    useAuthStore.getState().logout();
    if (window.location.pathname !== "/") {
      window.location.assign("/");
    }
  }
  return response;
}

export async function authPost(url: string, data: unknown): Promise<Response> {
  return authFetch(url, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function authGet(url: string): Promise<Response> {
  return authFetch(url, { method: "GET" });
}

export async function authDelete(url: string): Promise<Response> {
  return authFetch(url, { method: "DELETE" });
}
