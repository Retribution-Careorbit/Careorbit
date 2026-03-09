import { useQuery } from "@tanstack/react-query";
import { Link } from "wouter";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Layout } from "@/components/layout";
import { useAuthStore } from "@/lib/auth";
import { StaggerContainer, StaggerItem, FadeIn, CountUp, HoverCard } from "@/components/animations";
import { OrbitScoreRadial, HealthMetricsChart } from "@/components/charts";
import { Pill, FileText, Bell, Activity, Shield, Heart, AlertCircle, ArrowRight, Calendar, Clock, TrendingUp } from "lucide-react";

function getGreeting() {
  const h = new Date().getHours();
  if (h < 12) return "Good morning";
  if (h < 17) return "Good afternoon";
  return "Good evening";
}

const STAT_CONFIGS = [
  {
    title: "Health Records",
    icon: Activity,
    gradient: "from-cyan-500/10 to-cyan-600/5",
    iconBg: "bg-cyan-500/10 text-cyan-500",
    borderAccent: "border-l-cyan-500",
  },
  {
    title: "Medications",
    icon: Pill,
    gradient: "from-purple-500/10 to-purple-600/5",
    iconBg: "bg-purple-500/10 text-purple-500",
    borderAccent: "border-l-purple-500",
  },
  {
    title: "Reminders",
    icon: Bell,
    gradient: "from-amber-500/10 to-amber-600/5",
    iconBg: "bg-amber-500/10 text-amber-500",
    borderAccent: "border-l-amber-500",
  },
  {
    title: "Subscription",
    icon: Shield,
    gradient: "from-green-500/10 to-green-600/5",
    iconBg: "bg-green-500/10 text-green-500",
    borderAccent: "border-l-green-500",
  },
];

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
    { ...STAT_CONFIGS[3], value: subscription?.tier || "free", description: subscription?.features?.shows_ads ? "With ads" : "Ad-free", isNumeric: false },
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
      color: "text-purple-400",
    })),
    ...(overview?.interactions || []).slice(0, 1).map((ix: any) => ({
      label: `Interaction: ${ix.drug_pair}`,
      icon: AlertCircle,
      color: "text-red-400",
    })),
  ];

  return (
    <Layout>
      <div className="space-y-8">
        <FadeIn>
          <div>
            <h1 className="text-3xl font-heading font-bold tracking-tight" data-testid="text-dashboard-title">
              {getGreeting()}{user?.name ? `, ${user.name}` : ""}
            </h1>
            <p className="text-muted-foreground mt-1.5 text-base">
              Your healthcare overview at a glance
            </p>
          </div>
        </FadeIn>

        {user?.onboardingComplete === false && (
          <FadeIn delay={0.1}>
            <Card className="border-primary/30 bg-gradient-to-r from-primary/5 to-transparent overflow-hidden">
              <CardContent className="p-4 flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                  <AlertCircle className="h-5 w-5 text-primary" />
                </div>
                <div className="flex-1">
                  <p className="font-medium" data-testid="text-onboarding-banner">
                    Complete your profile for personalized health reports
                  </p>
                  <p className="text-sm text-muted-foreground">
                    Your age, gender, and language preferences help us tailor health insights to you.
                  </p>
                </div>
                <Link href="/onboarding">
                  <Button size="sm" className="shadow-sm" data-testid="link-complete-profile">
                    Complete Profile
                    <ArrowRight className="h-3.5 w-3.5 ml-1.5" />
                  </Button>
                </Link>
              </CardContent>
            </Card>
          </FadeIn>
        )}

        <StaggerContainer className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {statValues.map((stat) => (
            <StaggerItem key={stat.title}>
              <HoverCard>
                <Card className={`glass border-l-4 ${stat.borderAccent} overflow-hidden`}>
                  <div className={`absolute inset-0 bg-gradient-to-br ${stat.gradient} pointer-events-none`} />
                  <CardHeader className="flex flex-row items-center justify-between pb-2 relative">
                    <CardTitle className="text-sm font-medium text-muted-foreground">{stat.title}</CardTitle>
                    <div className={`w-9 h-9 rounded-lg flex items-center justify-center ${stat.iconBg}`}>
                      <stat.icon className="h-[18px] w-[18px]" />
                    </div>
                  </CardHeader>
                  <CardContent className="relative">
                    {loading ? (
                      <Skeleton className="h-8 w-20" />
                    ) : (
                      <>
                        <div className="text-2xl font-bold font-heading" data-testid={`text-stat-${stat.title.toLowerCase().replace(/\s/g, "-")}`}>
                          {stat.isNumeric ? (
                            <CountUp end={stat.value as number} />
                          ) : (
                            <span className="capitalize">{String(stat.value).replace("_", " ")}</span>
                          )}
                        </div>
                        <p className="text-xs text-muted-foreground mt-1">
                          {stat.description}
                        </p>
                      </>
                    )}
                  </CardContent>
                </Card>
              </HoverCard>
            </StaggerItem>
          ))}
        </StaggerContainer>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {orbitScore && (
            <FadeIn delay={0.1}>
              <Card className="glass" data-testid="card-orbit-mini">
                <CardHeader className="pb-2">
                  <CardTitle className="flex items-center gap-2 font-heading text-base">
                    <TrendingUp className="h-5 w-5 text-primary" />
                    Orbit Score
                  </CardTitle>
                </CardHeader>
                <CardContent className="flex flex-col items-center pb-4">
                  <OrbitScoreRadial score={orbitScore.total_score || 0} size={160} />
                  <Link href="/orbit-score">
                    <Button variant="ghost" size="sm" className="mt-2 text-xs" data-testid="link-view-orbit">
                      View Details
                      <ArrowRight className="h-3 w-3 ml-1" />
                    </Button>
                  </Link>
                </CardContent>
              </Card>
            </FadeIn>
          )}

          {bpChartData.length > 0 && (
            <FadeIn delay={0.15} className="lg:col-span-2">
              <Card className="glass" data-testid="card-vitals-chart">
                <CardHeader className="pb-2">
                  <CardTitle className="flex items-center gap-2 font-heading text-base">
                    <Heart className="h-5 w-5 text-cyan-400" />
                    Heart Rate Trend
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <HealthMetricsChart data={bpChartData} label="Heart Rate" color="#00d9ff" height={200} />
                </CardContent>
              </Card>
            </FadeIn>
          )}
        </div>

        <StaggerContainer className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <StaggerItem>
            <Card className="glass">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 font-heading text-base">
                  <Heart className="h-5 w-5 text-primary" />
                  Quick Actions
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <Link href="/documents" data-testid="link-quick-upload">
                  <div className="flex items-center gap-3 p-3.5 rounded-lg border border-border/50 hover:border-primary/30 hover:bg-primary/5 transition-all duration-200 cursor-pointer group">
                    <div className="w-10 h-10 rounded-lg bg-cyan-500/10 flex items-center justify-center shrink-0 group-hover:bg-cyan-500/20 transition-colors">
                      <FileText className="h-5 w-5 text-cyan-500" />
                    </div>
                    <div className="flex-1">
                      <p className="font-medium text-sm">Upload Document</p>
                      <p className="text-xs text-muted-foreground">Prescription, lab report, or medicine strip</p>
                    </div>
                    <ArrowRight className="h-4 w-4 text-muted-foreground group-hover:text-primary transition-colors" />
                  </div>
                </Link>
                <Link href="/chat" data-testid="link-quick-chat">
                  <div className="flex items-center gap-3 p-3.5 rounded-lg border border-border/50 hover:border-secondary/30 hover:bg-secondary/5 transition-all duration-200 cursor-pointer group mt-3">
                    <div className="w-10 h-10 rounded-lg bg-purple-500/10 flex items-center justify-center shrink-0 group-hover:bg-purple-500/20 transition-colors">
                      <Activity className="h-5 w-5 text-purple-500" />
                    </div>
                    <div className="flex-1">
                      <p className="font-medium text-sm">Ask AI Assistant</p>
                      <p className="text-xs text-muted-foreground">Get health insights in Hindi or English</p>
                    </div>
                    <ArrowRight className="h-4 w-4 text-muted-foreground group-hover:text-secondary transition-colors" />
                  </div>
                </Link>
              </CardContent>
            </Card>
          </StaggerItem>

          <StaggerItem>
            <Card className="glass">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 font-heading text-base">
                  <Bell className="h-5 w-5 text-amber-500" />
                  Upcoming Reminders
                </CardTitle>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <div className="space-y-3">
                    <Skeleton className="h-12 w-full rounded-lg" />
                    <Skeleton className="h-12 w-full rounded-lg" />
                  </div>
                ) : reminderList.length === 0 ? (
                  <div className="text-center py-6">
                    <Bell className="h-8 w-8 text-muted-foreground/40 mx-auto mb-2" />
                    <p className="text-sm text-muted-foreground" data-testid="text-no-reminders">
                      No reminders set. Go to Reminders to create one.
                    </p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {reminderList.slice(0, 3).map((r: any, i: number) => (
                      <div key={i} className="flex items-center justify-between p-3 rounded-lg border border-border/50 hover:bg-accent/50 transition-colors">
                        <span className="text-sm font-medium" data-testid={`text-reminder-${i}`}>
                          {r.medication_node_id || "Medication"}
                        </span>
                        <Badge variant="outline" className="text-xs">{r.reminder_time || "N/A"}</Badge>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </StaggerItem>

          <StaggerItem>
            <Card className="glass">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 font-heading text-base">
                  <Calendar className="h-5 w-5 text-green-500" />
                  Appointments
                </CardTitle>
              </CardHeader>
              <CardContent>
                {upcomingAppts.length === 0 ? (
                  <div className="text-center py-6">
                    <Calendar className="h-8 w-8 text-muted-foreground/40 mx-auto mb-2" />
                    <p className="text-sm text-muted-foreground" data-testid="text-no-appointments">
                      No upcoming appointments
                    </p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {upcomingAppts.map((appt: any, i: number) => (
                      <div key={i} className="p-3 rounded-lg border border-border/50 hover:bg-accent/50 transition-colors">
                        <p className="text-sm font-medium">{appt.doctor_name}</p>
                        <div className="flex items-center gap-1 mt-1 text-xs text-muted-foreground">
                          <Clock className="h-3 w-3" />
                          {new Date(appt.appointment_datetime).toLocaleDateString("en-IN", { month: "short", day: "numeric" })}
                        </div>
                      </div>
                    ))}
                    <Link href="/appointments">
                      <Button variant="ghost" size="sm" className="w-full mt-1 text-xs" data-testid="link-view-appointments">
                        View All <ArrowRight className="h-3 w-3 ml-1" />
                      </Button>
                    </Link>
                  </div>
                )}
              </CardContent>
            </Card>
          </StaggerItem>
        </StaggerContainer>

        {recentEvents.length > 0 && (
          <FadeIn delay={0.2}>
            <Card className="glass" data-testid="card-activity-timeline">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 font-heading text-base">
                  <Activity className="h-5 w-5 text-primary" />
                  Recent Activity
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {recentEvents.map((event, i) => (
                    <div key={i} className="flex items-center gap-3 p-2">
                      <div className="w-2 h-2 rounded-full bg-primary shrink-0" />
                      <event.icon className={`h-4 w-4 ${event.color} shrink-0`} />
                      <span className="text-sm">{event.label}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </FadeIn>
        )}
      </div>
    </Layout>
  );
}
