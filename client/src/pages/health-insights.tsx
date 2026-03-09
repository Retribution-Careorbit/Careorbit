import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Layout } from "@/components/layout";
import { FadeIn, StaggerContainer, StaggerItem, HoverCard } from "@/components/animations";
import { HealthMetricsChart, Sparkline } from "@/components/charts";
import { Heart, Droplets, Weight, Thermometer, TrendingDown, TrendingUp, AlertCircle, Download, Lightbulb } from "lucide-react";

const INSIGHTS = [
  {
    title: "Blood Pressure Improving",
    description: "Your systolic BP has decreased from 148 to 128 mmHg over the past 6 weeks. Keep up the good work with your Amlodipine regimen.",
    icon: TrendingDown,
    color: "text-green-500",
    bgColor: "bg-green-500/10",
    type: "positive",
  },
  {
    title: "HbA1c Above Target",
    description: "Your HbA1c is 7.8%, above the recommended <5.7%. Discuss with your doctor about adjusting your Metformin dosage or diet plan.",
    icon: AlertCircle,
    color: "text-amber-500",
    bgColor: "bg-amber-500/10",
    type: "warning",
  },
  {
    title: "Weight Loss Progress",
    description: "You've lost 2kg in the past month (82.5 → 80.5 kg). Steady weight loss supports your diabetes and BP management.",
    icon: TrendingDown,
    color: "text-cyan-400",
    bgColor: "bg-cyan-400/10",
    type: "positive",
  },
  {
    title: "Kidney Function Alert",
    description: "Your eGFR is 52 mL/min (Stage 3a CKD). Avoid NSAIDs like Ibuprofen and ensure regular monitoring.",
    icon: AlertCircle,
    color: "text-red-500",
    bgColor: "bg-red-500/10",
    type: "critical",
  },
];

