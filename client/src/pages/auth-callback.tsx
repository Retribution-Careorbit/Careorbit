import { useEffect, useState } from "react";
import { useLocation } from "wouter";
import { Loader2 } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { useAuthStore } from "@/lib/auth";

function getExchangeCode(): string | null {
  const params = new URLSearchParams(window.location.search);
  return params.get("exchange_code");
}

export default function AuthCallbackPage() {
  const [, navigate] = useLocation();
  const { toast } = useToast();
  const setAuth = useAuthStore((s) => s.setAuth);
  const [message, setMessage] = useState("Completing secure sign-in...");

  useEffect(() => {
    const run = async () => {
      const exchangeCode = getExchangeCode();
      if (!exchangeCode) {
        setMessage("Missing login code. Please try again.");
        return;
      }

      try {
        const res = await fetch("/api/auth/entra/exchange", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ exchange_code: exchangeCode }),
        });

        const raw = await res.text();
        const data = raw ? (() => { try { return JSON.parse(raw); } catch { return null; } })() : null;

        if (!res.ok || !data) {
          const detail = (data && (data.detail || data.message)) || raw || "Federated sign-in failed";
          throw new Error(detail);
        }

        const user = data.user || {};
        setAuth(data.access_token, data.refresh_token, {
          id: user.id || user.email || "entra-user",
          email: user.email,
          name: user.name,
          onboardingComplete: !!user.onboarding_complete,
          preferredLanguage: user.preferred_language || "en",
        });

        navigate(user.onboarding_complete ? "/" : "/onboarding");
      } catch (error: any) {
        toast({
          title: "Sign-in failed",
          description: error?.message || "Could not complete sign-in.",
          variant: "destructive",
        });
        navigate("/login");
      }
    };

    run();
  }, [navigate, setAuth, toast]);

  return (
    <div className="min-h-screen flex items-center justify-center" style={{ background: "var(--bg-base)", color: "var(--text-primary)" }}>
      <div className="rounded-2xl px-8 py-7 text-center" style={{ background: "var(--bg-card)", border: "1px solid var(--border-subtle)" }}>
        <div className="flex items-center justify-center mb-3">
          <Loader2 className="w-6 h-6 animate-spin" style={{ color: "var(--accent-cyan)" }} />
        </div>
        <p className="text-sm" style={{ color: "var(--text-secondary)" }}>{message}</p>
      </div>
    </div>
  );
}
