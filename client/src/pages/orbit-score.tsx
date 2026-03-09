import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Layout } from "@/components/layout";
import { FadeIn, StaggerContainer, StaggerItem, HoverCard } from "@/components/animations";
import { OrbitScoreRadial, HealthMetricsChart, CategoryBreakdownBar } from "@/components/charts";
import { Trophy, TrendingUp, Target, Star, Upload, Calendar, Shield } from "lucide-react";

const BADGES = [
  { id: "first-upload", label: "First Upload", icon: Upload, description: "Uploaded your first document", color: "text-cyan-400" },
  { id: "score-50", label: "Score 50+", icon: TrendingUp, description: "Reached Orbit Score 50", color: "text-purple-400" },
  { id: "five-meds", label: "Med Tracker", icon: Shield, description: "Tracking 5+ medications", color: "text-green-400" },
  { id: "streak-7", label: "7-Day Streak", icon: Star, description: "7 consecutive days active", color: "text-amber-400" },
];

export default function OrbitScorePage() {
  const { data: scoreData, isLoading: scoreLoading } = useQuery<any>({
    queryKey: ["/api/orbit/score"],
  });

  const { data: historyData, isLoading: historyLoading } = useQuery<any[]>({
    queryKey: ["/api/orbit/score/history"],
  });

  const loading = scoreLoading || historyLoading;
  const score = scoreData?.total_score || 0;
  const breakdown = scoreData?.breakdown;
  const history = Array.isArray(historyData) ? historyData : [];

  const historyChartData = history.map((h: any) => ({
    date: new Date(h.computed_at).toLocaleDateString("en-IN", { month: "short", day: "numeric" }),
    value: h.total_score,
  }));

  const breakdownData = breakdown
    ? [
        { name: "Completeness", value: Math.round((breakdown.completeness || 0) * 100) },
        { name: "Confidence", value: Math.round((breakdown.avg_confidence || 0) * 100) },
        { name: "Interactions", value: Math.round((1 - (breakdown.interaction_risk || 0)) * 100) },
        { name: "Care Gaps", value: Math.round((1 - (breakdown.care_gap_penalty || 0)) * 100) },
      ]
    : [];

  const earnedBadges = [
    score >= 0,
    score >= 50,
    true,
    score >= 60,
  ];

  return (
    <Layout>
      <div className="space-y-8">
        <FadeIn>
          <div>
            <h1 className="text-3xl font-heading font-bold tracking-tight" data-testid="text-orbit-title">
              Orbit Score
            </h1>
            <p className="text-muted-foreground mt-1.5 text-base">
              Your comprehensive health score and progress
            </p>
          </div>
        </FadeIn>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <FadeIn delay={0.1}>
            <Card className="glass lg:row-span-2" data-testid="card-orbit-main">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 font-heading">
                  <Target className="h-5 w-5 text-primary" />
                  Health Score
                </CardTitle>
              </CardHeader>
              <CardContent className="flex flex-col items-center">
                {loading ? (
                  <Skeleton className="h-[200px] w-[200px] rounded-full" />
                ) : (
                  <>
                    <OrbitScoreRadial score={score} size={220} />
                    <div className="mt-4 text-center">
                      <Badge
                        className={`text-sm ${
                          score >= 70
                            ? "bg-green-500/10 text-green-500 border-green-500/30"
                            : score >= 40
                            ? "bg-amber-500/10 text-amber-500 border-amber-500/30"
                            : "bg-red-500/10 text-red-500 border-red-500/30"
                        }`}
                        data-testid="badge-score-status"
                      >
                        {score >= 70 ? "Good" : score >= 40 ? "Improving" : "Needs Attention"}
                      </Badge>
                      <p className="text-sm text-muted-foreground mt-2">
                        {score >= 70
                          ? "Great job! Keep maintaining your health records."
                          : "Upload more records and follow your care plan to improve."}
                      </p>
                    </div>
                  </>
                )}
              </CardContent>
            </Card>
          </FadeIn>

          <FadeIn delay={0.15} className="lg:col-span-2">
            <Card className="glass" data-testid="card-score-history">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 font-heading">
                  <TrendingUp className="h-5 w-5 text-primary" />
                  Score History
                </CardTitle>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <Skeleton className="h-[250px] w-full" />
                ) : historyChartData.length > 0 ? (
                  <HealthMetricsChart data={historyChartData} label="Orbit Score" color="#00d9ff" />
                ) : (
                  <p className="text-sm text-muted-foreground text-center py-12">No history data yet</p>
                )}
              </CardContent>
            </Card>
          </FadeIn>

          {breakdown && (
            <FadeIn delay={0.2} className="lg:col-span-2">
              <Card className="glass" data-testid="card-score-breakdown">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 font-heading">
                    <Trophy className="h-5 w-5 text-secondary" />
                    Score Breakdown
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <CategoryBreakdownBar data={breakdownData} height={180} />
                </CardContent>
              </Card>
            </FadeIn>
          )}

          {scoreData?.premium_required_for_breakdown && (
            <FadeIn delay={0.2} className="lg:col-span-2">
              <Card className="glass border-secondary/30" data-testid="card-premium-upsell">
                <CardContent className="p-6 text-center">
                  <Shield className="h-10 w-10 text-secondary mx-auto mb-3" />
                  <p className="font-heading font-semibold">Upgrade to Premium</p>
                  <p className="text-sm text-muted-foreground mt-1">
                    Get detailed score breakdowns, category insights, and personalized recommendations
                  </p>
                </CardContent>
              </Card>
            </FadeIn>
          )}
        </div>

        <FadeIn delay={0.25}>
          <Card className="glass" data-testid="card-badges">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 font-heading">
                <Star className="h-5 w-5 text-amber-400" />
                Achievements
              </CardTitle>
            </CardHeader>
            <CardContent>
              <StaggerContainer className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {BADGES.map((badge, i) => (
                  <StaggerItem key={badge.id}>
                    <HoverCard>
                      <div
                        className={`p-4 rounded-xl border text-center transition-all ${
                          earnedBadges[i]
                            ? "border-primary/30 bg-primary/5"
                            : "border-border/30 opacity-40"
                        }`}
                        data-testid={`badge-achievement-${badge.id}`}
                      >
                        <badge.icon className={`h-8 w-8 mx-auto mb-2 ${earnedBadges[i] ? badge.color : "text-muted-foreground"}`} />
                        <p className="font-medium text-sm">{badge.label}</p>
                        <p className="text-xs text-muted-foreground mt-0.5">{badge.description}</p>
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
