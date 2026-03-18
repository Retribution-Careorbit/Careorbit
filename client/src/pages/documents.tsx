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
      error_message: status === "failed" ? (doc.error_message || doc.summary) : undefined,
      summary: doc.summary,
    };
  });

  const syncMutation = useMutation({
    mutationFn: async (documentId: string) => {
      const res = await apiRequest("POST", `/api/documents/sync/${documentId}`);
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/patients/medications"] });
      queryClient.invalidateQueries({ queryKey: ["/api/patients/overview"] });
      queryClient.invalidateQueries({ queryKey: ["/api/patients/lab-insights"] });
      queryClient.invalidateQueries({ queryKey: ["/api/tests/scenarios"] });
      queryClient.invalidateQueries({ queryKey: ["/api/orbit/score"] });
      queryClient.invalidateQueries({ queryKey: ["/api/system/notifications"] });
      queryClient.invalidateQueries({ queryKey: ["/api/documents/list"] });
      toast({ title: "Synced to PHIG", description: "Document data has been synced and other tabs are updated." });
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
                      {!!result.document_id && (
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          className="mt-2"
                          onClick={() => syncMutation.mutate(result.document_id!)}
                          disabled={syncMutation.isPending}
                          data-testid={`button-sync-phig-${result.document_id}`}
                        >
                          {syncMutation.isPending ? "Syncing..." : "Apply To PHIG"}
                        </Button>
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
