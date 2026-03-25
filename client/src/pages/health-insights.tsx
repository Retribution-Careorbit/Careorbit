import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Layout } from "@/components/layout";
import { FadeIn, StaggerContainer, StaggerItem } from "@/components/animations";
import { HealthMetricsChart } from "@/components/charts";
import { Download, Lightbulb, TrendingUp, Volume2, Square } from "lucide-react";
import { apiRequest } from "@/lib/queryClient";
import { useAuthStore } from "@/lib/auth";

interface LabTrendPoint {
  date: string;
  value: number;
}

interface AffectedAreaInsight {
  area_key: string;
  area_label: string;
  marker_name: string;
  latest_value: number;
  unit: string;
  threshold: string;
  severity: "critical" | "warning" | "monitor";
  trend_direction: "up" | "down" | "stable";
  insight: string;
  points: LabTrendPoint[];
}

interface LabInsightsResponse {
  areas: AffectedAreaInsight[];
}

interface LabReportDocument {
  document_id: string;
  file_name: string;
  document_type: string;
  valid: boolean;
  uploaded_at: string;
  doctor_name?: string;
  summary?: string;
  file_url?: string;
  extracted_markers?: Array<{ name: string; value: number; unit?: string }>;
}

export default function HealthInsightsPage() {
  const [timeframe, setTimeframe] = useState<"weekly" | "monthly">("monthly");
  const [selectedArea, setSelectedArea] = useState<AffectedAreaInsight | null>(null);
  const [activeReadKey, setActiveReadKey] = useState<string | null>(null);
  const user = useAuthStore((s) => s.user);
  const nativeLang = (user?.preferredLanguage || "en").toLowerCase();

  const { data: labInsightsData, isLoading: labInsightsLoading } = useQuery<LabInsightsResponse>({
    queryKey: ["/api/patients/lab-insights"],
  });
  const { data: labReportsData, isLoading: labReportsLoading } = useQuery<{ documents: LabReportDocument[] }>({
    queryKey: ["/api/documents/lab-reports/valid"],
  });

  const severityColor: Record<string, string> = {
    critical: "var(--accent-rose)",
    warning: "var(--accent-amber)",
    monitor: "var(--accent-cyan)",
  };

  const primaryArea = selectedArea || labInsightsData?.areas?.[0] || null;

  const selectedChartData = primaryArea
    ? primaryArea.points.map((point) => ({
        date: new Date(point.date).toLocaleDateString("en-IN", { month: "short", day: "numeric" }),
        value: point.value,
      }))
    : [];

  const openLabReportPdf = async (documentId: string) => {
    const response = await apiRequest("GET", `/api/documents/file/${documentId}`);
    const blob = await response.blob();
    const blobUrl = URL.createObjectURL(blob);
    window.open(blobUrl, "_blank", "noopener,noreferrer");
    setTimeout(() => URL.revokeObjectURL(blobUrl), 60_000);
  };

  const downloadSummaryPdf = async () => {
    const response = await apiRequest("GET", "/api/summary/generate");
    const blob = await response.blob();
    const blobUrl = URL.createObjectURL(blob);
    window.open(blobUrl, "_blank", "noopener,noreferrer");
    setTimeout(() => URL.revokeObjectURL(blobUrl), 60_000);
  };

  const speakNative = async (text: string, key: string) => {
    if (!("speechSynthesis" in window)) return;
    if (activeReadKey === key) {
      window.speechSynthesis.cancel();
      setActiveReadKey(null);
      return;
    }

    let voiceText = text;
    if (nativeLang !== "en") {
      try {
        const res = await apiRequest("POST", "/api/system/translate", {
          text,
          target_lang: nativeLang,
          source_lang: "en",
        });
        const data = await res.json();
        if (typeof data?.translated_text === "string" && data.translated_text.trim()) {
          voiceText = data.translated_text.trim();
        }
      } catch {
        voiceText = text;
      }
    }

    const langMap: Record<string, string> = {
      en: "en-IN", hi: "hi-IN", bn: "bn-IN", ta: "ta-IN", te: "te-IN", mr: "mr-IN", gu: "gu-IN", kn: "kn-IN", ml: "ml-IN",
    };
    const utterance = new SpeechSynthesisUtterance(voiceText);
    utterance.lang = langMap[nativeLang] || "en-IN";
    utterance.rate = 0.95;
    utterance.onstart = () => setActiveReadKey(key);
    utterance.onend = () => setActiveReadKey(null);
    utterance.onerror = () => setActiveReadKey(null);
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utterance);
  };

  return (
    <Layout>
      <div className="space-y-6">
        <FadeIn>
          <div className="page-title-bar">
            <div>
              <h1 data-testid="text-insights-title">
                Health Insights
              </h1>
              <p>
                Lab report trends and AI-powered health recommendations
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant={timeframe === "weekly" ? "default" : "outline"}
                size="sm"
                onClick={() => setTimeframe("weekly")}
                data-testid="button-timeframe-weekly"
              >
                Weekly
              </Button>
              <Button
                variant={timeframe === "monthly" ? "default" : "outline"}
                size="sm"
                onClick={() => setTimeframe("monthly")}
                data-testid="button-timeframe-monthly"
              >
                Monthly
              </Button>
              <Button variant="outline" size="sm" onClick={downloadSummaryPdf} data-testid="button-download-summary">
                <Download className="h-4 w-4 mr-1" />
                PDF
              </Button>
            </div>
          </div>
        </FadeIn>

        <StaggerContainer className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {(labInsightsData?.areas || []).slice(0, 4).map((area, i) => {
            const color = severityColor[area.severity] || "var(--accent-cyan)";
            return (
              <StaggerItem key={area.area_key || i}>
                <button
                  className="page-card p-5 text-left w-full"
                  onClick={() => setSelectedArea(area)}
                  data-testid={`card-affected-area-${i}`}
                >
                  {labInsightsLoading ? (
                    <Skeleton className="h-20 w-full" />
                  ) : (
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <p className="text-xs" style={{ color: "var(--text-muted)" }}>{area.area_label}</p>
                        <Badge variant="outline" className="text-xs uppercase" style={{ color, borderColor: `color-mix(in srgb, ${color} 40%, transparent)` }}>
                          {area.severity}
                        </Badge>
                      </div>
                      <p className="text-2xl font-mono font-bold" style={{ color: "var(--text-primary)" }}>{area.latest_value}</p>
                      <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                        {area.marker_name} ({area.threshold})
                      </p>
                    </div>
                  )}
                </button>
              </StaggerItem>
            );
          })}
        </StaggerContainer>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          <FadeIn delay={0.15}>
            <div
              className="page-card p-6"
              data-testid="card-lab-trend"
            >
              <div className="page-card-header flex items-center justify-between">
                <div className="card-icon" style={{ background: "var(--accent-cyan-dim)" }}>
                  <TrendingUp className="h-[18px] w-[18px]" style={{ color: "var(--accent-cyan)" }} />
                </div>
                <span className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>Top Lab Marker Trend</span>
                <Button
                  variant="outline"
                  size="sm"
                  className="h-7 px-2 text-xs"
                  onClick={() => {
                    if (!primaryArea) return;
                    const text = `${primaryArea.area_label}. ${primaryArea.marker_name} latest value ${primaryArea.latest_value} ${primaryArea.unit}. Threshold ${primaryArea.threshold}. ${primaryArea.insight}`;
                    speakNative(text, "health-top-lab-trend");
                  }}
                  disabled={!primaryArea}
                  data-testid="button-read-lab-trend-summary"
                >
                  {activeReadKey === "health-top-lab-trend" ? <Square className="h-3 w-3 mr-1" /> : <Volume2 className="h-3 w-3 mr-1" />} Read
                </Button>
              </div>
              {labInsightsLoading ? (
                <Skeleton className="h-[250px] w-full" />
              ) : primaryArea && selectedChartData.length > 0 ? (
                <HealthMetricsChart data={selectedChartData} label={primaryArea.marker_name} color="#00D4FF" height={220} />
              ) : (
                <p className="text-sm text-center py-12" style={{ color: "var(--text-muted)" }}>No lab marker trend available</p>
              )}
              {primaryArea && (
                <p className="text-xs mt-3" style={{ color: "var(--text-muted)" }}>
                  {primaryArea.area_label} • Latest {primaryArea.latest_value} {primaryArea.unit} ({primaryArea.threshold})
                </p>
              )}
            </div>
          </FadeIn>

          <FadeIn delay={0.2}>
            <div
              className="page-card p-6"
              data-testid="card-lab-reports"
            >
              <div className="page-card-header">
                <div className="card-icon" style={{ background: "var(--accent-amber-dim)" }}>
                  <Download className="h-[18px] w-[18px]" style={{ color: "var(--accent-amber)" }} />
                </div>
                <span className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>Recent Lab Reports</span>
              </div>
              {labReportsLoading ? (
                <Skeleton className="h-[200px] w-full" />
              ) : (labReportsData?.documents?.length || 0) > 0 ? (
                <div className="space-y-3" data-testid="list-lab-reports">
                  {(labReportsData?.documents || []).slice(0, 5).map((doc, i) => (
                    <div key={doc.document_id || i} className="p-3 rounded-xl" style={{ border: "1px solid var(--border-subtle)", background: "var(--bg-card)" }}>
                      <div className="flex items-center justify-between gap-2">
                        <p className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>{doc.file_name}</p>
                        <Badge variant="outline" className="capitalize">valid</Badge>
                      </div>
                      <p className="text-xs mt-1" style={{ color: "var(--text-secondary)" }}>{doc.summary || "Lab report upload"}</p>
                      <p className="text-[11px] mt-2 font-mono" style={{ color: "var(--text-muted)" }}>{doc.doctor_name || "Unknown doctor"}</p>
                      <button
                        type="button"
                        className="text-xs underline"
                        style={{ color: "var(--accent-cyan)" }}
                        onClick={() => openLabReportPdf(doc.document_id)}
                      >
                        View PDF
                      </button>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-center py-12" style={{ color: "var(--text-muted)" }}>No valid lab reports uploaded yet.</p>
              )}
            </div>
          </FadeIn>
        </div>

        <FadeIn delay={0.25}>
          <div
            className="page-card p-6"
            data-testid="card-ai-insights"
          >
            <div className="page-card-header">
              <div className="card-icon" style={{ background: "var(--accent-amber-dim)" }}>
                <Lightbulb className="h-[18px] w-[18px]" style={{ color: "var(--accent-amber)" }} />
              </div>
              <span className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>Most Affected Areas</span>
            </div>
            {labInsightsLoading ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {[1, 2].map((k) => <Skeleton key={k} className="h-24 w-full" />)}
              </div>
            ) : (labInsightsData?.areas?.length || 0) > 0 ? (
              <div className="flex gap-3 overflow-x-auto pb-2" data-testid="row-affected-areas">
                {(labInsightsData?.areas || []).map((area, i) => {
                  const color = severityColor[area.severity] || "var(--accent-cyan)";
                  return (
                    <button
                      key={area.area_key}
                      className="min-w-[280px] text-left p-4 rounded-xl"
                      style={{ border: `1px solid color-mix(in srgb, ${color} 35%, transparent)`, background: "var(--bg-elevated)" }}
                      onClick={() => setSelectedArea(area)}
                      data-testid={`button-affected-area-${i}`}
                    >
                      <div className="flex items-center justify-between gap-2">
                        <p className="font-semibold text-sm" style={{ color: "var(--text-primary)" }}>{area.area_label}</p>
                        <Badge variant="outline" className="uppercase" style={{ color, borderColor: `color-mix(in srgb, ${color} 40%, transparent)` }}>
                          {area.severity}
                        </Badge>
                      </div>
                      <p className="text-xs mt-1" style={{ color: "var(--text-secondary)" }}>
                        {area.marker_name}: {area.latest_value} {area.unit} ({area.threshold})
                      </p>
                      <p className="text-xs mt-2 leading-relaxed" style={{ color: "var(--text-muted)" }}>{area.insight}</p>
                    </button>
                  );
                })}
              </div>
            ) : (
              <p className="text-sm" style={{ color: "var(--text-muted)" }}>No abnormal lab markers currently detected.</p>
            )}
          </div>
        </FadeIn>

        <Dialog open={!!selectedArea} onOpenChange={(open) => !open && setSelectedArea(null)}>
          <DialogContent style={{ background: "var(--bg-elevated)", border: "1px solid var(--border-default)" }}>
            <DialogHeader>
              <DialogTitle style={{ color: "var(--text-primary)" }}>
                {selectedArea?.area_label || "Area Trend"}
              </DialogTitle>
            </DialogHeader>
                {selectedArea && (
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <Badge variant="outline">{selectedArea.marker_name}</Badge>
                  <Badge variant="outline">Latest: {selectedArea.latest_value} {selectedArea.unit}</Badge>
                  <Badge variant="outline">Threshold: {selectedArea.threshold}</Badge>
                </div>
                {selectedChartData.length > 0 ? (
                  <HealthMetricsChart data={selectedChartData} label={selectedArea.marker_name} color="#00D4FF" height={220} />
                ) : (
                  <p className="text-sm" style={{ color: "var(--text-muted)" }}>No trend points available for this marker.</p>
                )}
                <div className="flex items-center justify-between">
                  <p className="text-xs" style={{ color: "var(--text-secondary)" }}>{selectedArea.insight}</p>
                  <span className="text-xs inline-flex items-center gap-1" style={{ color: "var(--text-muted)" }}>
                    <TrendingUp className="h-3 w-3" /> {selectedArea.trend_direction}
                  </span>
                </div>
              </div>
            )}
          </DialogContent>
        </Dialog>
      </div>
    </Layout>
  );
}
