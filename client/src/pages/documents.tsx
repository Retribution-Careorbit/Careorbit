import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { queryClient, toApiUrl } from "@/lib/queryClient";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Layout } from "@/components/layout";
import { useToast } from "@/hooks/use-toast";
import { useAuthStore } from "@/lib/auth";
import { FadeIn, StaggerContainer, StaggerItem } from "@/components/animations";
import { FileUp, Upload, CheckCircle, AlertTriangle, XCircle, Loader2, Plus } from "lucide-react";

interface ReviewMedication {
  name: string;
  dosage: string;
  frequency?: string;
  dose_to_take?: string;
}

interface ExtractedReview {
  doctor_name: string;
  medications: ReviewMedication[];
  missing_fields: string[];
  low_confidence_fields?: string[];
}

interface UploadResult {
  document_id?: string;
  file_name?: string;
  document_type: string;
  status: string;
  nodes_created: number;
  interaction_alerts: any[];
  confirmation_needed: any[];
  error_message?: string;
  summary?: string;
  extracted_review?: ExtractedReview;
  review_status?: "pending_confirmation" | "confirmed";
}

type ReviewStage = "targeted" | "final";

const FREQUENCY_CANONICAL: Record<string, string> = {
  "od": "od",
  "once daily": "once daily",
  "1 time a day": "once daily",
  "1 times a day": "once daily",
  "once a day": "once daily",
  "daily": "daily",
  "bd": "bd",
  "bid": "bid",
  "twice daily": "twice daily",
  "2 times a day": "twice daily",
  "2x/day": "twice daily",
  "tds": "tds",
  "tid": "tid",
  "three times daily": "three times daily",
  "3 times a day": "three times daily",
  "qid": "qid",
  "four times daily": "qid",
  "4 times a day": "qid",
  "qhs": "qhs",
  "q4h": "q4h",
  "q6h": "q6h",
  "q8h": "q8h",
  "weekly": "weekly",
  "monthly": "monthly",
  "am": "am",
  "pm": "pm",
  "prn": "prn",
  "sos": "sos",
  "stat": "stat",
  "": "",
};

const normalizeFrequency = (value: string): string => {
  const raw = (value || "").trim().toLowerCase();
  if (!raw) return "";
  if (FREQUENCY_CANONICAL[raw] !== undefined) {
    return FREQUENCY_CANONICAL[raw];
  }
  // Unknown free-text frequency is cleared so validation gate does not reject it.
  return "";
};

