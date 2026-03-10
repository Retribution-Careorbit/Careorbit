import { useState } from "react";
import { useLocation, Link } from "wouter";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";
import { useAuthStore } from "@/lib/auth";
import { FadeIn, ScaleIn } from "@/components/animations";
import { Heart, LogIn } from "lucide-react";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [, navigate] = useLocation();
  const { toast } = useToast();
  const setAuth = useAuthStore((s) => s.setAuth);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Login failed");
      const onboardingComplete = data.user?.onboarding_complete ?? false;
      setAuth(data.access_token, data.refresh_token, { id: data.user?.id || email, email, name: data.user?.name, onboardingComplete });
      navigate(onboardingComplete ? "/" : "/onboarding");
    } catch (err: any) {
      toast({ title: "Login Failed", description: err.message, variant: "destructive" });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center aurora-bg-strong p-4">
      <ScaleIn>
        <div
          className="w-full max-w-md rounded-xl p-6"
          style={{
            background: "var(--bg-card)",
            border: "1px solid var(--border-subtle)",
            boxShadow: "0 20px 40px rgba(0,0,0,0.2)",
          }}
        >
          <div className="text-center mb-6">
            <FadeIn delay={0.1}>
              <div className="flex items-center justify-center gap-2.5 mb-3">
                <div className="w-11 h-11 rounded-xl flex items-center justify-center shadow-lg" style={{ background: "var(--accent-cyan)" }}>
                  <Heart className="h-6 w-6 text-white" />
                </div>
                <span className="text-2xl font-mono font-bold" style={{ color: "var(--text-primary)" }}>CareOrbit</span>
              </div>
            </FadeIn>
            <p className="text-sm" style={{ color: "var(--text-secondary)" }}>Sign in to your healthcare dashboard</p>
          </div>

          <FadeIn delay={0.2}>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email" style={{ color: "var(--text-secondary)" }}>Email</Label>
                <Input
                  id="email"
                  type="email"
                  data-testid="input-email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="h-10"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="password" style={{ color: "var(--text-secondary)" }}>Password</Label>
                <Input
                  id="password"
                  type="password"
                  data-testid="input-password"
                  placeholder="Enter your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="h-10"
                  required
                />
              </div>
              <Button type="submit" className="w-full h-10" disabled={loading} data-testid="button-login">
                <LogIn className="h-4 w-4 mr-2" />
                {loading ? "Signing in..." : "Sign In"}
              </Button>
            </form>
          </FadeIn>
          <p className="text-center text-sm mt-5" style={{ color: "var(--text-muted)" }}>
            Don't have an account?{" "}
            <Link href="/register" className="font-medium hover:underline" style={{ color: "var(--accent-cyan)" }} data-testid="link-register">
              Register
            </Link>
          </p>
        </div>
      </ScaleIn>
    </div>
  );
}
