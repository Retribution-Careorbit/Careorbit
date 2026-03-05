import { useQuery, useMutation } from "@tanstack/react-query";
import { queryClient, apiRequest } from "@/lib/queryClient";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Layout } from "@/components/layout";
import { useToast } from "@/hooks/use-toast";
import { useAuthStore } from "@/lib/auth";
import { useTheme } from "@/components/theme-provider";
import { Shield, Crown, Check, Moon, Sun, User } from "lucide-react";

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
        <div>
          <h1 className="text-3xl font-bold" data-testid="text-settings-title">Settings</h1>
          <p className="text-muted-foreground mt-1">
            Manage your account and subscription
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <User className="h-5 w-5" />
              Profile
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Email</span>
              <span className="text-sm font-medium" data-testid="text-profile-email">
                {user?.email || "N/A"}
              </span>
            </div>
            {user?.name && (
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Name</span>
                <span className="text-sm font-medium" data-testid="text-profile-name">
                  {user.name}
                </span>
              </div>
            )}
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Theme</span>
              <Button
                variant="outline"
                size="sm"
                onClick={toggleTheme}
                data-testid="button-theme"
              >
                {theme === "dark" ? <Sun className="h-4 w-4 mr-2" /> : <Moon className="h-4 w-4 mr-2" />}
                {theme === "dark" ? "Light Mode" : "Dark Mode"}
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="h-5 w-5" />
              Subscription
            </CardTitle>
            <CardDescription>
              Current plan: <Badge data-testid="text-current-tier">{subscription?.tier || "free"}</Badge>
              {subscription?.features?.shows_ads && (
                <span className="text-xs text-muted-foreground ml-2">(with ads)</span>
              )}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {plans.map((plan) => {
                const isCurrent = subscription?.tier === plan.tier;
                return (
                  <Card
                    key={plan.tier}
                    className={`relative ${isCurrent ? "border-primary" : ""}`}
                    data-testid={`card-plan-${plan.tier}`}
                  >
                    {isCurrent && (
                      <Badge className="absolute -top-2 left-4">Current</Badge>
                    )}
                    <CardContent className="p-4 pt-6 text-center space-y-3">
                      <Crown className={`h-8 w-8 mx-auto ${plan.tier.includes("premium") ? "text-chart-3" : "text-muted-foreground"}`} />
                      <p className="font-bold capitalize">{plan.tier.replace("_", " ")}</p>
                      <p className="text-2xl font-bold">{formatPrice(plan.price_monthly_cents)}</p>
                      {isCurrent ? (
                        <Button variant="outline" disabled className="w-full">
                          <Check className="h-4 w-4 mr-2" />
                          Current Plan
                        </Button>
                      ) : (
                        <Button
                          className="w-full"
                          onClick={() => upgradeMutation.mutate(plan.tier)}
                          disabled={upgradeMutation.isPending}
                          data-testid={`button-upgrade-${plan.tier}`}
                        >
                          {upgradeMutation.isPending ? "Upgrading..." : "Upgrade"}
                        </Button>
                      )}
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <Button
              variant="destructive"
              onClick={logout}
              className="w-full"
              data-testid="button-sign-out"
            >
              Sign Out
            </Button>
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
}
