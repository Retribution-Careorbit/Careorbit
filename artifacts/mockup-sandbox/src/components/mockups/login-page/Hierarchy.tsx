import React, { useState } from "react";
import { Heart, LogIn, Shield, Activity, FileText, Lock, ArrowRight, Eye, EyeOff } from "lucide-react";
import "./_group.css";

export function Hierarchy() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setTimeout(() => {
      alert(`Mock sign in for ${email}`);
      setLoading(false);
    }, 1000);
  };

  return (
    <div className="min-h-screen flex" style={{ background: "var(--bg-base)", color: "var(--text-primary)", fontFamily: "var(--font-sans)" }}>
      {/* Left Panel */}
      <div className="hidden lg:flex lg:w-[480px] xl:w-[560px] flex-col justify-between p-12 relative overflow-hidden" style={{ background: "var(--bg-surface)", borderRight: "1px solid var(--border-default)" }}>
        {/* Floating Background Shapes */}
        <div className="absolute top-[-10%] right-[-20%] w-[400px] h-[400px] rounded-full blur-[100px] opacity-20 pointer-events-none" style={{ background: "var(--accent-cyan)" }} />
        <div className="absolute bottom-[-10%] left-[-10%] w-[300px] h-[300px] rounded-full blur-[80px] opacity-10 pointer-events-none" style={{ background: "var(--accent-violet)" }} />

        {/* TOP: Logo */}
        <div className="relative z-10">
          <div className="inline-flex items-center gap-3 p-2 pr-4 rounded-full" style={{ background: "var(--bg-elevated)", border: "1px solid var(--border-subtle)" }}>
            <div className="w-10 h-10 rounded-full flex items-center justify-center shadow-[0_0_15px_rgba(0,212,255,0.4)]" style={{ background: "var(--accent-cyan)" }}>
              <Heart className="h-5 w-5 text-[#0A0C10] fill-current" />
            </div>
            <span className="text-xl font-bold tracking-tight" style={{ fontFamily: "var(--font-mono)" }}>CareOrbit</span>
          </div>
        </div>

        {/* MIDDLE: Headline & Features */}
        <div className="relative z-10 flex flex-col gap-10 mt-12 mb-auto">
          <div>
            <h1 className="text-4xl xl:text-5xl font-bold leading-[1.15] tracking-tight mb-4 text-white">
              Your health,<br />
              <span style={{ color: "var(--accent-cyan)" }}>intelligently managed.</span>
            </h1>
            <p className="text-lg leading-relaxed max-w-[400px]" style={{ color: "var(--text-secondary)" }}>
              Upload prescriptions, track medications, get AI-powered health insights — all in Hindi or English.
            </p>
          </div>

          <div className="flex flex-col gap-6">
            {[
              { num: "01", icon: Shield, title: "Drug interaction alerts", desc: "Automated checks for medication safety", color: "var(--accent-cyan)" },
              { num: "02", icon: Activity, title: "AI health score tracking", desc: "Real-time monitoring of your vitals", color: "var(--accent-violet)" },
              { num: "03", icon: FileText, title: "Smart prescription extraction", desc: "Turn paper into digital records instantly", color: "var(--accent-emerald)" },
            ].map((feature) => (
              <div key={feature.num} className="flex items-start gap-5 relative group">
                <div className="absolute left-0 top-0 bottom-0 w-1 rounded-full opacity-70 group-hover:opacity-100 transition-opacity" style={{ background: feature.color }} />
                <div className="pl-4 flex items-start gap-4">
                  <div className="flex flex-col items-center mt-1">
                    <span className="text-xs font-bold" style={{ color: feature.color, fontFamily: "var(--font-mono)" }}>{feature.num}</span>
                  </div>
                  <div>
                    <h3 className="text-base font-semibold text-white mb-1">{feature.title}</h3>
                    <p className="text-sm" style={{ color: "var(--text-secondary)" }}>{feature.desc}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* BOTTOM: Trust Indicators */}
        <div className="relative z-10 mt-12 pt-8" style={{ borderTop: "1px solid var(--border-subtle)" }}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm font-medium" style={{ color: "var(--text-secondary)" }}>
              <span>Built for Indian patients</span>
              <span className="text-lg leading-none" aria-label="India flag">🇮🇳</span>
            </div>
            <div className="flex gap-3">
              <div className="flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-medium" style={{ background: "var(--bg-elevated)", color: "var(--text-secondary)", border: "1px solid var(--border-subtle)" }}>
                <Lock className="w-3.5 h-3.5" style={{ color: "var(--accent-emerald)" }} />
                <span>Encrypted</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Right Panel */}
      <div className="flex-1 flex flex-col items-center justify-center p-6 sm:p-12 relative overflow-y-auto">
        <div className="w-full max-w-[440px] flex flex-col items-center">
          
          {/* Mobile Logo */}
          <div className="lg:hidden flex items-center gap-3 mb-10 p-2 pr-4 rounded-full" style={{ background: "var(--bg-surface)", border: "1px solid var(--border-subtle)" }}>
            <div className="w-10 h-10 rounded-full flex items-center justify-center shadow-[0_0_15px_rgba(0,212,255,0.4)]" style={{ background: "var(--accent-cyan)" }}>
              <Heart className="h-5 w-5 text-[#0A0C10] fill-current" />
            </div>
            <span className="text-xl font-bold tracking-tight" style={{ fontFamily: "var(--font-mono)", color: "white" }}>CareOrbit</span>
          </div>

          <div className="w-full rounded-2xl p-8 sm:p-10 shadow-2xl relative" style={{ background: "var(--bg-card)", border: "1px solid var(--border-default)" }}>
            {/* Form Top Label */}
            <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 px-4 py-1 rounded-full text-[11px] font-bold tracking-wider uppercase" style={{ background: "var(--bg-elevated)", color: "var(--accent-cyan)", border: "1px solid var(--border-default)" }}>
              Sign In
            </div>

            <div className="mb-8 mt-2 text-center">
              <h2 className="text-3xl font-bold text-white mb-2">Welcome back</h2>
              <p className="text-base" style={{ color: "var(--text-secondary)" }}>
                Sign in to your healthcare dashboard
              </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Email Field - Floating Label Style Layout */}
              <div className="relative group">
                <div className="absolute inset-0 rounded-xl transition-colors pointer-events-none" style={{ border: "1px solid var(--border-strong)" }} />
                <div className="absolute -top-2.5 left-4 px-1.5 text-xs font-medium transition-colors" style={{ background: "var(--bg-card)", color: "var(--text-muted)" }}>
                  Email Address
                </div>
                <input
                  type="email"
                  required
                  data-testid="input-email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full h-[52px] bg-transparent px-5 outline-none text-white focus:ring-0 transition-all rounded-xl"
                  style={{ fontSize: "16px" }}
                  placeholder="you@example.com"
                />
              </div>

              {/* Password Field - Floating Label Style Layout */}
              <div className="relative group">
                <div className="absolute inset-0 rounded-xl transition-colors pointer-events-none" style={{ border: "1px solid var(--border-strong)" }} />
                <div className="absolute -top-2.5 left-4 px-1.5 text-xs font-medium transition-colors" style={{ background: "var(--bg-card)", color: "var(--text-muted)" }}>
                  Password
                </div>
                <div className="flex items-center h-[52px] px-5">
                  <input
                    type={showPassword ? "text" : "password"}
                    required
                    data-testid="input-password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full h-full bg-transparent outline-none text-white focus:ring-0 transition-all"
                    style={{ fontSize: "16px" }}
                    placeholder="Enter your password"
                  />
                  <button 
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="p-1 outline-none hover:opacity-100 opacity-60 transition-opacity flex-shrink-0"
                    style={{ color: "var(--text-secondary)" }}
                  >
                    {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                  </button>
                </div>
              </div>

              <div className="flex justify-end mt-2 mb-6">
                <a href="#" className="text-sm font-medium hover:underline transition-colors" style={{ color: "var(--accent-cyan)" }}>
                  Forgot password?
                </a>
              </div>

              <button
                type="submit"
                disabled={loading}
                data-testid="button-login"
                className="w-full h-[52px] rounded-xl flex items-center justify-center gap-2 text-base font-bold transition-all hover:brightness-110 active:scale-[0.98] disabled:opacity-70 disabled:pointer-events-none shadow-[0_4px_14px_rgba(0,212,255,0.25)]"
                style={{ background: "var(--accent-cyan)", color: "#0A0C10" }}
              >
                {loading ? (
                  <div className="w-5 h-5 border-2 border-[#0A0C10] border-t-transparent rounded-full animate-spin" />
                ) : (
                  <>
                    Sign In
                    <LogIn className="w-5 h-5 ml-1" />
                  </>
                )}
              </button>
            </form>
          </div>

          <div className="mt-8 text-center">
            <p className="text-sm flex items-center justify-center gap-2" style={{ color: "var(--text-muted)" }}>
              Don't have an account? 
              <a href="/register" className="font-semibold flex items-center hover:underline transition-colors group" style={{ color: "var(--text-primary)" }} data-testid="link-register">
                Register 
                <ArrowRight className="w-3.5 h-3.5 ml-1 group-hover:translate-x-0.5 transition-transform" style={{ color: "var(--accent-cyan)" }} />
              </a>
            </p>
          </div>
          
        </div>
      </div>
    </div>
  );
}
