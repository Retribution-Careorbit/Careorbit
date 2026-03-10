import { useQuery } from "@tanstack/react-query";
import { Link } from "wouter";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Layout } from "@/components/layout";
import { useAuthStore } from "@/lib/auth";
import { StaggerContainer, StaggerItem, FadeIn, CountUp } from "@/components/animations";
import { OrbitScoreRadial, HealthMetricsChart } from "@/components/charts";
import { Pill, FileText, Bell, Activity, Shield, Heart, AlertCircle, ArrowRight, Calendar, Clock, TrendingUp, ChevronRight } from "lucide-react";

function getGreeting() {
  const h = new Date().getHours();
  if (h < 12) return "Good morning";
  if (h < 17) return "Good afternoon";
  return "Good evening";
}

function formatDate() {
  return new Date().toLocaleDateString("en-IN", {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

const STAT_CONFIGS = [
  { title: "Health Records", icon: Activity, accent: "cyan" as const },
  { title: "Medications", icon: Pill, accent: "violet" as const },
  { title: "Reminders", icon: Bell, accent: "amber" as const },
  { title: "Subscription", icon: Shield, accent: "emerald" as const },
];

const ACCENT_COLORS: Record<string, string> = {
  cyan: "var(--accent-cyan)",
  violet: "var(--accent-violet)",
  amber: "var(--accent-amber)",
  emerald: "var(--accent-emerald)",
};

function StatCard({
  title,
  icon: Icon,
  accent,
  value,
  description,
  isNumeric,
  loading,
  isSubscription,
}: {
  title: string;
  icon: any;
  accent: string;
  value: number | string;
  description: string;
  isNumeric: boolean;
  loading: boolean;
  isSubscription?: boolean;
}) {
  const color = ACCENT_COLORS[accent];

  return (
    <div className="stat-card" data-accent={accent} data-testid={`card-stat-${title.toLowerCase().replace(/\s/g, "-")}`}>
      <div className="flex items-center justify-between mb-4">
        <div
          className="w-8 h-8 rounded-lg flex items-center justify-center"
          style={{ background: `color-mix(in srgb, ${color} 12%, transparent)` }}
        >
          <Icon className="h-5 w-5" style={{ color }} />
        </div>
        <span className="text-xs font-medium uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>
          {title}
        </span>
      </div>

      {loading ? (
        <Skeleton className="h-10 w-24" />
      ) : (
        <>
          <div className="flex items-end justify-between">
            <span
              className="font-mono text-4xl font-bold leading-none"
              style={{ color: (isNumeric && value === 0) ? "var(--text-muted)" : "var(--text-primary)" }}
              data-testid={`text-stat-${title.toLowerCase().replace(/\s/g, "-")}`}
            >
              {isSubscription ? (
                <span style={{ color: "var(--accent-emerald)" }}>
                  {String(value).toUpperCase()}
                </span>
              ) : isNumeric ? (
                <CountUp end={value as number} />
              ) : (
                <span className="capitalize">{String(value).replace("_", " ")}</span>
              )}
            </span>
          </div>
          <p className="text-xs mt-2" style={{ color: "var(--text-muted)" }}>
            {description}
          </p>
          {isSubscription && String(value).toLowerCase() === "free" && (
            <Link href="/settings">
              <button
                className="mt-3 px-3 py-1 rounded-md text-[10px] font-medium text-white"
                style={{ background: "var(--accent-violet)", borderRadius: 6 }}
                data-testid="button-upgrade"
              >
                UPGRADE
              </button>
            </Link>
          )}
        </>
      )}
    </div>
  );
}

export default function DashboardPage() {
  const user = useAuthStore((s) => s.user);

  const { data: overview, isLoading: overviewLoading } = useQuery<any>({
    queryKey: ["/api/patients/overview"],
  });

  const { data: subscription, isLoading: subLoading } = useQuery<any>({
    queryKey: ["/api/subscriptions/current"],
  });

  const { data: reminders = [], isLoading: remLoading } = useQuery<any[]>({
    queryKey: ["/api/reminders/list"],
  });

  const { data: orbitScore } = useQuery<any>({
    queryKey: ["/api/orbit/score"],
  });

  const { data: vitalsData } = useQuery<any>({
    queryKey: ["/api/patients/vitals"],
  });

  const { data: appointments = [] } = useQuery<any[]>({
    queryKey: ["/api/orbit/appointments"],
  });

  const loading = overviewLoading || subLoading || remLoading;
  const totalNodes = overview?.summary?.total_nodes || 0;
  const reminderList = Array.isArray(reminders) ? reminders : [];

  const statValues = [
    { ...STAT_CONFIGS[0], value: totalNodes, description: "Total nodes in your health graph", isNumeric: true },
    { ...STAT_CONFIGS[1], value: overview?.medications?.length || 0, description: "Active medications tracked", isNumeric: true },
    { ...STAT_CONFIGS[2], value: reminderList.length, description: "Active medication reminders", isNumeric: true },
    { ...STAT_CONFIGS[3], value: subscription?.tier || "free", description: subscription?.features?.shows_ads ? "With ads" : "Ad-free", isNumeric: false, isSubscription: true },
  ];

  const vitals = vitalsData?.vitals || [];
  const bpChartData = vitals
    .filter((v: any) => v.type === "blood_pressure")
    .map((v: any) => ({
      date: new Date(v.date).toLocaleDateString("en-IN", { month: "short", day: "numeric" }),
      value: v.heart_rate,
    }));

  const upcomingAppts = Array.isArray(appointments) ? appointments.filter((a: any) => a.status === "upcoming").slice(0, 2) : [];

  const recentEvents = [
    ...(overview?.medications || []).slice(0, 2).map((m: any) => ({
      label: `${m.name} tracked`,
      icon: Pill,
      color: "var(--accent-violet)",
    })),
    ...(overview?.interactions || []).slice(0, 1).map((ix: any) => ({
      label: `Interaction: ${ix.drug_pair}`,
      icon: AlertCircle,
      color: "var(--accent-rose)",
    })),
  ];

  const firstName = user?.name?.split(" ")[0] || "";

  return (
    <Layout>
      <div className="space-y-6">
        <FadeIn>
          <div className="flex items-start justify-between">
            <div>
              <h1
                className="text-[32px] font-semibold leading-tight"
                style={{ color: "var(--text-primary)" }}
                data-testid="text-dashboard-title"
              >
                {getGreeting()}{firstName ? `, ${firstName}` : ""}
              </h1>
              <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
                Your healthcare overview at a glance
              </p>
            </div>
            <span className="font-mono text-xs hidden md:block" style={{ color: "var(--text-muted)" }}>
              {formatDate()}
            </span>
          </div>
          <div className="mt-6 mb-2" style={{ borderBottom: "1px solid var(--border-subtle)" }} />
        </FadeIn>

        {user?.onboardingComplete === false && (
          <FadeIn delay={0.1}>
            <div
              className="flex items-center gap-3 p-4 rounded-xl"
              style={{ background: "var(--bg-card)", border: "1px solid var(--border-subtle)" }}
            >
              <div className="w-10 h-10 rounded-full flex items-center justify-center shrink-0" style={{ background: "var(--accent-cyan-dim)" }}>
                <AlertCircle className="h-5 w-5" style={{ color: "var(--accent-cyan)" }} />
              </div>
              <div className="flex-1">
                <p className="font-medium text-sm" style={{ color: "var(--text-primary)" }} data-testid="text-onboarding-banner">
                  Complete your profile for personalized health reports
                </p>
                <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
                  Your age, gender, and language preferences help us tailor health insights to you.
                </p>
              </div>
              <Link href="/onboarding">
                <Button size="sm" data-testid="link-complete-profile">
                  Complete Profile
                  <ArrowRight className="h-3.5 w-3.5 ml-1.5" />
                </Button>
              </Link>
            </div>
          </FadeIn>
        )}

        <StaggerContainer className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          {statValues.map((stat) => (
            <StaggerItem key={stat.title}>
              <StatCard {...stat} loading={loading} />
            </StaggerItem>
          ))}
        </StaggerContainer>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
          {orbitScore && (
            <FadeIn delay={0.1}>
              <div
                className="rounded-xl p-6"
                style={{ background: "var(--bg-card)", border: "1px solid var(--border-subtle)" }}
                data-testid="card-orbit-mini"
              >
                <div className="flex items-center gap-2 mb-4">
                  <TrendingUp className="h-5 w-5" style={{ color: "var(--accent-cyan)" }} />
                  <span className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>Orbit Score</span>
                </div>
                <div className="flex flex-col items-center">
                  <OrbitScoreRadial score={orbitScore.total_score || 0} size={160} />
                  <Link href="/orbit-score">
                    <Button variant="ghost" size="sm" className="mt-3 text-xs" style={{ color: "var(--accent-cyan)" }} data-testid="link-view-orbit">
                      View Details
                      <ArrowRight className="h-3 w-3 ml-1" />
                    </Button>
                  </Link>
                </div>
              </div>
            </FadeIn>
          )}

          {bpChartData.length > 0 && (
            <FadeIn delay={0.15} className="lg:col-span-2">
              <div
                className="rounded-xl p-6"
                style={{ background: "var(--bg-card)", border: "1px solid var(--border-subtle)" }}
                data-testid="card-vitals-chart"
              >
                <div className="flex items-center gap-2 mb-4">
                  <Heart className="h-5 w-5" style={{ color: "var(--accent-cyan)" }} />
                  <span className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>Heart Rate Trend</span>
                </div>
                <HealthMetricsChart data={bpChartData} label="Heart Rate" color="#00D4FF" height={200} />
              </div>
            </FadeIn>
          )}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-[1fr_1.2fr_1fr] gap-5">
          <FadeIn delay={0.1}>
            <div
              className="rounded-xl p-6 min-h-[280px]"
              style={{ background: "var(--bg-card)", border: "1px solid var(--border-subtle)" }}
            >
              <div className="flex items-center gap-2 mb-4">
                <Heart className="h-5 w-5" style={{ color: "var(--accent-cyan)" }} />
                <span className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>Quick Actions</span>
              </div>
              <div style={{ borderTop: "1px solid var(--border-subtle)" }}>
                <Link href="/documents" data-testid="link-quick-upload">
                  <div
                    className="flex items-center gap-3 h-14 px-3 cursor-pointer group"
                    style={{ borderBottom: "1px solid var(--border-subtle)" }}
                  >
                    <div
                      className="w-9 h-9 rounded-lg flex items-center justify-center shrink-0"
                      style={{ background: "var(--accent-cyan-dim)" }}
                    >
                      <FileText className="h-[18px] w-[18px]" style={{ color: "var(--accent-cyan)" }} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>Upload Document</p>
                      <p className="text-xs" style={{ color: "var(--text-muted)" }}>Prescription, lab, medicine strip</p>
                    </div>
                    <ChevronRight className="h-3.5 w-3.5 shrink-0 group-hover:translate-x-1 transition-transform" style={{ color: "var(--text-muted)" }} />
                  </div>
                </Link>
                <Link href="/chat" data-testid="link-quick-chat">
                  <div className="flex items-center gap-3 h-14 px-3 cursor-pointer group">
                    <div
                      className="w-9 h-9 rounded-lg flex items-center justify-center shrink-0"
                      style={{ background: "var(--accent-violet-dim)" }}
                    >
                      <Activity className="h-[18px] w-[18px]" style={{ color: "var(--accent-violet)" }} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>Ask AI Assistant</p>
                      <p className="text-xs" style={{ color: "var(--text-muted)" }}>Health insights in Hindi or English</p>
                    </div>
                    <ChevronRight className="h-3.5 w-3.5 shrink-0 group-hover:translate-x-1 transition-transform" style={{ color: "var(--text-muted)" }} />
                  </div>
                </Link>
              </div>
            </div>
          </FadeIn>

          <FadeIn delay={0.15}>
            <div
              className="rounded-xl p-6 min-h-[280px]"
              style={{ background: "var(--bg-card)", border: "1px solid var(--border-subtle)" }}
            >
              <div className="flex items-center gap-2 mb-4">
                <Bell className="h-5 w-5" style={{ color: "var(--accent-amber)" }} />
                <span className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>Upcoming Reminders</span>
              </div>
              {loading ? (
                <div className="space-y-3">
                  <Skeleton className="h-12 w-full rounded-lg" />
                  <Skeleton className="h-12 w-full rounded-lg" />
                </div>
              ) : reminderList.length === 0 ? (
                <div className="text-center py-8">
                  <Bell className="h-12 w-12 mx-auto mb-3" strokeWidth={1} style={{ color: "var(--text-muted)" }} />
                  <p className="text-sm" style={{ color: "var(--text-secondary)" }} data-testid="text-no-reminders">
                    No reminders set
                  </p>
                  <Link href="/reminders">
                    <span className="text-xs underline cursor-pointer" style={{ color: "var(--accent-cyan)" }}>Create a reminder</span>
                  </Link>
                </div>
              ) : (
                <div className="space-y-2">
                  {reminderList.slice(0, 3).map((r: any, i: number) => (
                    <div
                      key={i}
                      className="flex items-center justify-between p-3 rounded-lg"
                      style={{ border: "1px solid var(--border-subtle)" }}
                    >
                      <span className="text-sm font-medium" style={{ color: "var(--text-primary)" }} data-testid={`text-reminder-${i}`}>
                        {r.medication_node_id || "Medication"}
                      </span>
                      <Badge variant="outline" className="text-xs font-mono">{r.reminder_time || "N/A"}</Badge>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </FadeIn>

          <FadeIn delay={0.2}>
            <div
              className="rounded-xl p-6 min-h-[280px]"
              style={{ background: "var(--bg-card)", border: "1px solid var(--border-subtle)" }}
            >
              <div className="flex items-center gap-2 mb-4">
                <Calendar className="h-5 w-5" style={{ color: "var(--accent-emerald)" }} />
                <span className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>Appointments</span>
              </div>
              {upcomingAppts.length === 0 ? (
                <div className="text-center py-8">
                  <Calendar className="h-12 w-12 mx-auto mb-3" strokeWidth={1} style={{ color: "var(--text-muted)" }} />
                  <p className="text-sm" style={{ color: "var(--text-secondary)" }} data-testid="text-no-appointments">
                    No upcoming appointments
                  </p>
                  <Link href="/appointments">
                    <span className="text-xs underline cursor-pointer" style={{ color: "var(--accent-cyan)" }}>Book one</span>
                  </Link>
                </div>
              ) : (
                <div className="space-y-2">
                  {upcomingAppts.map((appt: any, i: number) => (
                    <div
                      key={i}
                      className="p-3 rounded-lg"
                      style={{ border: "1px solid var(--border-subtle)" }}
                    >
                      <p className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>{appt.doctor_name}</p>
                      <div className="flex items-center gap-1 mt-1 text-xs" style={{ color: "var(--text-muted)" }}>
                        <Clock className="h-3 w-3" />
                        {new Date(appt.appointment_datetime).toLocaleDateString("en-IN", { month: "short", day: "numeric" })}
                      </div>
                    </div>
                  ))}
                  <Link href="/appointments">
                    <Button variant="ghost" size="sm" className="w-full mt-1 text-xs" style={{ color: "var(--accent-cyan)" }} data-testid="link-view-appointments">
                      View All <ArrowRight className="h-3 w-3 ml-1" />
                    </Button>
                  </Link>
                </div>
              )}
            </div>
          </FadeIn>
        </div>

        {recentEvents.length > 0 && (
          <FadeIn delay={0.25}>
            <div
              className="rounded-xl p-6"
              style={{ background: "var(--bg-card)", border: "1px solid var(--border-subtle)" }}
              data-testid="card-activity-timeline"
            >
              <div className="flex items-center gap-2 mb-4">
                <Activity className="h-5 w-5" style={{ color: "var(--accent-cyan)" }} />
                <span className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>Recent Activity</span>
              </div>
              <div className="space-y-3">
                {recentEvents.map((event, i) => (
                  <div key={i} className="flex items-center gap-3 p-2">
                    <div className="w-2 h-2 rounded-full shrink-0" style={{ background: "var(--accent-cyan)" }} />
                    <event.icon className="h-4 w-4 shrink-0" style={{ color: event.color }} />
                    <span className="text-sm" style={{ color: "var(--text-primary)" }}>{event.label}</span>
                  </div>
                ))}
              </div>
            </div>
          </FadeIn>
        )}
      </div>
    </Layout>
  );
}
