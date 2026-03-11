import { useState } from "react";
import { useLocation, Link } from "wouter";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";
import { useAuthStore } from "@/lib/auth";
import { FadeIn, ScaleIn } from "@/components/animations";
import { Heart, UserPlus, Shield, Activity, FileText } from "lucide-react";

export default function RegisterPage() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [, navigate] = useLocation();
  const { toast } = useToast();
  const setAuth = useAuthStore((s) => s.setAuth);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password.length < 8) {
      toast({ title: "Weak Password", description: "Password must be at least 8 characters with letters and numbers", variant: "destructive" });
      return;
    }
    setLoading(true);
    try {
      const res = await fetch("/api/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, email, password }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Registration failed");
      setAuth(data.access_token, data.refresh_token, { id: data.user?.id || email, email, name, onboardingComplete: false });
      toast({ title: "Welcome to CareOrbit!", description: "Your account has been created." });
      navigate("/onboarding");
    } catch (err: any) {
      toast({ title: "Registration Failed", description: err.message, variant: "destructive" });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex">
      <div className="hidden lg:flex lg:w-[480px] xl:w-[520px] login-panel flex-col justify-between p-10 relative">
        <div className="login-floating-shape" style={{ width: 300, height: 300, top: '10%', right: '-10%', background: 'var(--accent-violet)' }} />
        <div className="login-floating-shape" style={{ width: 200, height: 200, bottom: '15%', left: '5%', background: 'var(--accent-cyan)', animationDelay: '2s' }} />
        <div className="login-floating-shape" style={{ width: 120, height: 120, top: '50%', left: '40%', background: 'var(--accent-emerald)', animationDelay: '4s' }} />

        <div className="relative z-10">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-11 h-11 rounded-xl flex items-center justify-center" style={{ background: 'var(--accent-cyan)' }}>
              <Heart className="h-6 w-6 text-white" />
            </div>
            <span className="text-2xl font-mono font-bold text-white tracking-tight">CareOrbit</span>
          </div>
          <p className="text-sm mt-1" style={{ color: 'rgba(255,255,255,0.5)' }}>Healthcare AI Platform</p>
        </div>

        <div className="relative z-10 space-y-8">
          <div>
            <h2 className="text-3xl font-semibold text-white leading-tight">
              Start your<br />health journey.
            </h2>
            <p className="text-sm mt-3 leading-relaxed" style={{ color: 'rgba(255,255,255,0.55)' }}>
              Join thousands of patients using AI to manage their healthcare better.
            </p>
          </div>

          <div className="space-y-4">
            {[
              { icon: Shield, label: "Drug interaction alerts", color: "var(--accent-cyan)" },
              { icon: Activity, label: "AI health score tracking", color: "var(--accent-violet)" },
              { icon: FileText, label: "Smart prescription extraction", color: "var(--accent-emerald)" },
            ].map((feature) => (
              <div key={feature.label} className="flex items-center gap-3">
                <div
                  className="w-8 h-8 rounded-lg flex items-center justify-center"
                  style={{ background: `color-mix(in srgb, ${feature.color} 15%, transparent)` }}
                >
                  <feature.icon className="h-4 w-4" style={{ color: feature.color }} />
                </div>
                <span className="text-sm" style={{ color: 'rgba(255,255,255,0.7)' }}>{feature.label}</span>
              </div>
            ))}
          </div>
        </div>

        <p className="relative z-10 text-xs" style={{ color: 'rgba(255,255,255,0.25)' }}>
          Built for Indian patients
        </p>
      </div>

      <div className="flex-1 flex items-center justify-center aurora-bg-strong p-6">
        <ScaleIn>
          <div className="w-full max-w-[420px]">
            <div className="lg:hidden flex items-center justify-center gap-2.5 mb-8">
              <div className="w-11 h-11 rounded-xl flex items-center justify-center shadow-lg" style={{ background: "var(--accent-cyan)" }}>
                <Heart className="h-6 w-6 text-white" />
              </div>
              <span className="text-2xl font-mono font-bold" style={{ color: "var(--text-primary)" }}>CareOrbit</span>
            </div>

            <div
              className="rounded-2xl p-8"
              style={{
                background: "var(--bg-card)",
                border: "1px solid var(--border-subtle)",
                boxShadow: "0 20px 60px rgba(0,0,0,0.12), 0 0 0 1px var(--border-subtle)",
              }}
            >
              <div className="mb-8">
                <FadeIn delay={0.1}>
                  <h1 className="text-2xl font-semibold" style={{ color: "var(--text-primary)" }}>Create account</h1>
                  <p className="text-sm mt-1" style={{ color: "var(--text-secondary)" }}>Get started with your healthcare dashboard</p>
                </FadeIn>
              </div>

              <FadeIn delay={0.2}>
                <form onSubmit={handleSubmit} className="space-y-5">
                  <div className="space-y-2">
                    <Label htmlFor="name" style={{ color: "var(--text-secondary)" }}>Full Name</Label>
                    <Input
                      id="name"
                      data-testid="input-name"
                      placeholder="Your full name"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      className="h-11"
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="email" style={{ color: "var(--text-secondary)" }}>Email</Label>
                    <Input
                      id="email"
                      type="email"
                      data-testid="input-email"
                      placeholder="you@example.com"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className="h-11"
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="password" style={{ color: "var(--text-secondary)" }}>Password</Label>
                    <Input
                      id="password"
                      type="password"
                      data-testid="input-password"
                      placeholder="Min 8 characters, letters + numbers"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className="h-11"
                      required
                    />
                  </div>
                  <Button
                    type="submit"
                    className="w-full h-11 text-sm font-medium"
                    disabled={loading}
                    data-testid="button-register"
                  >
                    <UserPlus className="h-4 w-4 mr-2" />
                    {loading ? "Creating account..." : "Create Account"}
                  </Button>
                </form>
              </FadeIn>
            </div>
            <p className="text-center text-sm mt-6" style={{ color: "var(--text-muted)" }}>
              Already have an account?{" "}
              <Link href="/login" className="font-medium hover:underline" style={{ color: "var(--accent-cyan)" }} data-testid="link-login">
                Sign In
              </Link>
            </p>
          </div>
        </ScaleIn>
      </div>
    </div>
  );
}
