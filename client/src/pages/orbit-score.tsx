import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Layout } from "@/components/layout";
import { FadeIn, StaggerContainer, StaggerItem, CountUp } from "@/components/animations";
import { CategoryBreakdownBar } from "@/components/charts";
import { Trophy, TrendingUp, Target, Star, Upload, Shield } from "lucide-react";

const BADGES = [
  { id: "first-upload", label: "First Upload", icon: Upload, description: "Uploaded your first document", color: "var(--accent-cyan)" },
  { id: "score-50", label: "Score 50+", icon: TrendingUp, description: "Reached Orbit Score 50", color: "var(--accent-violet)" },
  { id: "five-meds", label: "Med Tracker", icon: Shield, description: "Tracking 5+ medications", color: "var(--accent-emerald)" },
  { id: "streak-7", label: "7-Day Streak", icon: Star, description: "7 consecutive days active", color: "var(--accent-amber)" },
];

export default function OrbitScorePage() {
  const [selectedAction, setSelectedAction] = useState<any | null>(null);

  const { data: scoreData, isLoading: scoreLoading } = useQuery<any>({
    queryKey: ["/api/orbit/score"],
  });


  const { data: improvementPlan } = useQuery<any>({
    queryKey: ["/api/orbit/improvement-plan"],
  });

  const loading = scoreLoading;
  const score = scoreData?.total_score || 0;
  const breakdown = scoreData?.breakdown;

  const breakdownData = breakdown
    ? [
        { name: "Completeness", value: Math.round(breakdown.completeness || 0) },
        { name: "Avg Confidence", value: Math.round(breakdown.avg_confidence || 0) },
        { name: "Interaction Risk", value: Math.round(breakdown.interaction_risk || 0) },
        { name: "Care Gap Status", value: Math.round(breakdown.care_gap_status || 0) },
        { name: "Adherence (30d)", value: Math.round(breakdown.adherence_rate || 0) },
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
          <div className="page-title-bar">
            <div>
              <h1 data-testid="text-orbit-title">
                Orbit Score
              </h1>
              <p>
                Your comprehensive health score and progress
              </p>
            </div>
          </div>
        </FadeIn>

        <div className="grid grid-cols-1 gap-5">
          <FadeIn delay={0.1}>
            <div
              className="page-card p-6 flex flex-col items-center"
              data-testid="card-orbit-main"
            >
              <div className="page-card-header self-stretch">
                <div className="card-icon" style={{ background: "var(--accent-cyan-dim)" }}>
                  <Target className="h-[18px] w-[18px]" style={{ color: "var(--accent-cyan)" }} />
                </div>
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

          {breakdown && (
            <FadeIn delay={0.15}>
              <div
                className="page-card p-6"
                data-testid="card-score-breakdown"
              >
                <div className="page-card-header">
                  <div className="card-icon" style={{ background: "var(--accent-violet-dim)" }}>
                    <Trophy className="h-[18px] w-[18px]" style={{ color: "var(--accent-violet)" }} />
                  </div>
                  <span className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>Score Breakdown</span>
                </div>
                <CategoryBreakdownBar data={breakdownData} height={180} />
              </div>
            </FadeIn>
          )}

        </div>

        <FadeIn delay={0.25}>
          <div
            className="page-card p-6"
            data-testid="card-badges"
          >
            <div className="page-card-header">
              <div className="card-icon" style={{ background: "var(--accent-amber-dim)" }}>
                <Star className="h-[18px] w-[18px]" style={{ color: "var(--accent-amber)" }} />
              </div>
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

        {improvementPlan?.actions?.length > 0 && (
          <FadeIn delay={0.3}>
            <div className="page-card p-6" data-testid="card-orbit-improvement-plan">
              <div className="page-card-header">
                <div className="card-icon" style={{ background: "var(--accent-emerald-dim)" }}>
                  <TrendingUp className="h-[18px] w-[18px]" style={{ color: "var(--accent-emerald)" }} />
                </div>
                <span className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>How To Improve Orbit Score</span>
              </div>
              <div className="flex flex-wrap gap-2 mb-4">
                <Badge variant="outline">Current: {improvementPlan.current_score}</Badge>
                <Badge variant="outline">Projected 30d: {improvementPlan.projected_score_30d}</Badge>
                <Badge variant="outline">Adherence: {Math.round((improvementPlan.adherence?.adherence_rate || 0) * 100)}%</Badge>
              </div>
              <div className="space-y-3">
                {improvementPlan.actions.slice(0, 4).map((action: any, i: number) => (
                  <div key={i} className="p-3 rounded-xl" style={{ border: "1px solid var(--border-subtle)", background: "var(--bg-elevated)" }} data-testid={`card-improvement-action-${i}`}>
                    <div className="flex items-center justify-between gap-2">
                      <p className="font-medium" style={{ color: "var(--text-primary)" }}>{action.focus}</p>
                      <Badge variant="outline">+{action.expected_impact}</Badge>
                    </div>
                    <p className="text-sm mt-1" style={{ color: "var(--text-secondary)" }}>{action.action}</p>
                    <p className="text-xs mt-1" style={{ color: "var(--text-muted)" }}>{action.why}</p>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="mt-2 px-0 text-xs"
                      style={{ color: "var(--accent-cyan)" }}
                      onClick={() => setSelectedAction(action)}
                      data-testid={`button-improvement-detail-${i}`}
                    >
                      View details
                    </Button>
                  </div>
                ))}
              </div>
            </div>
          </FadeIn>
        )}


        <Dialog open={!!selectedAction} onOpenChange={(open) => !open && setSelectedAction(null)}>
          <DialogContent style={{ background: "var(--bg-elevated)", border: "1px solid var(--border-default)" }}>
            <DialogHeader>
              <DialogTitle style={{ color: "var(--text-primary)" }}>
                {selectedAction?.focus || "Orbit Improvement"}
              </DialogTitle>
            </DialogHeader>
            {selectedAction && (
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <Badge variant="outline">Expected impact: +{selectedAction.expected_impact}</Badge>
                </div>
                <div>
                  <p className="text-xs uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>Suggested action</p>
                  <p className="text-sm mt-1" style={{ color: "var(--text-primary)" }}>{selectedAction.action}</p>
                </div>
                <div>
                  <p className="text-xs uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>Why this matters</p>
                  <p className="text-sm mt-1" style={{ color: "var(--text-secondary)" }}>{selectedAction.why}</p>
                </div>
                <div className="flex justify-end">
                  <span className="text-xs font-medium" style={{ color: "var(--accent-amber)" }} data-testid="text-upgrade-note">
                    + please upgrade subscription for better insights
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