export default function DocumentsPage() {
  const [results, setResults] = useState<UploadResult[]>([]);
  const [dragOver, setDragOver] = useState(false);
  const [activeReviewDocId, setActiveReviewDocId] = useState<string | null>(null);
  const [doctorName, setDoctorName] = useState("");
  const [doctorNameDisplay, setDoctorNameDisplay] = useState("");
  const doctorNameTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const handleDoctorNameChange = useCallback((value: string) => {
    setDoctorNameDisplay(value);
    if (doctorNameTimerRef.current) clearTimeout(doctorNameTimerRef.current);
    doctorNameTimerRef.current = setTimeout(() => {
      setDoctorName(value);
    }, 300);
  }, []);

  useEffect(() => {
    return () => {
      if (doctorNameTimerRef.current) clearTimeout(doctorNameTimerRef.current);
    };
  }, []);

  const [reviewMeds, setReviewMeds] = useState<ReviewMedication[]>([]);
  const [missingFields, setMissingFields] = useState<string[]>([]);
  const [lowConfidenceFields, setLowConfidenceFields] = useState<string[]>([]);
  const [reviewStage, setReviewStage] = useState<ReviewStage>("targeted");
  const [targetedPage, setTargetedPage] = useState(0);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { toast } = useToast();
  const token = useAuthStore((s) => s.token);

  const activeResult = useMemo(
    () => results.find((r) => r.document_id && r.document_id === activeReviewDocId),
    [results, activeReviewDocId]
  );

  const reviewFieldSet = useMemo(() => {
    const all = [...missingFields, ...lowConfidenceFields];
    return new Set(all);
  }, [missingFields, lowConfidenceFields]);

  const medicationFieldRequests = useMemo(() => {
    const requests: Array<{ index: number; field: keyof ReviewMedication; key: string }> = [];
    reviewFieldSet.forEach((key) => {
      const match = key.match(/^medications\[(\d+)\]\.(name|dosage|frequency|dose_to_take)$/);
      if (!match) return;
      requests.push({
        index: Number(match[1]),
        field: match[2] as keyof ReviewMedication,
        key,
      });
    });
    const fieldOrder: Record<keyof ReviewMedication, number> = {
      name: 0,
      dosage: 1,
      frequency: 2,
      dose_to_take: 3,
    };
    return requests.sort((a, b) => (a.index - b.index) || (fieldOrder[a.field] - fieldOrder[b.field]));
  }, [reviewFieldSet]);

  const reviewSuggestions = useMemo(() => {
    const map: Record<string, string> = {};
    const doctor = (activeResult?.extracted_review?.doctor_name || "").trim();
    if (doctor) {
      map["doctor_name"] = doctor;
    }
    (activeResult?.extracted_review?.medications || []).forEach((med, idx) => {
      map[`medications[${idx}].name`] = (med.name || "").trim();
      map[`medications[${idx}].dosage`] = (med.dosage || "").trim();
      map[`medications[${idx}].frequency`] = (med.frequency || "").trim();
      map[`medications[${idx}].dose_to_take`] = (med.dose_to_take || "").trim();
    });
    return map;
  }, [activeResult]);

  const lowConfidenceFieldSet = useMemo(() => new Set(lowConfidenceFields), [lowConfidenceFields]);

  const showDoctorField = reviewFieldSet.has("doctor_name");
  const showManualMedicationRows = reviewFieldSet.has("medications");

  const targetedEntries = useMemo(
    () => [
      ...(showDoctorField ? [{ kind: "doctor" as const, key: "doctor_name" }] : []),
      ...medicationFieldRequests.map((req) => ({ kind: "medication" as const, key: req.key, req })),
    ],
    [showDoctorField, medicationFieldRequests]
  );

  const TARGETED_PAGE_SIZE = 6;
  const targetedTotalPages = Math.max(1, Math.ceil(targetedEntries.length / TARGETED_PAGE_SIZE));
  const pagedTargetedEntries = useMemo(
    () => targetedEntries.slice(targetedPage * TARGETED_PAGE_SIZE, (targetedPage + 1) * TARGETED_PAGE_SIZE),
    [targetedEntries, targetedPage]
  );

  const highConfidenceDoctor = useMemo(() => {
    if (reviewFieldSet.has("doctor_name")) return "";
    return (reviewSuggestions["doctor_name"] || "").trim();
  }, [reviewFieldSet, reviewSuggestions]);

  const highConfidenceMeds = useMemo(() => {
    const meds = activeResult?.extracted_review?.medications || [];
    return meds.filter((_, idx) => {
      const nameKey = `medications[${idx}].name`;
      const dosageKey = `medications[${idx}].dosage`;
      return !reviewFieldSet.has(nameKey) && !reviewFieldSet.has(dosageKey);
    });
  }, [activeResult, reviewFieldSet]);

  const resolvedPayload = useMemo(() => {
    const resolvedDoctor = (() => {
      const entered = doctorName.trim();
      if (entered) return entered;
      if (lowConfidenceFieldSet.has("doctor_name")) {
        return (reviewSuggestions["doctor_name"] || "").trim();
      }
      return entered;
    })();

    const resolvedMeds = reviewMeds.map((med, idx) => {
      const resolveField = (field: keyof ReviewMedication) => {
        const entered = String(med[field] || "").trim();
        if (entered) return entered;
        const key = `medications[${idx}].${field}`;
        if (lowConfidenceFieldSet.has(key)) {
          return (reviewSuggestions[key] || "").trim();
        }
        return entered;
      };

      return {
        name: resolveField("name"),
        dosage: resolveField("dosage"),
        frequency: normalizeFrequency(resolveField("frequency")),
        dose_to_take: resolveField("dose_to_take"),
      };
    });

    return {
      doctor_name: resolvedDoctor,
      medications: resolvedMeds,
    };
  }, [doctorName, reviewMeds, lowConfidenceFieldSet, reviewSuggestions]);

  const changedLowConfidenceFields = useMemo(() => {
    const changed: string[] = [];
    for (const key of lowConfidenceFields) {
      const suggested = (reviewSuggestions[key] || "").trim();
      if (!suggested) continue;
      let actual = "";
      if (key === "doctor_name") {
        actual = (resolvedPayload.doctor_name || "").trim();
      } else {
        const match = key.match(/^medications\[(\d+)\]\.(name|dosage|frequency|dose_to_take)$/);
        if (!match) continue;
        const idx = Number(match[1]);
        const field = match[2] as keyof ReviewMedication;
        actual = String(resolvedPayload.medications[idx]?.[field] || "").trim();
      }
      if (actual && suggested.toLowerCase() !== actual.toLowerCase()) {
        changed.push(key);
      }
    }
    return changed;
  }, [lowConfidenceFields, reviewSuggestions, resolvedPayload]);

  const requiredMissingFromPayload = useMemo(() => {
    const missing: string[] = [];
    if (!resolvedPayload.doctor_name) {
      missing.push("doctor_name");
    }
    if (!resolvedPayload.medications.length) {
      missing.push("medications");
    } else {
      resolvedPayload.medications.forEach((med, idx) => {
        if (!med.name) missing.push(`medications[${idx}].name`);
        if (!med.dosage) missing.push(`medications[${idx}].dosage`);
      });
    }
    return missing;
  }, [resolvedPayload]);

  const loadReviewState = (review?: ExtractedReview, fallbackMissing: string[] = []) => {
    if (doctorNameTimerRef.current) {
      clearTimeout(doctorNameTimerRef.current);
      doctorNameTimerRef.current = null;
    }
    const extractedMeds = review?.medications?.length
      ? review.medications
      : [{ name: "", dosage: "", frequency: "", dose_to_take: "" }];
    const reviewMissing = review?.missing_fields || fallbackMissing;
    const reviewLow = review?.low_confidence_fields || [];
    const lowSet = new Set(reviewLow);

    const nextDoctor = lowSet.has("doctor_name") ? "" : (review?.doctor_name || "");
    const nextMeds = extractedMeds.map((med, idx) => ({
      name: lowSet.has(`medications[${idx}].name`) ? "" : (med.name || ""),
      dosage: lowSet.has(`medications[${idx}].dosage`) ? "" : (med.dosage || ""),
      frequency: lowSet.has(`medications[${idx}].frequency`) ? "" : (med.frequency || ""),
      dose_to_take: lowSet.has(`medications[${idx}].dose_to_take`) ? "" : (med.dose_to_take || ""),
    }));

    setDoctorName(nextDoctor);
    setDoctorNameDisplay(nextDoctor);
    setReviewMeds(nextMeds);
    setMissingFields(reviewMissing);
    setLowConfidenceFields(reviewLow);
    setTargetedPage(0);
    if ((reviewMissing.length + reviewLow.length) > 0) {
      setReviewStage("targeted");
    } else {
      setReviewStage("final");
    }
  };

  const flushDoctorName = useCallback(() => {
    if (doctorNameTimerRef.current) {
      clearTimeout(doctorNameTimerRef.current);
      doctorNameTimerRef.current = null;
    }
    setDoctorName(doctorNameDisplay);
  }, [doctorNameDisplay]);

  const proceedToFinalReview = () => {
    flushDoctorName();
    const currentDoctor = doctorNameDisplay.trim() ||
      (lowConfidenceFieldSet.has("doctor_name") ? (reviewSuggestions["doctor_name"] || "").trim() : "");
    const effectiveMissing: string[] = [];
    if (!currentDoctor) effectiveMissing.push("doctor_name");
    if (!resolvedPayload.medications.length) {
      effectiveMissing.push("medications");
    } else {
      resolvedPayload.medications.forEach((med, idx) => {
        if (!med.name) effectiveMissing.push(`medications[${idx}].name`);
        if (!med.dosage) effectiveMissing.push(`medications[${idx}].dosage`);
      });
    }
    if (effectiveMissing.length > 0) {
      const mergedMissing = Array.from(new Set([...missingFields, ...effectiveMissing]));
      setMissingFields(mergedMissing);
      toast({
        title: "Missing Details",
        description: `Please fill required fields: ${effectiveMissing.join(", ")}`,
        variant: "destructive",
      });
      return;
    }

    setDoctorName(currentDoctor);
    setDoctorNameDisplay(currentDoctor);
    setReviewMeds(resolvedPayload.medications);
    setReviewStage("final");

    if (changedLowConfidenceFields.length > 0) {
      toast({
        title: "Reconfirm Updated Values",
        description: "Some low-confidence extracted values were edited. Please verify the final PHIG payload.",
      });
    }
  };

  const formatConfirmError = (data: any): string => {
    const detail = data?.detail;
    if (typeof detail === "string" && detail.trim()) {
      return detail;
    }
    if (detail && typeof detail === "object") {
      if (detail.error === "post_confirmation_validation_failed") {
        const fields = Array.isArray(detail.missing_fields) ? detail.missing_fields.join(", ") : "required fields";
        return `Please fill required fields: ${fields}.`;
      }
      if (detail.error === "post_confirmation_validation_gate_failed") {
        const first = Array.isArray(detail.rejections) ? detail.rejections[0] : null;
        const reasons = Array.isArray(first?.reasons) ? first.reasons.join(", ") : "validation failed";
        const med = first?.name ? ` for ${first.name}` : "";
        return `Medication validation failed${med}: ${reasons}. Example dosage: 500 mg.`;
      }
      if (detail.error === "phig_consistency_failed_after_write") {
        return "PHIG consistency check failed after confirmation. Please try again.";
      }
    }
    if (typeof data?.error_message === "string" && data.error_message.trim()) {
      return data.error_message;
    }
    return "Failed to confirm extracted data";
  };

  const confirmMutation = useMutation({
    mutationFn: async () => {
      if (!activeReviewDocId) {
        throw new Error("No active review selected");
      }
      flushDoctorName();
      const currentDoctor = doctorNameDisplay.trim() || resolvedPayload.doctor_name;
      const res = await fetch(toApiUrl(`/api/documents/confirm/${activeReviewDocId}`), {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          doctor_name: currentDoctor,
          medications: resolvedPayload.medications,
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        if (data?.detail?.error === "post_confirmation_validation_gate_failed") {
          const rejections = Array.isArray(data?.detail?.rejections) ? data.detail.rejections : [];
          const unsupportedByName = new Set(
            rejections
              .filter((r: any) => Array.isArray(r?.reasons) && r.reasons.includes("unsupported_frequency"))
              .map((r: any) => String(r?.name || "").trim().toLowerCase())
              .filter((v: string) => !!v)
          );
          if (unsupportedByName.size > 0) {
            const frequencyKeys = reviewMeds
              .map((m, idx) => ({ idx, name: String(m.name || "").trim().toLowerCase() }))
              .filter((row) => unsupportedByName.has(row.name))
              .map((row) => `medications[${row.idx}].frequency`);
            if (frequencyKeys.length > 0) {
              setReviewStage("targeted");
              setMissingFields((prev) => Array.from(new Set([...prev, ...frequencyKeys])));
            }
          }
        }
        throw new Error(formatConfirmError(data));
      }
      return { ...data, _submittedDoctor: currentDoctor };
    },
    onSuccess: (data) => {
      if (data?.status === "needs_manual_input") {
        setMissingFields(Array.isArray(data?.missing_fields) ? data.missing_fields : []);
        setLowConfidenceFields(Array.isArray(data?.low_confidence_fields) ? data.low_confidence_fields : []);
        toast({
          title: "Missing Details",
          description: "Please fill missing doctor/medication fields before confirming.",
          variant: "destructive",
        });
        return;
      }

      setResults((prev) =>
        prev.map((row) =>
          row.document_id === activeReviewDocId
            ? {
                ...row,
                review_status: "confirmed",
                summary: `Confirmed and added ${data.medications_added || 0} medication(s) to PHIG.`,
                extracted_review: {
                  doctor_name: data.doctor_name || data._submittedDoctor,
                  medications: data.medications || reviewMeds,
                  missing_fields: [],
                  low_confidence_fields: [],
                },
              }
            : row
        )
      );

      setMissingFields([]);
      setLowConfidenceFields([]);
      setActiveReviewDocId(null);

      queryClient.invalidateQueries({ queryKey: ["/api/patients/medications"] });
      queryClient.invalidateQueries({ queryKey: ["/api/patients/overview"] });
      queryClient.invalidateQueries({ queryKey: ["/api/patients/lab-insights"] });
      queryClient.invalidateQueries({ queryKey: ["/api/tests/scenarios"] });
      queryClient.invalidateQueries({ queryKey: ["/api/system/notifications"] });
      queryClient.invalidateQueries({ queryKey: ["/api/orbit/score"] });

      toast({
        title: "Confirmed",
        description: `Added ${data.medications_added || 0} medication(s) to PHIG and synced across tabs.`,
      });
    },
    onError: (err: Error) => {
      toast({ title: "Confirmation Failed", description: err.message, variant: "destructive" });
    },
  });

  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append("file", file);
      const res = await fetch(toApiUrl("/api/documents/upload"), {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });
      const raw = await res.text();
      const parsed = raw ? (() => { try { return JSON.parse(raw); } catch { return null; } })() : null;
      if (!res.ok) {
        const detail = (parsed && (parsed.detail || parsed.error_message || parsed.message)) || raw || `Upload failed (${res.status})`;
        throw new Error(detail);
      }
      if (!parsed) {
        throw new Error("Upload failed: invalid server response");
      }
      return parsed;
    },
    onSuccess: (data: UploadResult) => {
      setResults((prev) => [data, ...prev]);
      queryClient.invalidateQueries({ queryKey: ["/api/tests/scenarios"] });
      queryClient.invalidateQueries({ queryKey: ["/api/documents/lab-reports/valid"] });
      queryClient.invalidateQueries({ queryKey: ["/api/system/notifications"] });

      if (data.status === "failed") {
        if (data.document_id) {
          setActiveReviewDocId(data.document_id);
          loadReviewState(data.extracted_review, ["doctor_name", "medications"]);
        }
        toast({
          title: "Extraction Failed",
          description: data.error_message || "Could not extract clinical data. Please fill details manually and confirm.",
          variant: "destructive",
        });
        return;
      }

      if (data.status === "needs_confirmation") {
        setActiveReviewDocId(data.document_id || null);
        loadReviewState(data.extracted_review);
        toast({
          title: "Review Needed",
          description: data.summary || `${data.document_type || "Document"} needs confirmation before finalizing.`,
        });
        return;
      }
      setActiveReviewDocId(null);
      setDoctorName("");
      setDoctorNameDisplay("");
      setReviewMeds([]);
      setMissingFields([]);
      setLowConfidenceFields([]);

      toast({
        title: "Extraction Complete",
        description: "Data extracted with high confidence and processed.",
      });
    },
    onError: (err: Error) => {
      toast({ title: "Upload Failed", description: err.message, variant: "destructive" });
    },
  });

  const handleUpload = (file: File) => {
    const allowedTypes = ["image/jpeg", "image/png", "image/webp", "image/heic", "application/pdf"];
    const allowedExtensions = ["jpg", "jpeg", "png", "webp", "heic", "pdf"];
    const ext = (file.name.split(".").pop() || "").toLowerCase();
    const mimeOk = allowedTypes.includes(file.type);
    const extOk = allowedExtensions.includes(ext);
    if (!mimeOk && !extOk) {
      toast({ title: "Invalid File", description: "Allowed files: JPG, PNG, WebP, HEIC, or PDF (max 10MB)", variant: "destructive" });
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      toast({ title: "File Too Large", description: "Maximum file size is 10MB", variant: "destructive" });
      return;
    }
    uploadMutation.mutate(file);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleUpload(file);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) handleUpload(file);
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "success": return <CheckCircle className="h-5 w-5" style={{ color: "var(--accent-emerald)" }} />;
      case "needs_confirmation": return <AlertTriangle className="h-5 w-5" style={{ color: "var(--accent-amber)" }} />;
      case "failed": return <XCircle className="h-5 w-5" style={{ color: "var(--accent-rose)" }} />;
      default: return null;
    }
  };

  const openReviewDialog = (row: UploadResult) => {
    if (!row.document_id) {
      return;
    }
    setActiveReviewDocId(row.document_id);
    setTargetedPage(0);
    loadReviewState(row.extracted_review);
  };

  const updateMedAt = (index: number, field: keyof ReviewMedication, value: string) => {
    setReviewMeds((prev) => {
      const next = [...prev];
      while (next.length <= index) {
        next.push({ name: "", dosage: "", frequency: "", dose_to_take: "" });
      }
      next[index] = { ...next[index], [field]: value };
      return next;
    });
  };

  return (
    <Layout>
      <div className="space-y-6">
        <FadeIn>
          <div className="page-title-bar">
            <div>
              <h1 data-testid="text-documents-title">
                Documents
              </h1>
              <p>
                Upload prescriptions, lab reports, or medicine strip photos for AI extraction
              </p>
            </div>
          </div>
        </FadeIn>

        <FadeIn delay={0.1}>
          <div className="page-card p-8">
            <div
              role="button"
              tabIndex={0}
              aria-label="Upload document. Drop a file here or press Enter to browse"
              className="border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer"
              style={{
                borderColor: dragOver ? "var(--accent-cyan)" : "var(--border-default)",
                background: dragOver
                  ? "linear-gradient(135deg, var(--accent-cyan-dim), color-mix(in srgb, var(--accent-violet-dim) 50%, transparent))"
                  : "transparent",
                transition: "all 200ms ease",
              }}
              onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
              onDragLeave={() => setDragOver(false)}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); fileInputRef.current?.click(); } }}
              data-testid="dropzone-upload"
            >
              <input ref={fileInputRef} type="file" accept="image/jpeg,image/png,image/webp,image/heic,application/pdf,.pdf" onChange={handleFileChange} className="hidden" data-testid="input-file" />
              {uploadMutation.isPending ? (
                <div className="space-y-4">
                  <div
                    className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto"
                    style={{ background: "linear-gradient(135deg, var(--accent-cyan-dim), var(--accent-violet-dim))" }}
                  >
                    <Loader2 className="h-8 w-8 animate-spin" style={{ color: "var(--accent-cyan)" }} data-testid="spinner-processing" />
                  </div>
                  <p className="text-lg font-medium" style={{ color: "var(--text-primary)" }}>Processing document...</p>
                  <p className="text-sm" style={{ color: "var(--text-muted)" }}>AI is extracting health data</p>
                </div>
              ) : (
                <div className="space-y-4">
                  <div
                    className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto"
                    style={{ background: "var(--bg-elevated)", border: "1px solid var(--border-subtle)" }}
                  >
                    <Upload className="h-8 w-8" style={{ color: "var(--text-muted)" }} />
                  </div>
                  <p className="text-lg font-medium" style={{ color: "var(--text-primary)" }}>Drop your document here</p>
                  <p className="text-sm" style={{ color: "var(--text-muted)" }}>JPEG, PNG, WebP, HEIC, or PDF up to 10MB</p>
                  <Button variant="outline" className="rounded-full" data-testid="button-browse">
                    <FileUp className="h-4 w-4 mr-2" />
                    Browse Files
                  </Button>
                </div>
              )}
            </div>
          </div>
        </FadeIn>

        {results.length > 0 && (
          <div className="space-y-4">
            <p className="section-header">Upload Results</p>
            <StaggerContainer className="space-y-3">
              {results.map((result, i) => (
                <StaggerItem key={i}>
                  <div className="page-card p-5" data-testid={`card-result-${i}`}>
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        {getStatusIcon(result.status)}
                        <span className="font-medium" style={{ color: "var(--text-primary)" }}>{result.document_type || "Document"}</span>
                      </div>
                      <Badge variant={result.status === "success" ? "default" : "outline"}>{result.status}</Badge>
                    </div>
                    {result.file_name && (
                      <p className="text-xs mb-2" style={{ color: "var(--text-muted)" }}>
                        File: <span className="font-mono">{result.file_name}</span>
                      </p>
                    )}
                    <div className="text-sm space-y-1.5">
                      <p>
                        <span style={{ color: "var(--text-muted)" }}>Nodes created:</span>{" "}
                        <span className="font-mono font-medium" style={{ color: "var(--text-primary)" }}>{result.nodes_created}</span>
                      </p>
                      {result.error_message && (
                        <div className="mt-2 p-3 rounded-lg" style={{ background: "rgba(244,63,94,0.05)", border: "1px solid rgba(244,63,94,0.20)" }}>
                          <p className="text-sm" style={{ color: "var(--accent-rose)" }}>
                            {result.error_message}
                          </p>
                        </div>
                      )}
                      {!result.error_message && result.summary && (
                        <p className="text-xs mt-2" style={{ color: "var(--text-secondary)" }}>
                          {result.summary}
                        </p>
                      )}
                      {result.extracted_review && (
                        <div className="mt-3 p-3 rounded-lg" style={{ background: "var(--bg-elevated)", border: "1px solid var(--border-subtle)" }}>
                          <p className="text-xs font-medium mb-2" style={{ color: "var(--text-secondary)" }}>
                            Extracted Review
                          </p>
                          <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
                            Doctor: <span style={{ color: "var(--text-primary)" }}>{result.extracted_review.doctor_name || "Not extracted"}</span>
                          </p>
                          <p className="text-xs mt-1" style={{ color: "var(--text-secondary)" }}>
                            Medicines: <span style={{ color: "var(--text-primary)" }}>{result.extracted_review.medications.length}</span>
                          </p>
                          {result.review_status === "confirmed" ? (
                            <Badge className="mt-2">Added to PHIG</Badge>
                          ) : (
                            <Button className="mt-2" size="sm" variant="outline" onClick={() => openReviewDialog(result)}>
                              Review & Confirm
                            </Button>
                          )}
                        </div>
                      )}
                      {result.interaction_alerts?.length > 0 && (
                        <div className="mt-2 p-3 rounded-lg" style={{ background: "rgba(244,63,94,0.05)", border: "1px solid rgba(244,63,94,0.20)" }}>
                          <p className="font-medium text-sm" style={{ color: "var(--accent-rose)" }}>
                            {result.interaction_alerts.length} interaction alert(s)
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                </StaggerItem>
              ))}
            </StaggerContainer>
          </div>
        )}

        <Dialog open={Boolean(activeReviewDocId)} onOpenChange={(open) => { if (!open) setActiveReviewDocId(null); }}>
          <DialogContent className="sm:max-w-2xl w-[95vw] max-h-[90vh] overflow-hidden" data-testid="dialog-manual-review">
            <DialogHeader>
              <DialogTitle>{reviewStage === "targeted" ? "Resolve Missing / Low-Confidence Fields" : "Final Review Before PHIG Add"}</DialogTitle>
              <DialogDescription>
                {reviewStage === "targeted"
                  ? "Please confirm only the flagged fields first."
                  : "Review all data to be added to PHIG. You can still edit before final confirmation."}
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-3 overflow-y-auto pr-1" style={{ maxHeight: "64vh" }}>
              {missingFields.length > 0 && (
                <div className="rounded-lg p-3" style={{ background: "rgba(245,158,11,0.08)", border: "1px solid rgba(245,158,11,0.25)" }}>
                  <p className="text-xs font-medium" style={{ color: "var(--accent-amber)" }}>
                    These fields require manual confirmation: {missingFields.join(", ")}
                  </p>
                </div>
              )}

              {lowConfidenceFields.length > 0 && (
                <div className="rounded-lg p-3" style={{ background: "rgba(56,189,248,0.08)", border: "1px solid rgba(56,189,248,0.25)" }}>
                  <p className="text-xs font-medium" style={{ color: "var(--accent-cyan)" }}>
                    These fields were extracted with low confidence (&lt;60%). Confirm or edit: {lowConfidenceFields.join(", ")}
                  </p>
                </div>
              )}

              {reviewStage === "targeted" && (highConfidenceDoctor || highConfidenceMeds.length > 0) && (
                <div className="rounded-lg p-3" style={{ background: "rgba(34,197,94,0.08)", border: "1px solid rgba(34,197,94,0.22)" }}>
                  <p className="text-xs font-medium mb-1" style={{ color: "var(--accent-emerald)" }}>
                    High-confidence extracted data (already confirmed)
                  </p>
                  {highConfidenceDoctor && (
                    <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
                      Doctor: <span style={{ color: "var(--text-primary)" }}>{highConfidenceDoctor}</span>
                    </p>
                  )}
                  {highConfidenceMeds.length > 0 && (
                    <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
                      Medicines: <span style={{ color: "var(--text-primary)" }}>{highConfidenceMeds.map((m) => `${m.name || "Unknown"}${m.dosage ? ` (${m.dosage})` : ""}`).join(", ")}</span>
                    </p>
                  )}
                </div>
              )}

              <div className="space-y-3">
              {reviewStage === "targeted" ? (
                <>
                  {pagedTargetedEntries.map((entry) => {
                    if (entry.kind === "doctor") {
                      return (
                        <div key={entry.key} className="space-y-1">
                          <Label htmlFor="doctor_name">Doctor Name</Label>
                          <Input
                            id="doctor_name"
                            value={doctorNameDisplay}
                            onChange={(e) => handleDoctorNameChange(e.target.value)}
                            placeholder={lowConfidenceFieldSet.has("doctor_name") ? (reviewSuggestions["doctor_name"] || "") : ""}
                          />
                        </div>
                      );
                    }

                    const req = entry.req;
                    const labelMap: Record<keyof ReviewMedication, string> = {
                      name: "Medicine Name",
                      dosage: "Dosage (e.g., 500 mg)",
                      frequency: "Frequency",
                      dose_to_take: "Dose to Take",
                    };
                    const med = reviewMeds[req.index] || { name: "", dosage: "", frequency: "", dose_to_take: "" };
                    return (
                      <div key={req.key} className="space-y-1">
                        <Label>{`Medicine ${req.index + 1} - ${labelMap[req.field]}`}</Label>
                        <Input
                          value={med[req.field] || ""}
                          onChange={(e) => updateMedAt(req.index, req.field, e.target.value)}
                          placeholder={lowConfidenceFieldSet.has(req.key) ? (reviewSuggestions[req.key] || "") : ""}
                        />
                      </div>
                    );
                  })}

                  {(targetedEntries.length === 0 || showManualMedicationRows) && (
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <p className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>Medicines & Doses</p>
                        {showManualMedicationRows && (
                          <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            onClick={() => setReviewMeds((prev) => [...prev, { name: "", dosage: "", frequency: "", dose_to_take: "" }])}
                          >
                            <Plus className="h-4 w-4 mr-1" />
                            Add Row
                          </Button>
                        )}
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <>
                  <div className="rounded-lg p-3" style={{ background: "rgba(34,197,94,0.08)", border: "1px solid rgba(34,197,94,0.22)" }}>
                    <p className="text-xs font-medium" style={{ color: "var(--accent-emerald)" }}>
                      Final payload preview: this is the data that will be added to PHIG after you confirm.
                    </p>
                  </div>

                  {changedLowConfidenceFields.length > 0 && (
                    <div className="rounded-lg p-3" style={{ background: "rgba(245,158,11,0.08)", border: "1px solid rgba(245,158,11,0.25)" }}>
                      <p className="text-xs font-medium" style={{ color: "var(--accent-amber)" }}>
                        Reconfirm these edited low-confidence fields: {changedLowConfidenceFields.join(", ")}
                      </p>
                    </div>
                  )}

                  <div className="space-y-1">
                    <Label htmlFor="doctor_name_final">Doctor Name</Label>
                    <Input
                      id="doctor_name_final"
                      value={doctorNameDisplay}
                      onChange={(e) => handleDoctorNameChange(e.target.value)}
                      placeholder=""
                    />
                  </div>

                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <p className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>All Medicines & Doses</p>
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() => setReviewMeds((prev) => [...prev, { name: "", dosage: "", frequency: "", dose_to_take: "" }])}
                      >
                        <Plus className="h-4 w-4 mr-1" />
                        Add Row
                      </Button>
                    </div>

                    {reviewMeds.map((med, idx) => (
                      <div key={`${idx}-${med.name}`} className="grid grid-cols-1 md:grid-cols-2 gap-2">
                        <Input
                          value={med.name || ""}
                          onChange={(e) => updateMedAt(idx, "name", e.target.value)}
                          placeholder="Medicine name"
                        />
                        <Input
                          value={med.dosage || ""}
                          onChange={(e) => updateMedAt(idx, "dosage", e.target.value)}
                          placeholder="Dosage (e.g., 500 mg)"
                        />
                        <Input
                          value={med.frequency || ""}
                          onChange={(e) => updateMedAt(idx, "frequency", e.target.value)}
                          placeholder="Frequency"
                        />
                        <Input
                          value={med.dose_to_take || ""}
                          onChange={(e) => updateMedAt(idx, "dose_to_take", e.target.value)}
                          placeholder="Dose to take"
                        />
                      </div>
                    ))}
                  </div>
                </>
              )}
              </div>
            </div>

            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => setActiveReviewDocId(null)}
                disabled={confirmMutation.isPending}
              >
                Cancel
              </Button>
              {reviewStage === "targeted" ? (
                <>
                  <Button
                    variant="outline"
                    onClick={() => setTargetedPage((prev) => Math.max(prev - 1, 0))}
                    disabled={targetedPage === 0}
                  >
                    Previous
                  </Button>
                  {targetedPage < targetedTotalPages - 1 ? (
                    <Button
                      onClick={() => setTargetedPage((prev) => Math.min(prev + 1, targetedTotalPages - 1))}
                      disabled={!activeResult?.document_id}
                    >
                      Next
                    </Button>
                  ) : (
                    <Button onClick={proceedToFinalReview} disabled={!activeResult?.document_id}>
                      Review Full Data
                    </Button>
                  )}
                </>
              ) : (
                <>
                  <Button
                    variant="outline"
                    onClick={() => {
                      setReviewStage("targeted");
                      setTargetedPage(0);
                    }}
                    disabled={confirmMutation.isPending}
                  >
                    Back
                  </Button>
                  <Button onClick={() => confirmMutation.mutate()} disabled={confirmMutation.isPending || !activeResult?.document_id}>
                    {confirmMutation.isPending ? "Confirming..." : "Final Confirm & Add to PHIG"}
                  </Button>
                </>
              )}
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </Layout>
  );
}
