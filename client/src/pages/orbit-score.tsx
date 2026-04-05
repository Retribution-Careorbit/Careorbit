import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Layout } from "@/components/layout";
import { useActivePatientStore } from "@/lib/patient-context";
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
  const activePatientId = useActivePatientStore((s) => s.activePatientId);

  const { data: scoreData, isLoading: scoreLoading } = useQuery<any>({
    queryKey: ["/api/orbit/score", activePatientId],
  });

  const { data: profileData } = useQuery<any>({
    queryKey: ["/api/patients/profile", activePatientId],
  });

  const { data: improvementPlan } = useQuery<any>({
    queryKey: ["/api/orbit/improvement-plan", activePatientId],
  });

  const isHindi = String(profileData?.profile?.preferred_language || "en").toLowerCase() === "hi";
  const t = {
    title: isHindi ? "ऑर्बिट स्कोर" : "Orbit Score",
    subtitle: isHindi ? "आपका समग्र स्वास्थ्य स्कोर और प्रगति" : "Your comprehensive health score and progress",
    healthScore: isHindi ? "स्वास्थ्य स्कोर" : "Health Score",
    outOf100: isHindi ? "100 में से" : "out of 100",
    good: isHindi ? "अच्छा" : "Good",
    improving: isHindi ? "सुधर रहा है" : "Improving",
    needsAttention: isHindi ? "ध्यान आवश्यक" : "Needs Attention",
    goodHint: isHindi ? "बहुत अच्छा! अपने स्वास्थ्य रिकॉर्ड ऐसे ही बनाए रखें।" : "Great job! Keep maintaining your health records.",
    improveHint: isHindi ? "स्कोर सुधारने के लिए और रिकॉर्ड अपलोड करें और देखभाल योजना का पालन करें।" : "Upload more records and follow your care plan to improve.",
    breakdown: isHindi ? "स्कोर विवरण" : "Score Breakdown",
    achievements: isHindi ? "उपलब्धियाँ" : "Achievements",
    improvePlan: isHindi ? "ऑर्बिट स्कोर कैसे सुधारें" : "How To Improve Orbit Score",
    current: isHindi ? "वर्तमान" : "Current",
    projected30d: isHindi ? "30 दिन अनुमान" : "Projected 30d",
    adherence: isHindi ? "अनुपालन" : "Adherence",
    viewDetails: isHindi ? "विवरण देखें" : "View details",
    expectedImpact: isHindi ? "अनुमानित प्रभाव" : "Expected impact",
    suggestedAction: isHindi ? "सुझाई गई कार्रवाई" : "Suggested action",
    whyMatters: isHindi ? "यह क्यों ज़रूरी है" : "Why this matters",
    upgradeNote: isHindi ? "+ बेहतर जानकारी के लिए कृपया सदस्यता अपग्रेड करें" : "+ please upgrade subscription for better insights",
    orbitImprovement: isHindi ? "ऑर्बिट सुधार" : "Orbit Improvement",
  };

  const loading = scoreLoading;
  const score = scoreData?.total_score || 0;
  const breakdown = scoreData?.breakdown;

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
          <div className="page-title-bar">
            <div>
              <h1 data-testid="text-orbit-title">
                {t.title}
              </h1>
              <p>
                {t.subtitle}
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
                <span className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>{t.healthScore}</span>
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
                      <span className="text-xs mt-1" style={{ color: "var(--text-muted)" }}>{t.outOf100}</span>
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
                    {score >= 70 ? t.good : score >= 40 ? t.improving : t.needsAttention}
                  </Badge>
                  <p className="text-xs mt-2 text-center" style={{ color: "var(--text-muted)" }}>
                    {score >= 70
                      ? t.goodHint
                      : t.improveHint}
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
                  <span className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>{t.breakdown}</span>
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
              <span className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>{t.achievements}</span>
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
                <span className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>{t.improvePlan}</span>
              </div>
              <div className="flex flex-wrap gap-2 mb-4">
                <Badge variant="outline">{t.current}: {improvementPlan.current_score}</Badge>
                <Badge variant="outline">{t.projected30d}: {improvementPlan.projected_score_30d}</Badge>
                <Badge variant="outline">{t.adherence}: {Math.round((improvementPlan.adherence?.adherence_rate || 0) * 100)}%</Badge>
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
                      {t.viewDetails}
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
                {selectedAction?.focus || t.orbitImprovement}
              </DialogTitle>
            </DialogHeader>
            {selectedAction && (
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <Badge variant="outline">{t.expectedImpact}: +{selectedAction.expected_impact}</Badge>
                </div>
                <div>
                  <p className="text-xs uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>{t.suggestedAction}</p>
                  <p className="text-sm mt-1" style={{ color: "var(--text-primary)" }}>{selectedAction.action}</p>
                </div>
                <div>
                  <p className="text-xs uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>{t.whyMatters}</p>
                  <p className="text-sm mt-1" style={{ color: "var(--text-secondary)" }}>{selectedAction.why}</p>
                </div>
                <div className="flex justify-end">
                  <span className="text-xs font-medium" style={{ color: "var(--accent-amber)" }} data-testid="text-upgrade-note">
                    {t.upgradeNote}
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
