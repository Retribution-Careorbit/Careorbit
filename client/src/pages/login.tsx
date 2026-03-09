import { useState } from "react";
import { useLocation, Link } from "wouter";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
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
        <Card className="w-full max-w-md shadow-xl border-border/50">
          <CardHeader className="text-center pb-2">
            <FadeIn delay={0.1}>
              <div className="flex items-center justify-center gap-2.5 mb-3">
                <div className="w-11 h-11 rounded-xl bg-primary flex items-center justify-center shadow-lg">
                  <Heart className="h-6 w-6 text-primary-foreground" />
                </div>
                <CardTitle className="text-2xl font-heading font-bold tracking-tight">CareOrbit</CardTitle>
              </div>
            </FadeIn>
            <CardDescription className="text-base">Sign in to your healthcare dashboard</CardDescription>
          </CardHeader>
          <CardContent>
            <FadeIn delay={0.2}>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="email">Email</Label>
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
                  <Label htmlFor="password">Password</Label>
                  <Input
                    id="password"
                    type="password"
                    data-testid="input-password"
                    placeholder="Enter your password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="h-11"
                    required
                  />
                </div>
                <Button
                  type="submit"
                  className="w-full h-11 shadow-sm"
                  disabled={loading}
                  data-testid="button-login"
                >
                  <LogIn className="h-4 w-4 mr-2" />
                  {loading ? "Signing in..." : "Sign In"}
                </Button>
              </form>
            </FadeIn>
            <p className="text-center text-sm text-muted-foreground mt-5">
              Don't have an account?{" "}
              <Link href="/register" className="text-primary font-medium hover:underline" data-testid="link-register">
                Register
              </Link>
            </p>
          </CardContent>
        </Card>
      </ScaleIn>
    </div>
  );
}
