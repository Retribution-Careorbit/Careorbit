import { useMemo, useRef, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
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

interface ArchitectureCompliance {
  architecture_followed: boolean;
  degraded_mode?: boolean;
  strict_managed_mode?: boolean;
  warnings?: string[];
  gaps: string[];
  steps: Array<{ step: number; name: string; implemented: boolean; degraded_mode?: boolean; gap?: string }>;
  services: Array<{ name: string; configured: boolean; required: boolean; degraded_mode?: boolean; status?: string }>;
}

export default function DocumentsPage() {
  const [results, setResults] = useState<UploadResult[]>([]);
  const [dragOver, setDragOver] = useState(false);
  const [activeReviewDocId, setActiveReviewDocId] = useState<string | null>(null);
  const [doctorName, setDoctorName] = useState("");
  const [reviewMeds, setReviewMeds] = useState<ReviewMedication[]>([]);
  const [missingFields, setMissingFields] = useState<string[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { toast } = useToast();
  const token = useAuthStore((s) => s.token);

  const architectureQuery = useQuery<ArchitectureCompliance>({
    queryKey: ["/api/system/architecture/compliance"],
    queryFn: async () => {
      const res = await fetch(toApiUrl("/api/system/architecture/compliance"), {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) {
        throw new Error("Failed to load architecture compliance");
      }
      return await res.json();
    },
  });

  const activeResult = useMemo(
    () => results.find((r) => r.document_id && r.document_id === activeReviewDocId),
    [results, activeReviewDocId]
  );

  const confirmMutation = useMutation({
    mutationFn: async () => {
      if (!activeReviewDocId) {
        throw new Error("No active review selected");
      }
      const res = await fetch(toApiUrl(`/api/documents/confirm/${activeReviewDocId}`), {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          doctor_name: doctorName,
          medications: reviewMeds,
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data?.detail || data?.error_message || "Failed to confirm extracted data");
      }
      return data;
    },
    onSuccess: (data) => {
      if (data?.status === "needs_manual_input") {
        setMissingFields(Array.isArray(data?.missing_fields) ? data.missing_fields : []);
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
                  doctor_name: data.doctor_name || doctorName,
                  medications: data.medications || reviewMeds,
                  missing_fields: [],
                },
              }
            : row
        )
      );

      setMissingFields([]);
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
          const review = data.extracted_review;
          setActiveReviewDocId(data.document_id);
          setDoctorName(review?.doctor_name || "");
          setReviewMeds(review?.medications?.length ? review.medications : [{ name: "", dosage: "", frequency: "", dose_to_take: "" }]);
          setMissingFields(["doctor_name", "medications"]);
        }
        toast({
          title: "Extraction Failed",
          description: data.error_message || "Could not extract clinical data. Please fill details manually and confirm.",
          variant: "destructive",
        });
        return;
      }

      if (data.status === "needs_confirmation") {
        const review = data.extracted_review;
        setActiveReviewDocId(data.document_id || null);
        setDoctorName(review?.doctor_name || "");
        setReviewMeds(review?.medications?.length ? review.medications : [{ name: "", dosage: "", frequency: "", dose_to_take: "" }]);
        setMissingFields(review?.missing_fields || []);
        toast({
          title: "Review Needed",
          description: data.summary || `${data.document_type || "Document"} needs confirmation before finalizing.`,
        });
        return;
      }

      const review = data.extracted_review;
      setActiveReviewDocId(data.document_id || null);
      setDoctorName(review?.doctor_name || "");
      setReviewMeds(review?.medications?.length ? review.medications : [{ name: "", dosage: "", frequency: "", dose_to_take: "" }]);
      setMissingFields(review?.missing_fields || []);

      toast({
        title: "Extraction Complete",
        description: "Review and confirm extracted details to add data to PHIG.",
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
    const review = row.extracted_review;
    setDoctorName(review?.doctor_name || "");
    setReviewMeds(review?.medications?.length ? review.medications : [{ name: "", dosage: "", frequency: "", dose_to_take: "" }]);
    setMissingFields(review?.missing_fields || []);
  };

  const updateMedAt = (index: number, field: keyof ReviewMedication, value: string) => {
    setReviewMeds((prev) => prev.map((m, i) => (i === index ? { ...m, [field]: value } : m)));
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

        <FadeIn delay={0.08}>
          <div className="page-card p-5" data-testid="card-architecture-compliance">
            <div className="flex items-center justify-between mb-3">
              <p className="font-semibold" style={{ color: "var(--text-primary)" }}>Architecture Compliance (9 Services / 9 Steps)</p>
              {architectureQuery.data?.architecture_followed && !architectureQuery.data?.degraded_mode ? (
                <Badge>Followed</Badge>
              ) : architectureQuery.data?.architecture_followed && architectureQuery.data?.degraded_mode ? (
                <Badge variant="outline">Followed (Degraded)</Badge>
              ) : (
                <Badge variant="outline">Gaps Found</Badge>
              )}
            </div>
            {architectureQuery.isLoading ? (
              <p className="text-sm" style={{ color: "var(--text-muted)" }}>Checking architecture status...</p>
            ) : architectureQuery.data ? (
              <div className="space-y-2 text-sm">
                <p style={{ color: "var(--text-secondary)" }}>
                  Services configured: {architectureQuery.data.services.filter((s) => s.configured).length}/{architectureQuery.data.services.length}
                </p>
                {architectureQuery.data.degraded_mode && (
                  <p style={{ color: "var(--accent-amber)" }}>
                    Controlled backup mode is active (degraded_mode=true).
                  </p>
                )}
                {(architectureQuery.data.warnings || []).length > 0 && (
                  <ul className="list-disc pl-5 space-y-1" style={{ color: "var(--text-secondary)" }}>
                    {(architectureQuery.data.warnings || []).map((warning) => (
                      <li key={warning}>{warning}</li>
                    ))}
                  </ul>
                )}
                {architectureQuery.data.gaps.length > 0 ? (
                  <ul className="list-disc pl-5 space-y-1" style={{ color: "var(--accent-amber)" }}>
                    {architectureQuery.data.gaps.map((gap) => (
                      <li key={gap}>{gap}</li>
                    ))}
                  </ul>
                ) : (
                  <p style={{ color: "var(--accent-emerald)" }}>All required architecture checks are currently satisfied.</p>
                )}
              </div>
            ) : (
              <p className="text-sm" style={{ color: "var(--accent-rose)" }}>Could not fetch architecture status.</p>
            )}
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
          <DialogContent className="sm:max-w-2xl" data-testid="dialog-manual-review">
            <DialogHeader>
              <DialogTitle>Confirm Extracted Details</DialogTitle>
              <DialogDescription>
                Review doctor name, medicines, and doses before adding this document to PHIG.
              </DialogDescription>
            </DialogHeader>

            {missingFields.length > 0 && (
              <div className="rounded-lg p-3" style={{ background: "rgba(245,158,11,0.08)", border: "1px solid rgba(245,158,11,0.25)" }}>
                <p className="text-xs font-medium" style={{ color: "var(--accent-amber)" }}>
                  Missing fields: {missingFields.join(", ")}
                </p>
              </div>
            )}

            <div className="space-y-3">
              <div className="space-y-1">
                <Label htmlFor="doctor_name">Doctor Name</Label>
                <Input
                  id="doctor_name"
                  value={doctorName}
                  onChange={(e) => setDoctorName(e.target.value)}
                  placeholder="Dr. Name"
                />
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>Medicines & Doses</p>
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
                      placeholder="Dose (e.g., 500 mg)"
                    />
                    <Input
                      value={med.frequency || ""}
                      onChange={(e) => updateMedAt(idx, "frequency", e.target.value)}
                      placeholder="Frequency (e.g., BD)"
                    />
                    <Input
                      value={med.dose_to_take || ""}
                      onChange={(e) => updateMedAt(idx, "dose_to_take", e.target.value)}
                      placeholder="Dose to be taken"
                    />
                  </div>
                ))}
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
              <Button onClick={() => confirmMutation.mutate()} disabled={confirmMutation.isPending || !activeResult?.document_id}>
                {confirmMutation.isPending ? "Confirming..." : "Confirm & Add to PHIG"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </Layout>
  );
}
