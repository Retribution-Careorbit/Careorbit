import { useQuery } from "@tanstack/react-query";
import { Link } from "wouter";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Layout } from "@/components/layout";
import { useAuthStore } from "@/lib/auth";
import { Pill, FileText, Bell, Activity, Shield, Heart, AlertCircle } from "lucide-react";

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

  const loading = overviewLoading || subLoading || remLoading;
  const totalNodes = overview?.summary?.total_nodes || 0;
  const reminderList = Array.isArray(reminders) ? reminders : [];

  const stats = [
    {
      title: "Health Records",
      value: totalNodes,
      icon: Activity,
      description: "Total nodes in your health graph",
      color: "text-chart-1",
    },
    {
      title: "Medications",
      value: overview?.medications?.length || 0,
      icon: Pill,
      description: "Active medications tracked",
      color: "text-chart-2",
    },
    {
      title: "Reminders",
      value: reminderList.length,
      icon: Bell,
      description: "Active medication reminders",
      color: "text-chart-3",
    },
    {
      title: "Subscription",
      value: subscription?.tier || "free",
      icon: Shield,
      description: subscription?.features?.shows_ads ? "With ads" : "Ad-free",
      color: "text-chart-4",
    },
  ];

  return (
    <Layout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold" data-testid="text-dashboard-title">
            Welcome back{user?.name ? `, ${user.name}` : ""}
          </h1>
          <p className="text-muted-foreground mt-1">
            Your healthcare overview at a glance
          </p>
        </div>

        {user?.onboardingComplete === false && (
          <Card className="border-primary/50 bg-primary/5">
            <CardContent className="p-4 flex items-center gap-3">
              <AlertCircle className="h-5 w-5 text-primary shrink-0" />
              <div className="flex-1">
                <p className="font-medium" data-testid="text-onboarding-banner">
                  Complete your profile for personalized health reports
                </p>
                <p className="text-sm text-muted-foreground">
                  Your age, gender, and language preferences help us tailor health insights to you.
                </p>
              </div>
              <Link href="/onboarding">
                <Button size="sm" data-testid="link-complete-profile">Complete Profile</Button>
              </Link>
            </CardContent>
          </Card>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {stats.map((stat) => (
            <Card key={stat.title}>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">{stat.title}</CardTitle>
                <stat.icon className={`h-5 w-5 ${stat.color}`} />
              </CardHeader>
              <CardContent>
                {loading ? (
                  <Skeleton className="h-8 w-16" />
                ) : (
                  <>
                    <div className="text-2xl font-bold" data-testid={`text-stat-${stat.title.toLowerCase().replace(/\s/g, "-")}`}>
                      {stat.value}
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">
                      {stat.description}
                    </p>
                  </>
                )}
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Heart className="h-5 w-5 text-primary" />
                Quick Actions
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <Link href="/documents" className="block p-3 rounded-lg border hover:bg-accent transition-colors" data-testid="link-quick-upload">
                <div className="flex items-center gap-3">
                  <FileText className="h-5 w-5 text-chart-1" />
                  <div>
                    <p className="font-medium">Upload Document</p>
                    <p className="text-sm text-muted-foreground">Prescription, lab report, or medicine strip</p>
                  </div>
                </div>
              </Link>
              <Link href="/chat" className="block p-3 rounded-lg border hover:bg-accent transition-colors" data-testid="link-quick-chat">
                <div className="flex items-center gap-3">
                  <Activity className="h-5 w-5 text-chart-2" />
                  <div>
                    <p className="font-medium">Ask AI Assistant</p>
                    <p className="text-sm text-muted-foreground">Get health insights in Hindi or English</p>
                  </div>
                </div>
              </Link>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Bell className="h-5 w-5 text-chart-3" />
                Upcoming Reminders
              </CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="space-y-2">
                  <Skeleton className="h-10 w-full" />
                  <Skeleton className="h-10 w-full" />
                </div>
              ) : reminderList.length === 0 ? (
                <p className="text-sm text-muted-foreground" data-testid="text-no-reminders">
                  No reminders set. Go to Reminders to create one.
                </p>
              ) : (
                <div className="space-y-2">
                  {reminderList.slice(0, 3).map((r: any, i: number) => (
                    <div key={i} className="flex items-center justify-between p-2 rounded border">
                      <span className="text-sm font-medium" data-testid={`text-reminder-${i}`}>
                        {r.medication_node_id || "Medication"}
                      </span>
                      <Badge variant="outline">{r.reminder_time || "N/A"}</Badge>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </Layout>
  );
}
