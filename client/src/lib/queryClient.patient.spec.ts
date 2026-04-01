import { beforeEach, describe, expect, it, vi } from "vitest";

import { apiRequest, getQueryFn } from "./queryClient";

class LocalStorageMock {
  private store = new Map<string, string>();

  getItem(key: string): string | null {
    return this.store.has(key) ? this.store.get(key)! : null;
  }

  setItem(key: string, value: string): void {
    this.store.set(key, String(value));
  }

  removeItem(key: string): void {
    this.store.delete(key);
  }

  clear(): void {
    this.store.clear();
  }
}

function okResponse(body: unknown = {}): any {
  return {
    ok: true,
    status: 200,
    statusText: "OK",
    json: async () => body,
    text: async () => JSON.stringify(body),
  };
}

describe("query client patient scoping", () => {
  const storage = new LocalStorageMock();

  beforeEach(() => {
    (globalThis as any).localStorage = storage;
    storage.clear();

    (globalThis as any).window = {
      location: {
        hostname: "localhost",
        pathname: "/",
        assign: vi.fn(),
      },
    };

    storage.setItem("careorbit_token", "token-123");
    storage.setItem("careorbit_active_patient_id", "demo-harish-kumar-002");

    vi.restoreAllMocks();
  });

  it("appends patient_id to scoped API request URLs", async () => {
    const fetchMock = vi.fn(async () => okResponse({ ok: true }));
    (globalThis as any).fetch = fetchMock;

    await apiRequest("GET", "/api/patients/profile");

    const call = fetchMock.mock.calls[0];
    expect(call).toBeTruthy();
    const [url, init] = call as unknown as [string, any];
    expect(url).toContain("/api/patients/profile?patient_id=demo-harish-kumar-002");
    expect(init.headers.Authorization).toBe("Bearer token-123");
  });

  it("does not append patient_id to auth endpoints", async () => {
    const fetchMock = vi.fn(async () => okResponse({ ok: true }));
    (globalThis as any).fetch = fetchMock;

    await apiRequest("POST", "/api/auth/login", { email: "a@b.com", password: "x" });

    const call = fetchMock.mock.calls[0];
    expect(call).toBeTruthy();
    const [url] = call as unknown as [string, any];
    expect(String(url)).toBe("/api/auth/login");
  });

  it("query function uses patient-scoped URL", async () => {
    const fetchMock = vi.fn(async () => okResponse({ total_score: 50 }));
    (globalThis as any).fetch = fetchMock;

    const fn = getQueryFn<any>({ on401: "throw" });
    const data = await fn({ queryKey: ["/api/orbit/score"] } as any);

    const call = fetchMock.mock.calls[0];
    expect(call).toBeTruthy();
    const [url] = call as unknown as [string, any];
    expect(url).toContain("/api/orbit/score?patient_id=demo-harish-kumar-002");
    expect(data.total_score).toBe(50);
  });
});
