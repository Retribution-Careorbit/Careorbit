import { useQuery, useMutation } from "@tanstack/react-query";
import { queryClient, apiRequest } from "@/lib/queryClient";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Layout } from "@/components/layout";
import { useToast } from "@/hooks/use-toast";
import { useAuthStore } from "@/lib/auth";
import { useActivePatientStore } from "@/lib/patient-context";
import { useTheme } from "@/components/theme-provider";
import { FadeIn, StaggerContainer, StaggerItem } from "@/components/animations";
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
  const members = useActivePatientStore((s) => s.members);
  const activePatientId = useActivePatientStore((s) => s.activePatientId);
  const logout = useAuthStore((s) => s.logout);
  const { theme, toggleTheme } = useTheme();
  const activeMemberName = members.find((m) => m.id === activePatientId)?.name || user?.name;
  const { data: profileData } = useQuery<any>({
    queryKey: ["/api/patients/profile", activePatientId],
    enabled: Boolean(activePatientId),
  });
  const isHindi = String(profileData?.profile?.preferred_language || user?.preferredLanguage || "en").toLowerCase() === "hi";
  const tx = (en: string, hi: string) => (isHindi ? hi : en);

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
      toast({ title: tx("Plan Updated", "प्लान अपडेट हुआ") });
    },
    onError: (err: Error) => {
      toast({ title: tx("Error", "त्रुटि"), description: err.message, variant: "destructive" });
    },
  });

  const formatPrice = (cents: number) => {
    if (cents === 0) return tx("Free", "मुफ़्त");
    return `₹${(cents / 100).toFixed(0)}/mo`;
  };

  return (
    <Layout>
      <div className="space-y-6 max-w-3xl">
        <FadeIn>
          <div className="page-title-bar">
            <div>
              <h1 data-testid="text-settings-title">
                {tx("Settings", "सेटिंग्स")}
              </h1>
              <p>
                {tx("Manage your account and subscription", "अपना खाता और सब्सक्रिप्शन प्रबंधित करें")}
              </p>
            </div>
          </div>
        </FadeIn>

        <FadeIn delay={0.1}>
          <div className="page-card p-6">
            <div className="page-card-header">
              <div className="card-icon" style={{ background: "var(--accent-cyan-dim)" }}>
                <User className="h-[18px] w-[18px]" style={{ color: "var(--accent-cyan)" }} />
              </div>
              <span className="font-medium" style={{ color: "var(--text-primary)" }}>{tx("Profile", "प्रोफ़ाइल")}</span>
            </div>
            <div className="space-y-0">
              <div className="flex items-center justify-between h-[52px]" style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                <span className="text-sm" style={{ color: "var(--text-muted)" }}>{tx("Email", "ईमेल")}</span>
                <span className="text-sm font-medium" style={{ color: "var(--text-primary)" }} data-testid="text-profile-email">
                  {user?.email || tx("N/A", "उपलब्ध नहीं")}
                </span>
              </div>
              {activeMemberName && (
                <div className="flex items-center justify-between h-[52px]" style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                  <span className="text-sm" style={{ color: "var(--text-muted)" }}>{tx("Name", "नाम")}</span>
                  <span className="text-sm font-medium" style={{ color: "var(--text-primary)" }} data-testid="text-profile-name">
                    {activeMemberName}
                  </span>
                </div>
              )}
              <div className="flex items-center justify-between h-[52px]">
                <span className="text-sm" style={{ color: "var(--text-muted)" }}>{tx("Theme", "थीम")}</span>
                <Button variant="outline" size="sm" onClick={toggleTheme} data-testid="button-theme">
                  {theme === "dark" ? <Sun className="h-4 w-4 mr-2" /> : <Moon className="h-4 w-4 mr-2" />}
                  {theme === "dark" ? tx("Light Mode", "लाइट मोड") : tx("Dark Mode", "डार्क मोड")}
                </Button>
              </div>
            </div>
          </div>
        </FadeIn>

        <FadeIn delay={0.2}>
          <div className="page-card p-6">
            <div className="page-card-header">
              <div className="card-icon" style={{ background: "var(--accent-violet-dim)" }}>
                <Shield className="h-[18px] w-[18px]" style={{ color: "var(--accent-violet)" }} />
              </div>
              <span className="font-medium" style={{ color: "var(--text-primary)" }}>{tx("Subscription", "सब्सक्रिप्शन")}</span>
            </div>
            <p className="text-sm mb-6" style={{ color: "var(--text-muted)" }}>
              {tx("Current plan", "वर्तमान प्लान")}: <Badge className="ml-1" data-testid="text-current-tier">{subscription?.tier || "free"}</Badge>
              {subscription?.features?.shows_ads && (
                <span className="text-xs ml-2">{tx("(with ads)", "(विज्ञापनों के साथ)")}</span>
              )}
            </p>

            <StaggerContainer className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {plans.map((plan) => {
                const isCurrent = subscription?.tier === plan.tier;
                const isPremium = plan.tier.includes("premium");
                return (
                  <StaggerItem key={plan.tier} className="h-full">
                    <div
                      className="rounded-xl p-5 pt-7 text-center relative overflow-hidden flex flex-col h-full"
                      style={{
                        background: isPremium
                          ? "linear-gradient(180deg, color-mix(in srgb, var(--accent-amber) 5%, var(--bg-elevated)), var(--bg-elevated))"
                          : "var(--bg-elevated)",
                        border: isCurrent
                          ? "1px solid var(--accent-cyan)"
                          : "1px solid var(--border-subtle)",
                        boxShadow: isCurrent ? "var(--glow-cyan)" : undefined,
                      }}
                      data-testid={`card-plan-${plan.tier}`}
                    >
                      {isCurrent && (
                        <Badge className="absolute -top-0 left-4 rounded-t-none">{tx("Current", "वर्तमान")}</Badge>
                      )}
                      <div
                        className="w-12 h-12 rounded-full mx-auto flex items-center justify-center mb-3"
                        style={{
                          background: isPremium ? "var(--accent-amber-dim)" : "var(--bg-hover)",
                        }}
                      >
                        <Crown className="h-6 w-6" style={{ color: isPremium ? "var(--accent-amber)" : "var(--text-muted)" }} />
                      </div>
                      <p className="font-bold capitalize" style={{ color: "var(--text-primary)" }}>{plan.tier.replace("_", " ")}</p>
                      <p className="text-2xl font-mono font-bold mt-1" style={{ color: "var(--text-primary)" }}>{formatPrice(plan.price_monthly_cents)}</p>
                      <div className="mt-auto pt-4">
                        {isCurrent ? (
                          <Button variant="outline" disabled className="w-full">
                            <Check className="h-4 w-4 mr-2" />
                            {tx("Current Plan", "वर्तमान प्लान")}
                          </Button>
                        ) : (
                          <Button
                            className="w-full"
                            onClick={() => upgradeMutation.mutate(plan.tier)}
                            disabled={upgradeMutation.isPending}
                            data-testid={`button-upgrade-${plan.tier}`}
                          >
                            {upgradeMutation.isPending ? tx("Upgrading...", "अपग्रेड हो रहा है...") : tx("Upgrade", "अपग्रेड करें")}
                          </Button>
                        )}
                      </div>
                    </div>
                  </StaggerItem>
                );
              })}
            </StaggerContainer>
          </div>
        </FadeIn>

        <FadeIn delay={0.3}>
          <div className="page-card p-4">
            <Button
              variant="ghost"
              onClick={logout}
              className="w-full text-destructive hover:text-destructive hover:bg-destructive/10"
              data-testid="button-sign-out"
            >
              <LogOut className="h-4 w-4 mr-2" />
              {tx("Sign Out", "साइन आउट")}
            </Button>
          </div>
        </FadeIn>
      </div>
    </Layout>
  );
}