export default function HealthInsightsPage() {
  const [timeframe, setTimeframe] = useState<"weekly" | "monthly">("monthly");

  const { data: vitalsData, isLoading } = useQuery<any>({
    queryKey: ["/api/patients/vitals"],
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
  const latestGlucose = allVitals.filter((v: any) => v.type === "glucose").slice(-1)[0];
  const latestWeight = allVitals.filter((v: any) => v.type === "weight").slice(-1)[0];
  const latestTemp = allVitals.filter((v: any) => v.type === "temperature").slice(-1)[0];

  const vitalCards = [
    {
      title: "Blood Pressure",
      value: latestBP ? `${latestBP.systolic}/${latestBP.diastolic}` : "—",
      unit: "mmHg",
      icon: Heart,
      color: "#00d9ff",
      sparkData: hrData,
      status: latestBP && latestBP.systolic < 140 ? "normal" : "warning",
    },
    {
      title: "Blood Glucose",
      value: latestGlucose ? `${latestGlucose.fasting}` : "—",
      unit: "mg/dL (fasting)",
      icon: Droplets,
      color: "#7c3aed",
      sparkData: glucoseSparkline,
      status: latestGlucose && latestGlucose.fasting < 140 ? "normal" : "warning",
    },
    {
      title: "Weight",
      value: latestWeight ? `${latestWeight.value}` : "—",
      unit: "kg",
      icon: Weight,
      color: "#10b981",
      sparkData: weightData,
      status: "normal",
    },
    {
      title: "Temperature",
      value: latestTemp ? `${latestTemp.value}` : "—",
      unit: "°F",
      icon: Thermometer,
      color: "#fb923c",
      sparkData: tempData,
      status: latestTemp && latestTemp.value <= 99.5 ? "normal" : "warning",
    },
  ];

  return (
    <Layout>
      <div className="space-y-8">
        <FadeIn>
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-heading font-bold tracking-tight" data-testid="text-insights-title">
                Health Insights
              </h1>
              <p className="text-muted-foreground mt-1.5 text-base">
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
                <a href="/api/summary/generate" target="_blank" data-testid="button-download-summary">
                  <Download className="h-4 w-4 mr-1" />
                  PDF
                </a>
              </Button>
            </div>
          </div>
        </FadeIn>

        <StaggerContainer className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {vitalCards.map((card) => (
            <StaggerItem key={card.title}>
              <HoverCard>
                <Card className="glass" data-testid={`card-vital-${card.title.toLowerCase().replace(/\s/g, "-")}`}>
                  <CardContent className="p-5">
                    {isLoading ? (
                      <Skeleton className="h-20 w-full" />
                    ) : (
                      <div className="flex items-start justify-between">
                        <div>
                          <div className="flex items-center gap-2 mb-2">
                            <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ backgroundColor: `${card.color}15` }}>
                              <card.icon className="h-4 w-4" style={{ color: card.color }} />
                            </div>
                            <span className="text-sm text-muted-foreground">{card.title}</span>
                          </div>
                          <p className="text-2xl font-heading font-bold">{card.value}</p>
                          <p className="text-xs text-muted-foreground">{card.unit}</p>
                          <Badge
                            className={`mt-2 text-xs ${
                              card.status === "normal"
                                ? "bg-green-500/10 text-green-500 border-green-500/30"
                                : "bg-amber-500/10 text-amber-500 border-amber-500/30"
                            }`}
                          >
                            {card.status === "normal" ? "Normal" : "Monitor"}
                          </Badge>
                        </div>
                        {card.sparkData.length > 1 && (
                          <Sparkline data={card.sparkData} color={card.color} />
                        )}
                      </div>
                    )}
                  </CardContent>
                </Card>
              </HoverCard>
            </StaggerItem>
          ))}
        </StaggerContainer>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <FadeIn delay={0.15}>
            <Card className="glass" data-testid="card-bp-chart">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 font-heading text-base">
                  <Heart className="h-5 w-5 text-cyan-400" />
                  Blood Pressure Trends
                </CardTitle>
              </CardHeader>
              <CardContent>
                {isLoading ? (
                  <Skeleton className="h-[250px] w-full" />
                ) : bpData.length > 0 ? (
                  <HealthMetricsChart
                    data={bpData}
                    label="Systolic"
                    label2="Diastolic"
                    color="#00d9ff"
                    color2="#7c3aed"
                  />
                ) : (
                  <p className="text-sm text-muted-foreground text-center py-12">No BP data available</p>
                )}
              </CardContent>
            </Card>
          </FadeIn>

          <FadeIn delay={0.2}>
            <Card className="glass" data-testid="card-glucose-chart">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 font-heading text-base">
                  <Droplets className="h-5 w-5 text-purple-400" />
                  Blood Glucose Trends
                </CardTitle>
              </CardHeader>
              <CardContent>
                {isLoading ? (
                  <Skeleton className="h-[250px] w-full" />
                ) : glucoseData.length > 0 ? (
                  <HealthMetricsChart
                    data={glucoseData}
                    label="Fasting"
                    label2="Post-meal"
                    color="#10b981"
                    color2="#fb923c"
                  />
                ) : (
                  <p className="text-sm text-muted-foreground text-center py-12">No glucose data available</p>
                )}
              </CardContent>
            </Card>
          </FadeIn>
        </div>

        <FadeIn delay={0.25}>
          <Card className="glass" data-testid="card-ai-insights">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 font-heading">
                <Lightbulb className="h-5 w-5 text-amber-400" />
                AI Health Insights
              </CardTitle>
            </CardHeader>
            <CardContent>
              <StaggerContainer className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {INSIGHTS.map((insight, i) => (
                  <StaggerItem key={i}>
                    <HoverCard>
                      <div
                        className={`p-4 rounded-xl border border-border/50 hover:border-primary/20 transition-colors`}
                        data-testid={`card-insight-${i}`}
                      >
                        <div className="flex items-start gap-3">
                          <div className={`w-9 h-9 rounded-lg ${insight.bgColor} flex items-center justify-center shrink-0`}>
                            <insight.icon className={`h-4 w-4 ${insight.color}`} />
                          </div>
                          <div>
                            <p className="font-medium text-sm">{insight.title}</p>
                            <p className="text-xs text-muted-foreground mt-1 leading-relaxed">{insight.description}</p>
                          </div>
                        </div>
                      </div>
                    </HoverCard>
                  </StaggerItem>
                ))}
              </StaggerContainer>
            </CardContent>
          </Card>
        </FadeIn>
      </div>
    </Layout>
  );
}
