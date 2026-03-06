import { useState, useRef } from "react";
import { useMutation } from "@tanstack/react-query";
import { queryClient } from "@/lib/queryClient";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Layout } from "@/components/layout";
import { useToast } from "@/hooks/use-toast";
import { useAuthStore } from "@/lib/auth";
import { FadeIn, StaggerContainer, StaggerItem } from "@/components/animations";
import { FileUp, Upload, CheckCircle, AlertTriangle, XCircle, Loader2 } from "lucide-react";

interface UploadResult {
  document_type: string;
  status: string;
  nodes_created: number;
  interaction_alerts: any[];
  confirmation_needed: any[];
}

export default function DocumentsPage() {
  const [results, setResults] = useState<UploadResult[]>([]);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { toast } = useToast();
  const token = useAuthStore((s) => s.token);

  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append("file", file);
      const res = await fetch("/api/documents/upload", {
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
    onSuccess: (data) => {
      setResults((prev) => [data, ...prev]);
      queryClient.invalidateQueries({ queryKey: ["/api/patients/medications"] });
      queryClient.invalidateQueries({ queryKey: ["/api/patients/overview"] });
      toast({ title: "Document Uploaded", description: `${data.document_type || "Document"} processed` });
    },
    onError: (err: Error) => {
      toast({ title: "Upload Failed", description: err.message, variant: "destructive" });
    },
  });

  const handleUpload = (file: File) => {
    const allowedTypes = ["image/jpeg", "image/png", "image/webp", "image/heic"];
    if (!allowedTypes.includes(file.type)) {
      toast({ title: "Invalid File", description: "Only JPEG, PNG, WebP, and HEIC images are allowed", variant: "destructive" });
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
      case "success": return <CheckCircle className="h-5 w-5 text-emerald-600" />;
      case "needs_confirmation": return <AlertTriangle className="h-5 w-5 text-amber-600" />;
      case "failed": return <XCircle className="h-5 w-5 text-red-600" />;
      default: return null;
    }
  };

  return (
    <Layout>
      <div className="space-y-6">
        <FadeIn>
          <div>
            <h1 className="text-3xl font-heading font-bold tracking-tight" data-testid="text-documents-title">Documents</h1>
            <p className="text-muted-foreground mt-1.5">
              Upload prescriptions, lab reports, or medicine strip photos for AI extraction
            </p>
          </div>
        </FadeIn>

        <FadeIn delay={0.1}>
          <Card className="overflow-hidden">
            <CardContent className="p-8">
              <div
                role="button"
                tabIndex={0}
                aria-label="Upload document. Drop a file here or press Enter to browse"
                className={`border-2 border-dashed rounded-xl p-12 text-center transition-all duration-300 cursor-pointer
                  ${dragOver
                    ? "border-primary bg-primary/5 shadow-inner"
                    : "border-muted-foreground/20 hover:border-primary/40 hover:bg-accent/50"
                  }`}
                onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                onDragLeave={() => setDragOver(false)}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); fileInputRef.current?.click(); } }}
                data-testid="dropzone-upload"
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/jpeg,image/png,image/webp,image/heic"
                  onChange={handleFileChange}
                  className="hidden"
                  data-testid="input-file"
                />
                {uploadMutation.isPending ? (
                  <div className="space-y-4">
                    <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mx-auto">
                      <Loader2 className="h-8 w-8 text-primary animate-spin" data-testid="spinner-processing" />
                    </div>
                    <p className="text-lg font-heading font-medium">Processing document...</p>
                    <p className="text-sm text-muted-foreground">AI is extracting health data</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mx-auto">
                      <Upload className="h-8 w-8 text-muted-foreground" />
                    </div>
                    <p className="text-lg font-heading font-medium">Drop your document here</p>
                    <p className="text-sm text-muted-foreground">
                      JPEG, PNG, WebP, or HEIC up to 10MB
                    </p>
                    <Button variant="outline" className="shadow-sm" data-testid="button-browse">
                      <FileUp className="h-4 w-4 mr-2" />
                      Browse Files
                    </Button>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </FadeIn>

        {results.length > 0 && (
          <div className="space-y-4">
            <h2 className="text-xl font-heading font-semibold">Upload Results</h2>
            <StaggerContainer className="space-y-3">
              {results.map((result, i) => (
                <StaggerItem key={i}>
                  <Card data-testid={`card-result-${i}`}>
                    <CardHeader className="pb-2">
                      <div className="flex items-center justify-between">
                        <CardTitle className="text-base flex items-center gap-2 font-heading">
                          {getStatusIcon(result.status)}
                          {result.document_type || "Document"}
                        </CardTitle>
                        <Badge variant={result.status === "success" ? "default" : "outline"}>
                          {result.status}
                        </Badge>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="text-sm space-y-1.5">
                        <p><span className="text-muted-foreground">Nodes created:</span> <span className="font-medium">{result.nodes_created}</span></p>
                        {result.interaction_alerts?.length > 0 && (
                          <div className="mt-2 p-3 rounded-lg bg-destructive/5 border border-destructive/20 text-sm">
                            <p className="font-medium text-destructive">
                              {result.interaction_alerts.length} interaction alert(s)
                            </p>
                          </div>
                        )}
                        {result.confirmation_needed?.length > 0 && (
                          <div className="mt-2 p-3 rounded-lg bg-amber-100/50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 text-sm">
                            <p className="font-medium text-amber-800 dark:text-amber-200">
                              {result.confirmation_needed.length} item(s) need confirmation
                            </p>
                          </div>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                </StaggerItem>
              ))}
            </StaggerContainer>
          </div>
        )}
      </div>
    </Layout>
  );
}
