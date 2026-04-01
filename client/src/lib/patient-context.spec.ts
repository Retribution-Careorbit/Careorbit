import { beforeEach, describe, expect, it, vi } from "vitest";

let useAuthStore: typeof import("./auth").useAuthStore;
let useActivePatientStore: typeof import("./patient-context").useActivePatientStore;

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

describe("patient context store", () => {
  const storage = new LocalStorageMock();

  beforeEach(async () => {
    (globalThis as any).localStorage = storage;
    storage.clear();

    vi.resetModules();
    ({ useAuthStore } = await import("./auth"));
    ({ useActivePatientStore } = await import("./patient-context"));

    useAuthStore.setState({
      token: null,
      refreshToken: null,
      user: {
        id: "demo-ramesh-kumar-001",
        email: "ramesh@careorbit.dev",
        name: "Ramesh Kumar",
      },
      isAuthenticated: true,
    });

    useActivePatientStore.setState({
      activePatientId: null,
      members: [],
    });
  });

  it("includes self when linked members are loaded", () => {
    useActivePatientStore.getState().setMembers([
      {
        id: "demo-harish-kumar-002",
        name: "Harish Chandra Kumar",
        relationship: "son",
        permission_level: "full",
      },
    ]);

    const state = useActivePatientStore.getState();

    expect(state.members.map((m) => m.id)).toEqual([
      "demo-ramesh-kumar-001",
      "demo-harish-kumar-002",
    ]);
    expect(state.activePatientId).toBe("demo-ramesh-kumar-001");
    expect(localStorage.getItem("careorbit_active_patient_id")).toBe("demo-ramesh-kumar-001");
  });

  it("persists and restores selected member", () => {
    useActivePatientStore.getState().setMembers([
      { id: "demo-harish-kumar-002", name: "Harish Chandra Kumar" },
    ]);
    useActivePatientStore.getState().setActivePatientId("demo-harish-kumar-002");

    useActivePatientStore.getState().setMembers([
      { id: "demo-harish-kumar-002", name: "Harish Chandra Kumar" },
    ]);

    expect(useActivePatientStore.getState().activePatientId).toBe("demo-harish-kumar-002");
    expect(localStorage.getItem("careorbit_active_patient_id")).toBe("demo-harish-kumar-002");
  });

  it("clears patient state on reset", () => {
    useActivePatientStore.getState().setMembers([
      { id: "demo-harish-kumar-002", name: "Harish Chandra Kumar" },
    ]);
    useActivePatientStore.getState().setActivePatientId("demo-harish-kumar-002");

    useActivePatientStore.getState().resetForLogout();

    const state = useActivePatientStore.getState();
    expect(state.activePatientId).toBeNull();
    expect(state.members).toEqual([]);
    expect(localStorage.getItem("careorbit_active_patient_id")).toBeNull();
  });
});
