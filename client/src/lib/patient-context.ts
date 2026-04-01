import { create } from "zustand";
import { useAuthStore } from "@/lib/auth";

export interface SwitchablePatient {
  id: string;
  name: string;
  relationship?: string;
  permission_level?: string;
}

interface ActivePatientState {
  activePatientId: string | null;
  members: SwitchablePatient[];
  setMembers: (members: SwitchablePatient[]) => void;
  setActivePatientId: (patientId: string) => void;
  resetForLogout: () => void;
}

const ACTIVE_PATIENT_STORAGE_KEY = "careorbit_active_patient_id";

function normalizeMembersWithSelf(members: SwitchablePatient[]): SwitchablePatient[] {
  const self = useAuthStore.getState().user;
  const list = [...members];
  if (self?.id && !list.some((m) => m.id === self.id)) {
    list.unshift({ id: self.id, name: self.name || self.email || "Me", relationship: "self", permission_level: "full" });
  }
  return list;
}

export const useActivePatientStore = create<ActivePatientState>((set) => ({
  activePatientId: localStorage.getItem(ACTIVE_PATIENT_STORAGE_KEY),
  members: [],
  setMembers: (members) =>
    set((state) => {
      const normalized = normalizeMembersWithSelf(members);
      const persisted = localStorage.getItem(ACTIVE_PATIENT_STORAGE_KEY);
      const fallbackSelf = useAuthStore.getState().user?.id || normalized[0]?.id || null;
      const nextActive =
        (persisted && normalized.some((m) => m.id === persisted) && persisted) ||
        (state.activePatientId && normalized.some((m) => m.id === state.activePatientId) && state.activePatientId) ||
        fallbackSelf;

      if (nextActive) {
        localStorage.setItem(ACTIVE_PATIENT_STORAGE_KEY, nextActive);
      }

      return {
        members: normalized,
        activePatientId: nextActive,
      };
    }),
  setActivePatientId: (patientId) => {
    localStorage.setItem(ACTIVE_PATIENT_STORAGE_KEY, patientId);
    set({ activePatientId: patientId });
  },
  resetForLogout: () => {
    localStorage.removeItem(ACTIVE_PATIENT_STORAGE_KEY);
    set({ activePatientId: null, members: [] });
  },
}));

export function getActivePatientId(): string | null {
  return useActivePatientStore.getState().activePatientId;
}
