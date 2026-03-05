export interface OCRResult {
  fullText: string;
  lines: string[];
  avgConfidence: number;
  pageCount: number;
}

export interface MedicalEntity {
  text: string;
  category: string;
  confidence: number;
  rxnormId?: string;
}

export interface DrugInteraction {
  drugA: string;
  drugB: string;
  severity: "LOW" | "MODERATE" | "HIGH" | "CRITICAL";
  description: string;
  clinicalAction: string;
  severityModifiers?: Record<string, unknown>;
}

export interface ExtractedMedication {
  name: string;
  dosage: string;
  frequency: string;
  drugMatchScore: number;
  needsConfirmation: boolean;
}

export interface StructuredExtractionResult {
  medications: ExtractedMedication[];
  doctorName: string;
  diagnoses: string[];
  date: string;
}

export class MockVisionService {
  extractTextCalled = false;
  classifyDocumentTypeCalled = false;
  private _extractResult: OCRResult;
  private _classifyResult: string;
  private _shouldFail: boolean;
  private _failError: Error;
  private _delay: number;

  constructor(opts?: {
    extractResult?: OCRResult;
    classifyResult?: string;
    shouldFail?: boolean;
    failError?: Error;
    delay?: number;
  }) {
    this._extractResult = opts?.extractResult ?? {
      fullText: "Tab Metformin 500mg BD",
      lines: ["Tab Metformin 500mg BD"],
      avgConfidence: 0.94,
      pageCount: 1,
    };
    this._classifyResult = opts?.classifyResult ?? "prescription";
    this._shouldFail = opts?.shouldFail ?? false;
    this._failError = opts?.failError ?? new Error("Vision service timeout");
    this._delay = opts?.delay ?? 0;
  }

  async extractText(_imageBytes: Buffer): Promise<OCRResult> {
    this.extractTextCalled = true;
    if (this._delay > 0) await new Promise((r) => setTimeout(r, this._delay));
    if (this._shouldFail) throw this._failError;
    return this._extractResult;
  }

  async classifyDocumentType(_imageBytes: Buffer): Promise<string> {
    this.classifyDocumentTypeCalled = true;
    if (this._shouldFail) throw this._failError;
    return this._classifyResult;
  }
}

export class MockOpenAIService {
  extractStructuredDataCalled = false;
  chatCalled = false;
  private _extractResult: StructuredExtractionResult;
  private _chatResult: string;
  private _shouldFail: boolean;

  constructor(opts?: {
    extractResult?: StructuredExtractionResult;
    chatResult?: string;
    shouldFail?: boolean;
  }) {
    this._extractResult = opts?.extractResult ?? {
      medications: [
        {
          name: "Metformin",
          dosage: "500mg",
          frequency: "BD",
          drugMatchScore: 0.98,
          needsConfirmation: false,
        },
      ],
      doctorName: "Dr. Amit Roy",
      diagnoses: ["Type 2 Diabetes Mellitus"],
      date: "15/01/2026",
    };
    this._chatResult = opts?.chatResult ?? "Mocked AI response";
    this._shouldFail = opts?.shouldFail ?? false;
  }

  async extractStructuredData(
    _ocrText: string,
    _docType: string
  ): Promise<StructuredExtractionResult> {
    this.extractStructuredDataCalled = true;
    if (this._shouldFail) throw new Error("OpenAI service error");
    return this._extractResult;
  }

  async chat(_messages: Array<{ role: string; content: string }>): Promise<string> {
    this.chatCalled = true;
    if (this._shouldFail) throw new Error("OpenAI chat error");
    return this._chatResult;
  }
}

export class MockTranslatorService {
  translateCalled = false;
  lastSourceLang?: string;
  lastTargetLang?: string;
  private _translations: Record<string, string>;

  constructor(translations?: Record<string, string>) {
    this._translations = translations ?? {
      "मेरी दवाइयाँ क्या हैं?": "What are my medications?",
      "What are my medications?": "मेरी दवाइयाँ क्या हैं?",
      "Metformin 500mg twice daily": "मेटफॉर्मिन 500mg दिन में दो बार",
    };
  }

  async translate(text: string, target: string, source?: string): Promise<string> {
    this.translateCalled = true;
    this.lastSourceLang = source;
    this.lastTargetLang = target;
    return this._translations[text] ?? `[Translated to ${target}]: ${text}`;
  }
}

export class MockBlobStorageService {
  uploadCalled = false;
  deleteCalled = false;
  lastUploadedBlob?: string;
  private _uploadUrl: string;

  constructor(uploadUrl?: string) {
    this._uploadUrl = uploadUrl ?? "https://mockaccount.blob.core.windows.net/prescriptions/test/doc.jpg?sas=token";
  }

  async uploadDocument(
    _imageBytes: Buffer,
    patientId: string,
    docId: string
  ): Promise<string> {
    this.uploadCalled = true;
    this.lastUploadedBlob = `${patientId}/${docId}.jpg`;
    return this._uploadUrl;
  }

  async deleteDocument(_blobName: string): Promise<void> {
    this.deleteCalled = true;
  }

  async generateSasUrl(blobName: string): Promise<string> {
    return `${this._uploadUrl}/${blobName}?sas=token`;
  }
}

export class MockEmailService {
  sendCalled = false;
  lastRecipient?: string;
  lastSubject?: string;
  private _shouldFail: boolean;

  constructor(shouldFail = false) {
    this._shouldFail = shouldFail;
  }

  async sendMedicationReminder(
    toEmail: string,
    patientName: string,
    medicationName: string,
    dosage: string,
    timeLabel: string
  ): Promise<boolean> {
    this.sendCalled = true;
    this.lastRecipient = toEmail;
    this.lastSubject = `CareOrbit Reminder: ${medicationName} — ${timeLabel}`;
    if (this._shouldFail) return false;
    return true;
  }
}

export class MockSearchService {
  searchDrugInteractionsCalled = false;
  searchCareGapsCalled = false;
  private _interactions: DrugInteraction[];
  private _careGaps: Array<Record<string, unknown>>;

  constructor(opts?: {
    interactions?: DrugInteraction[];
    careGaps?: Array<Record<string, unknown>>;
  }) {
    this._interactions = opts?.interactions ?? [];
    this._careGaps = opts?.careGaps ?? [];
  }

  async searchDrugInteractions(
    drugA: string,
    drugB: string
  ): Promise<DrugInteraction[]> {
    this.searchDrugInteractionsCalled = true;
    return this._interactions.filter(
      (i) =>
        (i.drugA === drugA && i.drugB === drugB) ||
        (i.drugA === drugB && i.drugB === drugA)
    );
  }

  async searchCareGaps(
    _conditions: string[]
  ): Promise<Array<Record<string, unknown>>> {
    this.searchCareGapsCalled = true;
    return this._careGaps;
  }

  async getEmbedding(_text: string): Promise<number[]> {
    return new Array(1536).fill(0).map(() => Math.random());
  }
}

export class MockHealthcareNERService {
  recognizeCalled = false;
  private _entities: MedicalEntity[];

  constructor(entities?: MedicalEntity[]) {
    this._entities = entities ?? [
      {
        text: "Metformin",
        category: "MedicationName",
        confidence: 0.99,
        rxnormId: "860975",
      },
      {
        text: "500mg",
        category: "Dosage",
        confidence: 0.98,
      },
      {
        text: "Type 2 Diabetes",
        category: "Diagnosis",
        confidence: 0.95,
      },
    ];
  }

  async recognizeHealthEntities(_text: string): Promise<MedicalEntity[]> {
    this.recognizeCalled = true;
    return this._entities;
  }
}
