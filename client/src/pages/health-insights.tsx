import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Layout } from "@/components/layout";
import { FadeIn, StaggerContainer, StaggerItem } from "@/components/animations";
import { HealthMetricsChart, Sparkline } from "@/components/charts";
import { Heart, Weight, Thermometer, Download, Lightbulb, TrendingUp, AlertTriangle } from "lucide-react";
import { toApiUrl } from "@/lib/queryClient";

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

export default function HealthInsightsPage() {
  const [timeframe, setTimeframe] = useState<"weekly" | "monthly">("monthly");
  const [selectedArea, setSelectedArea] = useState<AffectedAreaInsight | null>(null);

  const { data: vitalsData, isLoading } = useQuery<any>({
    queryKey: ["/api/patients/vitals"],
  });

  const { data: labInsightsData, isLoading: labInsightsLoading } = useQuery<LabInsightsResponse>({
    queryKey: ["/api/patients/lab-insights"],
  });

  const allVitals = vitalsData?.vitals || [];

  const cutoff = new Date();
  cutoff.setDate(cutoff.getDate() - (timeframe === "weekly" ? 7 : 30));
  const vitals = allVitals.filter((v: any) => new Date(v.date) >= cutoff);

  const bpData = vitals
    .filter((v: any) => v.type === "blood_pressure")
    .map((v: any) => ({
      date: new Date(v.date).toLocaleDateString("en-IN", { month: "short", day: "numeric" }),
      value: v.systolic,
      value2: v.diastolic,
    }));

  const hrData = vitals
    .filter((v: any) => v.type === "blood_pressure")
    .map((v: any) => v.heart_rate);

  const glucoseData = vitals
    .filter((v: any) => v.type === "glucose")
    .map((v: any) => ({
      date: new Date(v.date).toLocaleDateString("en-IN", { month: "short", day: "numeric" }),
      value: v.fasting,
      value2: v.post_meal,
    }));

  const glucoseSparkline = vitals
    .filter((v: any) => v.type === "glucose")
    .map((v: any) => v.fasting);

  const weightData = vitals
    .filter((v: any) => v.type === "weight")
    .map((v: any) => v.value);

  const tempData = vitals
    .filter((v: any) => v.type === "temperature")
    .map((v: any) => v.value);

  const latestBP = allVitals.filter((v: any) => v.type === "blood_pressure").slice(-1)[0];
  const latestWeight = allVitals.filter((v: any) => v.type === "weight").slice(-1)[0];
  const latestTemp = allVitals.filter((v: any) => v.type === "temperature").slice(-1)[0];

  const affectedCards = (labInsightsData?.areas || []).slice(0, 4).map((area) => {
    const severityColor = area.severity === "critical"
      ? "var(--accent-rose)"
      : area.severity === "warning"
        ? "var(--accent-amber)"
        : "var(--accent-cyan)";
    const sparkData = Array.isArray(area.points) ? area.points.map((p) => p.value) : [];
    return {
      title: area.area_label,
      value: `${area.latest_value}`,
      unit: `${area.marker_name} (${area.unit})`,
      icon: AlertTriangle,
      color: severityColor,
      sparkData,
      status: area.severity,
    };
  });

  const fallbackCards = [
    {
      title: "Blood Pressure",
      value: latestBP ? `${latestBP.systolic}/${latestBP.diastolic}` : "—",
      unit: "mmHg",
      icon: Heart,
      color: "#00D4FF",
      sparkData: hrData,
      status: latestBP && latestBP.systolic < 140 ? "normal" : "warning",
    },
    {
      title: "Weight",
      value: latestWeight ? `${latestWeight.value}` : "—",
      unit: "kg",
      icon: Weight,
      color: "#10B981",
      sparkData: weightData,
      status: "normal",
    },
    {
      title: "Temperature",
      value: latestTemp ? `${latestTemp.value}` : "—",
      unit: "°F",
      icon: Thermometer,
      color: "#F59E0B",
      sparkData: tempData,
      status: latestTemp && latestTemp.value <= 99.5 ? "normal" : "warning",
    },
  ];

  const topCards = affectedCards.length > 0 ? affectedCards : fallbackCards;

  const severityColor: Record<string, string> = {
    critical: "var(--accent-rose)",
    warning: "var(--accent-amber)",
    monitor: "var(--accent-cyan)",
  };

  const selectedChartData = selectedArea
    ? selectedArea.points.map((point) => ({
        date: new Date(point.date).toLocaleDateString("en-IN", { month: "short", day: "numeric" }),
        value: point.value,
      }))
    : [];

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
                Vital signs trends and AI-powered health recommendations
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
              <Button variant="outline" size="sm" asChild>
                <a href={toApiUrl("/api/summary/generate")} target="_blank" rel="noreferrer" data-testid="button-download-summary">
                  <Download className="h-4 w-4 mr-1" />
                  PDF
                </a>
              </Button>
            </div>
          </div>
        </FadeIn>

        <StaggerContainer className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {topCards.map((card) => (
            <StaggerItem key={card.title}>
              <div
                className="page-card p-5"
                data-testid={`card-vital-${card.title.toLowerCase().replace(/\s/g, "-")}`}
              >
                {isLoading ? (
                  <Skeleton className="h-20 w-full" />
                ) : (
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center gap-2 mb-2">
                        <div
                          className="w-9 h-9 rounded-xl flex items-center justify-center"
                          style={{ backgroundColor: `${card.color}15` }}
                        >
                          <card.icon className="h-4 w-4" style={{ color: card.color }} />
                        </div>
                        <span className="text-xs" style={{ color: "var(--text-muted)" }}>{card.title}</span>
                      </div>
                      <p className="text-2xl font-mono font-bold" style={{ color: "var(--text-primary)" }}>{card.value}</p>
                      <p className="text-xs" style={{ color: "var(--text-muted)" }}>{card.unit}</p>
                      <Badge
                        className="mt-2 text-xs border"
                        style={{
                          background: card.status === "critical"
                            ? "var(--accent-rose-dim)"
                            : card.status === "warning"
                              ? "var(--accent-amber-dim)"
                              : "var(--accent-emerald-dim)",
                          color: card.status === "critical"
                            ? "var(--accent-rose)"
                            : card.status === "warning"
                              ? "var(--accent-amber)"
                              : "var(--accent-emerald)",
                          borderColor: card.status === "critical"
                            ? "color-mix(in srgb, var(--accent-rose) 30%, transparent)"
                            : card.status === "warning"
                              ? "color-mix(in srgb, var(--accent-amber) 30%, transparent)"
                              : "color-mix(in srgb, var(--accent-emerald) 30%, transparent)",
                        }}
                      >
                        {String(card.status).toUpperCase()}
                      </Badge>
                    </div>
                    {card.sparkData.length > 1 && (
                      <Sparkline data={card.sparkData} color={card.color} />
                    )}
                  </div>
                )}
              </div>
            </StaggerItem>
          ))}
        </StaggerContainer>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          <FadeIn delay={0.15}>
            <div
              className="page-card p-6"
              data-testid="card-bp-chart"
            >
              <div className="page-card-header">
                <div className="card-icon" style={{ background: "var(--accent-cyan-dim)" }}>
                  <Heart className="h-[18px] w-[18px]" style={{ color: "var(--accent-cyan)" }} />
                </div>
                <span className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>Blood Pressure Trends</span>
              </div>
              {isLoading ? (
                <Skeleton className="h-[250px] w-full" />
              ) : bpData.length > 0 ? (
                <HealthMetricsChart data={bpData} label="Systolic" label2="Diastolic" color="#00D4FF" color2="#7C3AED" />
              ) : (
                <p className="text-sm text-center py-12" style={{ color: "var(--text-muted)" }}>No BP data available</p>
              )}
            </div>
          </FadeIn>

          <FadeIn delay={0.2}>
            <div
              className="page-card p-6"
              data-testid="card-affected-trend-chart"
            >
              <div className="page-card-header">
                <div className="card-icon" style={{ background: "var(--accent-violet-dim)" }}>
                  <TrendingUp className="h-[18px] w-[18px]" style={{ color: "var(--accent-violet)" }} />
                </div>
                <span className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>
                  {selectedArea ? `${selectedArea.area_label} Trend` : "Most Affected Marker Trend"}
                </span>
              </div>
              {isLoading ? (
                <Skeleton className="h-[250px] w-full" />
              ) : selectedChartData.length > 0 ? (
                <HealthMetricsChart data={selectedChartData} label={selectedArea?.marker_name || "Marker"} color="#10B981" />
              ) : (
                <p className="text-sm text-center py-12" style={{ color: "var(--text-muted)" }}>Select an affected area to view marker trend</p>
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
