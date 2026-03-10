import { useQuery } from "@tanstack/react-query";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Layout } from "@/components/layout";
import { FadeIn, StaggerContainer, StaggerItem, CountUp } from "@/components/animations";
import { OrbitScoreRadial, HealthMetricsChart, CategoryBreakdownBar } from "@/components/charts";
import { Trophy, TrendingUp, Target, Star, Upload, Shield } from "lucide-react";

const BADGES = [
  { id: "first-upload", label: "First Upload", icon: Upload, description: "Uploaded your first document", color: "var(--accent-cyan)" },
  { id: "score-50", label: "Score 50+", icon: TrendingUp, description: "Reached Orbit Score 50", color: "var(--accent-violet)" },
  { id: "five-meds", label: "Med Tracker", icon: Shield, description: "Tracking 5+ medications", color: "var(--accent-emerald)" },
  { id: "streak-7", label: "7-Day Streak", icon: Star, description: "7 consecutive days active", color: "var(--accent-amber)" },
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

  const earnedBadges = [score >= 0, score >= 50, true, score >= 60];

  const ringSize = 240;
  const r = (ringSize - 8) / 2;
  const circumference = 2 * Math.PI * r;
  const offset = circumference - (score / 100) * circumference;
  const scoreColor = score >= 70 ? "var(--accent-emerald)" : score >= 40 ? "var(--accent-amber)" : "var(--accent-rose)";

  return (
    <Layout>
      <div className="space-y-8">
        <FadeIn>
          <div>
            <h1 className="text-[28px] font-semibold" style={{ color: "var(--text-primary)" }} data-testid="text-orbit-title">
              Orbit Score
            </h1>
            <p className="text-sm mt-1" style={{ color: "var(--text-secondary)" }}>
              Your comprehensive health score and progress
            </p>
          </div>
        </FadeIn>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
          <FadeIn delay={0.1}>
            <div
              className="rounded-xl p-6 lg:row-span-2 flex flex-col items-center"
              style={{ background: "var(--bg-card)", border: "1px solid var(--border-subtle)" }}
              data-testid="card-orbit-main"
            >
              <div className="flex items-center gap-2 self-start mb-6">
                <Target className="h-5 w-5" style={{ color: "var(--accent-cyan)" }} />
                <span className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>Health Score</span>
              </div>

              {loading ? (
                <Skeleton className="h-[240px] w-[240px] rounded-full" />
              ) : (
                <>
                  <div className="relative" style={{ width: ringSize, height: ringSize }}>
                    <svg width={ringSize} height={ringSize} viewBox={`0 0 ${ringSize} ${ringSize}`}>
                      <defs>
                        <linearGradient id="orbit-ring-grad" x1="0%" y1="0%" x2="100%" y2="100%">
                          <stop offset="0%" stopColor="var(--accent-cyan)" />
                          <stop offset="100%" stopColor="var(--accent-violet)" />
                        </linearGradient>
                      </defs>
                      <circle cx={ringSize / 2} cy={ringSize / 2} r={r} fill="none" stroke="var(--border-subtle)" strokeWidth={6} />
                      <circle
                        cx={ringSize / 2}
                        cy={ringSize / 2}
                        r={r}
                        fill="none"
                        stroke="url(#orbit-ring-grad)"
                        strokeWidth={6}
                        strokeLinecap="round"
                        strokeDasharray={circumference}
                        strokeDashoffset={offset}
                        transform={`rotate(-90 ${ringSize / 2} ${ringSize / 2})`}
                        style={{ transition: "stroke-dashoffset 600ms ease-out" }}
                      />
                    </svg>
                    <div className="absolute inset-0 flex flex-col items-center justify-center">
                      <span className="font-mono text-[72px] font-bold leading-none" style={{ color: "var(--text-primary)" }} data-testid="text-orbit-score">
                        <CountUp end={Math.round(score)} />
                      </span>
                      <span className="text-xs mt-1" style={{ color: "var(--text-muted)" }}>out of 100</span>
                    </div>
                  </div>

                  <Badge
                    className="mt-4 text-sm border"
                    style={{
                      background: `color-mix(in srgb, ${scoreColor} 12%, transparent)`,
                      color: scoreColor,
                      borderColor: `color-mix(in srgb, ${scoreColor} 30%, transparent)`,
                    }}
                    data-testid="badge-score-status"
                  >
                    {score >= 70 ? "Good" : score >= 40 ? "Improving" : "Needs Attention"}
                  </Badge>
                  <p className="text-xs mt-2 text-center" style={{ color: "var(--text-muted)" }}>
                    {score >= 70
                      ? "Great job! Keep maintaining your health records."
                      : "Upload more records and follow your care plan to improve."}
                  </p>
                </>
              )}
            </div>
          </FadeIn>

          <FadeIn delay={0.15} className="lg:col-span-2">
            <div
              className="rounded-xl p-6"
              style={{ background: "var(--bg-card)", border: "1px solid var(--border-subtle)" }}
              data-testid="card-score-history"
            >
              <div className="flex items-center gap-2 mb-4">
                <TrendingUp className="h-5 w-5" style={{ color: "var(--accent-cyan)" }} />
                <span className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>Score History</span>
              </div>
              {loading ? (
                <Skeleton className="h-[250px] w-full" />
              ) : historyChartData.length > 0 ? (
                <HealthMetricsChart data={historyChartData} label="Orbit Score" color="#00D4FF" />
              ) : (
                <p className="text-sm text-center py-12" style={{ color: "var(--text-muted)" }}>No history data yet</p>
              )}
            </div>
          </FadeIn>

          {breakdown && (
            <FadeIn delay={0.2} className="lg:col-span-2">
              <div
                className="rounded-xl p-6"
                style={{ background: "var(--bg-card)", border: "1px solid var(--border-subtle)" }}
                data-testid="card-score-breakdown"
              >
                <div className="flex items-center gap-2 mb-4">
                  <Trophy className="h-5 w-5" style={{ color: "var(--accent-violet)" }} />
                  <span className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>Score Breakdown</span>
                </div>
                <CategoryBreakdownBar data={breakdownData} height={180} />
              </div>
            </FadeIn>
          )}

          {scoreData?.premium_required_for_breakdown && (
            <FadeIn delay={0.2} className="lg:col-span-2">
              <div
                className="rounded-xl p-6 text-center"
                style={{ background: "var(--bg-card)", border: "1px solid var(--border-subtle)" }}
                data-testid="card-premium-upsell"
              >
                <Shield className="h-10 w-10 mx-auto mb-3" style={{ color: "var(--accent-violet)" }} />
                <p className="font-semibold" style={{ color: "var(--text-primary)" }}>Upgrade to Premium</p>
                <p className="text-sm mt-1" style={{ color: "var(--text-muted)" }}>
                  Get detailed score breakdowns, category insights, and personalized recommendations
                </p>
              </div>
            </FadeIn>
          )}
        </div>

        <FadeIn delay={0.25}>
          <div
            className="rounded-xl p-6"
            style={{ background: "var(--bg-card)", border: "1px solid var(--border-subtle)" }}
            data-testid="card-badges"
          >
            <div className="flex items-center gap-2 mb-4">
              <Star className="h-5 w-5" style={{ color: "var(--accent-amber)" }} />
              <span className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>Achievements</span>
            </div>
            <StaggerContainer className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {BADGES.map((badge, i) => (
                <StaggerItem key={badge.id}>
                  <div
                    className="p-4 rounded-xl text-center"
                    style={{
                      border: earnedBadges[i] ? `1px solid color-mix(in srgb, ${badge.color} 30%, transparent)` : "1px solid var(--border-subtle)",
                      background: earnedBadges[i] ? `color-mix(in srgb, ${badge.color} 5%, transparent)` : "transparent",
                      opacity: earnedBadges[i] ? 1 : 0.4,
                    }}
                    data-testid={`badge-achievement-${badge.id}`}
                  >
                    <badge.icon className="h-8 w-8 mx-auto mb-2" style={{ color: earnedBadges[i] ? badge.color : "var(--text-muted)" }} />
                    <p className="font-medium text-sm" style={{ color: "var(--text-primary)" }}>{badge.label}</p>
                    <p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>{badge.description}</p>
                  </div>
                </StaggerItem>
              ))}
            </StaggerContainer>
          </div>
        </FadeIn>
      </div>
    </Layout>
  );
}
