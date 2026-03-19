import { useState, useRef } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { apiRequest, queryClient, toApiUrl } from "@/lib/queryClient";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Layout } from "@/components/layout";
import { useToast } from "@/hooks/use-toast";
import { useAuthStore } from "@/lib/auth";
import { FadeIn, StaggerContainer, StaggerItem } from "@/components/animations";
import { FileUp, Upload, CheckCircle, AlertTriangle, XCircle, Loader2 } from "lucide-react";

interface UploadResult {
  document_id?: string;
  file_name?: string;
  document_type: string;
  status: string;
  nodes_created: number;
  interaction_alerts: any[];
  confirmation_needed: any[];
  extracted_medications?: Array<{ name?: string; dosage?: string; frequency?: string }>;
  extracted_markers?: Array<{ name?: string; value?: number | string; unit?: string }>;
  doctor_name?: string;
  prescribed_on?: string;
  duration_days?: number;
  is_ongoing?: boolean;
  follow_up_date?: string;
  ocr_confidence?: number;
  source_type?: string;
  error_message?: string;
  summary?: string;
}

export default function DocumentsPage() {
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { toast } = useToast();
  const token = useAuthStore((s) => s.token);

  const { data: docsData } = useQuery<{ documents: any[] }>({
    queryKey: ["/api/documents/list"],
  });

  const results: UploadResult[] = (docsData?.documents || []).map((doc) => {
    const status = doc.processing_status || (doc.valid ? "success" : "failed");
    return {
      document_id: doc.document_id,
      file_name: doc.file_name,
      document_type: doc.document_type || "Document",
      status,
      nodes_created: Number(doc.nodes_created || 0),
      interaction_alerts: doc.interaction_alerts || [],
      confirmation_needed: doc.confirmation_needed || [],
      extracted_medications: doc.extracted_medications || [],
      extracted_markers: doc.extracted_markers || [],
      doctor_name: doc.doctor_name,
      prescribed_on: doc.prescribed_on,
      duration_days: doc.duration_days,
      is_ongoing: doc.is_ongoing,
      follow_up_date: doc.follow_up_date,
      ocr_confidence: doc.ocr_confidence,
      source_type: doc.source_type,
      error_message: status === "failed" ? (doc.error_message || doc.summary) : undefined,
      summary: doc.summary,
    };
  });

  const confirmMutation = useMutation({
    mutationFn: async (documentId: string) => {
      const res = await apiRequest("POST", "/api/confirmations/confirm", {
        node_id: documentId,
        document_id: documentId,
        confirmed: true,
      });
      return res.json();
    },
    onSuccess: async (data: { new_confidence?: number }) => {
      const keys = [
        ["/api/documents/list"],
        ["/api/patients/medications"],
        ["/api/patients/overview"],
        ["/api/orbit/score"],
      ] as const;
      for (const key of keys) {
        queryClient.invalidateQueries({ queryKey: key });
      }
      await Promise.all(keys.map((key) => queryClient.refetchQueries({ queryKey: key, type: "active" })));
      toast({
        title: "Document Confirmed",
        description: `Confidence updated deterministically. New average confidence: ${Number(data?.new_confidence || 0).toFixed(2)}`,
      });
    },
    onError: (err: Error) => {
      toast({ title: "Confirmation Failed", description: err.message, variant: "destructive" });
    },
  });

  const syncMutation = useMutation({
    mutationFn: async (documentId: string) => {
      const res = await apiRequest("POST", `/api/documents/sync/${documentId}`);
      return res.json();
    },
    onSuccess: async (data: { medications_synced?: number; markers_available?: number; appointments_created?: number }) => {
      const keys = [
        ["/api/patients/medications"],
        ["/api/patients/overview"],
        ["/api/patients/lab-insights"],
        ["/api/tests/scenarios"],
        ["/api/orbit/score"],
        ["/api/system/notifications"],
        ["/api/documents/list"],
      ] as const;

      for (const key of keys) {
        queryClient.invalidateQueries({ queryKey: key });
      }
      await Promise.all(keys.map((key) => queryClient.refetchQueries({ queryKey: key, type: "active" })));

      const meds = Number(data?.medications_synced || 0);
      const markers = Number(data?.markers_available || 0);
      const appts = Number(data?.appointments_created || 0);
      if (meds === 0 && markers === 0) {
        toast({
          title: "No Extracted Data Found",
          description: "This document has no extracted medications or lab markers to apply yet.",
          variant: "destructive",
        });
        return;
      }

      toast({
        title: "Synced to PHIG",
        description: `Applied ${meds} medication(s), found ${markers} lab marker(s), created ${appts} appointment update(s).`,
      });
    },
    onError: (err: Error) => {
      toast({ title: "Sync Failed", description: err.message, variant: "destructive" });
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
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Upload failed");
      }
      return res.json();
    },
    onSuccess: (data: UploadResult) => {
      queryClient.invalidateQueries({ queryKey: ["/api/documents/list"] });
      queryClient.invalidateQueries({ queryKey: ["/api/patients/medications"] });
      queryClient.invalidateQueries({ queryKey: ["/api/patients/overview"] });
      queryClient.invalidateQueries({ queryKey: ["/api/patients/lab-insights"] });
      queryClient.invalidateQueries({ queryKey: ["/api/tests/scenarios"] });
      queryClient.invalidateQueries({ queryKey: ["/api/documents/lab-reports/valid"] });
      queryClient.invalidateQueries({ queryKey: ["/api/system/notifications"] });
      queryClient.invalidateQueries({ queryKey: ["/api/orbit/score"] });
      if (data.status === "failed") {
        toast({
          title: "Extraction Failed",
          description: data.error_message || "Could not extract clinical data. Please upload a clearer document.",
          variant: "destructive",
        });
        return;
      }

      if (data.status === "needs_confirmation") {
        toast({
          title: "Review Needed",
          description: data.summary || `${data.document_type || "Document"} needs confirmation before finalizing.`,
        });
        return;
      }

      toast({
        title: "Document Processed",
        description: data.summary || `${data.document_type || "Document"} extracted successfully.`,
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
                      {result.doctor_name && (
                        <p><span style={{ color: "var(--text-muted)" }}>Doctor:</span> <span style={{ color: "var(--text-primary)" }}>{result.doctor_name}</span></p>
                      )}
                      {result.prescribed_on && (
                        <p><span style={{ color: "var(--text-muted)" }}>Prescription Date:</span> <span style={{ color: "var(--text-primary)" }}>{result.prescribed_on}</span></p>
                      )}
                      {typeof result.duration_days === "number" && (
                        <p><span style={{ color: "var(--text-muted)" }}>Duration:</span> <span style={{ color: "var(--text-primary)" }}>{result.duration_days} day(s)</span></p>
                      )}
                      {typeof result.is_ongoing === "boolean" && (
                        <p><span style={{ color: "var(--text-muted)" }}>Ongoing:</span> <span style={{ color: "var(--text-primary)" }}>{result.is_ongoing ? "Yes" : "No"}</span></p>
                      )}
                      {result.follow_up_date && (
                        <p><span style={{ color: "var(--text-muted)" }}>Follow-up Date:</span> <span style={{ color: "var(--text-primary)" }}>{result.follow_up_date}</span></p>
                      )}
                      <p>
                        <span style={{ color: "var(--text-muted)" }}>Nodes created:</span>{" "}
                        <span className="font-mono font-medium" style={{ color: "var(--text-primary)" }}>{result.nodes_created}</span>
                      </p>
                      {typeof result.ocr_confidence === "number" && (
                        <p>
                          <span style={{ color: "var(--text-muted)" }}>OCR Confidence:</span>{" "}
                          <span className="font-mono font-medium" style={{ color: "var(--text-primary)" }}>{result.ocr_confidence.toFixed(2)}</span>
                        </p>
                      )}
                      {result.source_type && (
                        <p>
                          <span style={{ color: "var(--text-muted)" }}>Source:</span>{" "}
                          <span style={{ color: "var(--text-primary)" }}>{result.source_type}</span>
                        </p>
                      )}
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
                      {!!result.document_id && (
                        <div className="mt-2 flex gap-2">
                          {result.status === "needs_confirmation" && (
                            <Button
                              type="button"
                              size="sm"
                              onClick={() => confirmMutation.mutate(result.document_id!)}
                              disabled={confirmMutation.isPending}
                              data-testid={`button-confirm-${result.document_id}`}
                            >
                              {confirmMutation.isPending ? "Confirming..." : "Confirm Extraction"}
                            </Button>
                          )}
                          <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            onClick={() => syncMutation.mutate(result.document_id!)}
                            disabled={syncMutation.isPending}
                            data-testid={`button-sync-phig-${result.document_id}`}
                          >
                            {syncMutation.isPending ? "Syncing..." : "Apply To PHIG"}
                          </Button>
                        </div>
                      )}
                      {result.extracted_medications && result.extracted_medications.length > 0 && (
                        <div className="mt-3 p-3 rounded-lg" style={{ background: "rgba(56,189,248,0.08)", border: "1px solid rgba(56,189,248,0.25)" }}>
                          <p className="text-xs font-medium mb-1" style={{ color: "var(--accent-cyan)" }}>
                            Extracted Medications
                          </p>
                          <div className="space-y-1">
                            {result.extracted_medications.slice(0, 4).map((med, medIdx) => (
                              <p key={medIdx} className="text-xs" style={{ color: "var(--text-secondary)" }}>
                                {(med.name || "Unknown").trim()}
                                {med.dosage ? ` - ${med.dosage}` : ""}
                                {med.frequency ? ` (${med.frequency})` : ""}
                              </p>
                            ))}
                          </div>
                        </div>
                      )}
                      {result.extracted_markers && result.extracted_markers.length > 0 && (
                        <div className="mt-3 p-3 rounded-lg" style={{ background: "rgba(34,197,94,0.08)", border: "1px solid rgba(34,197,94,0.25)" }}>
                          <p className="text-xs font-medium mb-1" style={{ color: "var(--accent-emerald)" }}>
                            Extracted Lab Markers
                          </p>
                          <div className="space-y-1">
                            {result.extracted_markers.slice(0, 4).map((marker, markerIdx) => (
                              <p key={markerIdx} className="text-xs" style={{ color: "var(--text-secondary)" }}>
                                {(marker.name || "Marker").trim()}: {String(marker.value ?? "-")}
                                {marker.unit ? ` ${marker.unit}` : ""}
                              </p>
                            ))}
                          </div>
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
      </div>
    </Layout>
  );
}
