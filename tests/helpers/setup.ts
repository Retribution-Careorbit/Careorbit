import { type Express } from "express";
import { createServer, type Server } from "http";
import express from "express";

export interface TestUser {
  id: string;
  name: string;
  email: string;
  password: string;
  phoneNumber?: string;
  dateOfBirth?: string;
  gender?: string;
  preferredLanguage?: string;
  subscriptionTier?: "free" | "premium" | "family";
  isActive?: boolean;
}

export interface TestTokens {
  accessToken: string;
  refreshToken: string;
}

export const TEST_USER: TestUser = {
  id: "test-user-uuid-1234",
  name: "Test Patient",
  email: "patient@example.com",
  password: "SecureP@ss123!",
  phoneNumber: "+919876543210",
  dateOfBirth: "1990-05-15",
  gender: "male",
  preferredLanguage: "en",
  subscriptionTier: "free",
  isActive: true,
};

export const TEST_USER_PREMIUM: TestUser = {
  id: "premium-user-uuid-5678",
  name: "Premium Patient",
  email: "premium@example.com",
  password: "PremiumP@ss456!",
  phoneNumber: "+919876543211",
  dateOfBirth: "1985-03-22",
  gender: "female",
  preferredLanguage: "hi",
  subscriptionTier: "premium",
  isActive: true,
};

export const TEST_USER_INACTIVE: TestUser = {
  id: "inactive-user-uuid-9999",
  name: "Inactive Patient",
  email: "inactive@example.com",
  password: "InactiveP@ss789!",
  subscriptionTier: "free",
  isActive: false,
};

export function createTestApp(): Express {
  const app = express();
  app.use(express.json());
  return app;
}

export function createTestServer(app: Express): Server {
  return createServer(app);
}

export function generateMockJWT(payload: Record<string, unknown>): string {
  const header = Buffer.from(JSON.stringify({ alg: "HS256", typ: "JWT" })).toString("base64url");
  const body = Buffer.from(JSON.stringify({
    ...payload,
    iat: Math.floor(Date.now() / 1000),
    exp: Math.floor(Date.now() / 1000) + 3600,
  })).toString("base64url");
  const signature = Buffer.from("mock-signature").toString("base64url");
  return `${header}.${body}.${signature}`;
}

export function generateExpiredMockJWT(payload: Record<string, unknown>): string {
  const header = Buffer.from(JSON.stringify({ alg: "HS256", typ: "JWT" })).toString("base64url");
  const body = Buffer.from(JSON.stringify({
    ...payload,
    iat: Math.floor(Date.now() / 1000) - 7200,
    exp: Math.floor(Date.now() / 1000) - 3600,
  })).toString("base64url");
  const signature = Buffer.from("mock-signature").toString("base64url");
  return `${header}.${body}.${signature}`;
}

export const MOCK_OCR_RESULT = {
  fullText: "Tab Metformin 500mg BD\nTab Amlodipine 5mg OD\nDr. Amit Roy\nDate: 15/01/2026",
  lines: [
    "Tab Metformin 500mg BD",
    "Tab Amlodipine 5mg OD",
    "Dr. Amit Roy",
    "Date: 15/01/2026",
  ],
  avgConfidence: 0.94,
  pageCount: 1,
};

export const MOCK_LOW_CONFIDENCE_OCR = {
  fullText: "???smudged???",
  lines: ["???smudged???"],
  avgConfidence: 0.15,
  pageCount: 1,
};

export const MOCK_EXTRACTED_DATA = {
  medications: [
    {
      name: "Metformin",
      dosage: "500mg",
      frequency: "BD",
      drugMatchScore: 0.98,
      needsConfirmation: false,
    },
    {
      name: "Amlodipine",
      dosage: "5mg",
      frequency: "OD",
      drugMatchScore: 0.96,
      needsConfirmation: false,
    },
  ],
  doctorName: "Dr. Amit Roy",
  diagnoses: ["Type 2 Diabetes Mellitus", "Hypertension"],
  date: "15/01/2026",
};

export const MOCK_DRUG_INTERACTION = {
  drugA: "Metformin",
  drugB: "Contrast Dye",
  severity: "HIGH",
  description: "Metformin should be withheld before and after IV contrast dye",
  clinicalAction: "Hold Metformin 48h before and after contrast procedure",
  severityModifiers: {
    renalImpairment: true,
    escalatesTo: "CRITICAL",
    creatinineThreshold: 1.3,
  },
};

export const MOCK_CARE_GAP = {
  condition: "Type 2 Diabetes Mellitus",
  screeningType: "HbA1c",
  frequency: "Every 3 months",
  evidenceGrade: "A",
  source: "ADA 2024 Guidelines",
  applicableCodes: ["E11.9"],
};

export const MOCK_REMINDER = {
  medicationName: "Metformin",
  dosage: "500mg",
  reminderTime: "08:00",
  daysOfWeek: [1, 2, 3, 4, 5, 6, 7],
  isActive: true,
};
