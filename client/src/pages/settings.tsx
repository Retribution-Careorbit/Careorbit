import { useQuery, useMutation } from "@tanstack/react-query";
import { queryClient, apiRequest } from "@/lib/queryClient";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Layout } from "@/components/layout";
import { useToast } from "@/hooks/use-toast";
import { useAuthStore } from "@/lib/auth";
import { useTheme } from "@/components/theme-provider";
import { FadeIn, StaggerContainer, StaggerItem, HoverCard } from "@/components/animations";
import { Shield, Crown, Check, Moon, Sun, User, LogOut } from "lucide-react";

interface Plan {
  tier: string;
  price_monthly_cents: number;
}

interface Subscription {
  tier: string;
  features: { shows_ads: boolean; [key: string]: any };
}

export default function SettingsPage() {
  const { toast } = useToast();
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const { theme, toggleTheme } = useTheme();

  const { data: subscription } = useQuery<Subscription>({
    queryKey: ["/api/subscriptions/current"],
  });

  const { data: plansData } = useQuery<{ plans: Plan[] }>({
    queryKey: ["/api/subscriptions/plans"],
  });

  const plans = plansData?.plans || [];

  const upgradeMutation = useMutation({
    mutationFn: async (tier: string) => {
      const res = await apiRequest("POST", "/api/subscriptions/upgrade", { tier });
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/subscriptions/current"] });
      toast({ title: "Plan Updated" });
    },
    onError: (err: Error) => {
      toast({ title: "Error", description: err.message, variant: "destructive" });
    },
  });

  const formatPrice = (cents: number) => {
    if (cents === 0) return "Free";
    return `₹${(cents / 100).toFixed(0)}/mo`;
  };

  return (
    <Layout>
      <div className="space-y-6 max-w-3xl">
        <FadeIn>
          <div>
            <h1 className="text-3xl font-heading font-bold tracking-tight" data-testid="text-settings-title">Settings</h1>
            <p className="text-muted-foreground mt-1.5">
              Manage your account and subscription
            </p>
          </div>
        </FadeIn>

        <FadeIn delay={0.1}>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 font-heading">
                <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center">
                  <User className="h-4 w-4 text-primary" />
                </div>
                Profile
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between py-2">
                <span className="text-sm text-muted-foreground">Email</span>
                <span className="text-sm font-medium" data-testid="text-profile-email">
                  {user?.email || "N/A"}
                </span>
              </div>
              {user?.name && (
                <div className="flex items-center justify-between py-2 border-t">
                  <span className="text-sm text-muted-foreground">Name</span>
                  <span className="text-sm font-medium" data-testid="text-profile-name">
                    {user.name}
                  </span>
                </div>
              )}
              <div className="flex items-center justify-between py-2 border-t">
                <span className="text-sm text-muted-foreground">Theme</span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={toggleTheme}
                  className="shadow-sm"
                  data-testid="button-theme"
                >
                  {theme === "dark" ? <Sun className="h-4 w-4 mr-2" /> : <Moon className="h-4 w-4 mr-2" />}
                  {theme === "dark" ? "Light Mode" : "Dark Mode"}
                </Button>
              </div>
            </CardContent>
          </Card>
        </FadeIn>

        <FadeIn delay={0.2}>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 font-heading">
                <div className="w-8 h-8 rounded-lg bg-purple-500/10 flex items-center justify-center">
                  <Shield className="h-4 w-4 text-purple-600 dark:text-purple-400" />
                </div>
                Subscription
              </CardTitle>
              <CardDescription>
                Current plan: <Badge className="ml-1" data-testid="text-current-tier">{subscription?.tier || "free"}</Badge>
                {subscription?.features?.shows_ads && (
                  <span className="text-xs text-muted-foreground ml-2">(with ads)</span>
                )}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <StaggerContainer className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {plans.map((plan) => {
                  const isCurrent = subscription?.tier === plan.tier;
                  const isPremium = plan.tier.includes("premium");
                  return (
                    <StaggerItem key={plan.tier}>
                      <HoverCard>
                        <Card
                          className={`relative overflow-hidden ${isCurrent ? "border-primary ring-1 ring-primary/20" : "border-border/50"}`}
                          data-testid={`card-plan-${plan.tier}`}
                        >
                          {isCurrent && (
                            <Badge className="absolute -top-0 left-4 rounded-t-none">Current</Badge>
                          )}
                          <CardContent className="p-5 pt-7 text-center space-y-3">
                            <div className={`w-12 h-12 rounded-full mx-auto flex items-center justify-center ${isPremium ? "bg-amber-500/10" : "bg-muted"}`}>
                              <Crown className={`h-6 w-6 ${isPremium ? "text-amber-500" : "text-muted-foreground"}`} />
                            </div>
                            <p className="font-heading font-bold capitalize">{plan.tier.replace("_", " ")}</p>
                            <p className="text-2xl font-heading font-bold">{formatPrice(plan.price_monthly_cents)}</p>
                            {isCurrent ? (
                              <Button variant="outline" disabled className="w-full">
                                <Check className="h-4 w-4 mr-2" />
                                Current Plan
                              </Button>
                            ) : (
                              <Button
                                className="w-full shadow-sm"
                                onClick={() => upgradeMutation.mutate(plan.tier)}
                                disabled={upgradeMutation.isPending}
                                data-testid={`button-upgrade-${plan.tier}`}
                              >
                                {upgradeMutation.isPending ? "Upgrading..." : "Upgrade"}
                              </Button>
                            )}
                          </CardContent>
                        </Card>
                      </HoverCard>
                    </StaggerItem>
                  );
                })}
              </StaggerContainer>
            </CardContent>
          </Card>
        </FadeIn>

        <FadeIn delay={0.3}>
          <Card className="border-destructive/20">
            <CardContent className="p-4">
              <Button
                variant="ghost"
                onClick={logout}
                className="w-full text-destructive hover:text-destructive hover:bg-destructive/10 transition-colors"
                data-testid="button-sign-out"
              >
                <LogOut className="h-4 w-4 mr-2" />
                Sign Out
              </Button>
            </CardContent>
          </Card>
        </FadeIn>
      </div>
    </Layout>
  );
}
