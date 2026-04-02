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

  const startFederatedSignup = (provider: "microsoft" | "google" | "apple") => {
    window.location.assign(`/api/auth/entra/login?provider=${provider}`);
  };

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
      setAuth(data.access_token, data.refresh_token, {
        id: data.user?.id || email,
        email,
        name,
        onboardingComplete: false,
        preferredLanguage: data.user?.preferred_language || "en",
      });
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

                <div className="relative my-6">
                  <div className="absolute inset-0 flex items-center">
                    <div className="w-full border-t" style={{ borderColor: "var(--border-subtle)" }}></div>
                  </div>
                  <div className="relative flex justify-center text-sm">
                    <span className="px-2" style={{ background: "var(--bg-card)", color: "var(--text-muted)" }}>Or sign up with</span>
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <button type="button" onClick={() => startFederatedSignup("microsoft")} className="h-11 rounded-lg border border-[var(--border-default)] flex items-center justify-center gap-2 text-sm font-medium text-[var(--text-primary)] hover:bg-[var(--bg-hover)] transition-colors" data-testid="button-entra-register">
                    <svg className="w-4.5 h-4.5" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                      <rect x="2" y="2" width="9" height="9" fill="currentColor" />
                      <rect x="13" y="2" width="9" height="9" fill="currentColor" opacity="0.8" />
                      <rect x="2" y="13" width="9" height="9" fill="currentColor" opacity="0.7" />
                      <rect x="13" y="13" width="9" height="9" fill="currentColor" opacity="0.6" />
                    </svg>
                    Microsoft
                  </button>
                  <button type="button" onClick={() => startFederatedSignup("google")} className="h-11 rounded-lg border border-[var(--border-default)] flex items-center justify-center gap-2 text-sm font-medium text-[var(--text-primary)] hover:bg-[var(--bg-hover)] transition-colors" data-testid="button-google-register">
                    <svg className="w-4.5 h-4.5" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                      <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                      <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                      <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                      <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
                    </svg>
                    Google
                  </button>
                  <button type="button" onClick={() => startFederatedSignup("apple")} className="h-11 rounded-lg border border-[var(--border-default)] flex items-center justify-center gap-2 text-sm font-medium text-[var(--text-primary)] hover:bg-[var(--bg-hover)] transition-colors" data-testid="button-apple-register">
                    <svg className="w-4.5 h-4.5" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                      <path d="M12.152 6.896c-.948 0-2.415-1.078-3.96-1.04-2.04.027-3.91 1.183-4.961 3.014-2.117 3.675-.546 9.103 1.519 12.09 1.013 1.454 2.208 3.09 3.792 3.039 1.52-.065 2.09-.987 3.935-.987 1.831 0 2.35.987 3.96.948 1.637-.026 2.676-1.48 3.676-2.948 1.156-1.688 1.636-3.325 1.662-3.415-.039-.013-3.182-1.221-3.22-4.857-.026-3.04 2.48-4.494 2.597-4.559-1.43-2.09-3.603-2.324-4.335-2.376-2.053-.169-3.924 1.253-4.665 1.253zM15.504 4.542c.83-1.006 1.385-2.399 1.233-3.793-1.144.047-2.585.761-3.447 1.761-.692.805-1.353 2.227-1.171 3.603 1.28.1 2.553-.665 3.385-1.571z"/>
                    </svg>
                    Apple
                  </button>
                </div>
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
