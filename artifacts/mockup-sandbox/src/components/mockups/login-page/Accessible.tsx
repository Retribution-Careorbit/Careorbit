import React, { useState, useRef } from "react";
import { Heart, LogIn, Shield, Activity, FileText, Eye, EyeOff, AlertCircle } from "lucide-react";
import "./_group.css";

export function Accessible() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [emailError, setEmailError] = useState("Please enter a valid email address");

  const emailInputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.includes("@")) {
      setEmailError("Please enter a valid email address containing an @ symbol.");
      emailInputRef.current?.focus();
      return;
    }
    setEmailError("");
    setLoading(true);
    setTimeout(() => {
      alert(`Mock Login Submitted\nEmail: ${email}`);
      setLoading(false);
    }, 1000);
  };

  const handleSkipToSignIn = (e: React.MouseEvent<HTMLAnchorElement>) => {
    e.preventDefault();
    emailInputRef.current?.focus();
  };

  return (
    <div className="min-h-screen flex bg-[var(--bg-base)] text-[var(--text-primary)] font-sans">
      {/* Skip to Sign In Link - Accessible to keyboard/screen readers only until focused */}
      <a 
        href="#login-form" 
        onClick={handleSkipToSignIn}
        className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-6 focus:py-3 focus:bg-[var(--accent-cyan)] focus:text-black focus:font-bold focus:rounded focus:outline-none focus:ring-4 focus:ring-white focus:ring-offset-4 focus:ring-offset-[var(--bg-base)] text-lg"
      >
        Skip to Sign In
      </a>

      {/* Left Panel - Brand & Features (Hidden on Mobile) */}
      <div className="hidden lg:flex lg:w-1/2 flex-col justify-between p-12 bg-[var(--bg-surface)] border-r-2 border-[var(--border-strong)]">
        <div className="max-w-2xl mx-auto w-full h-full flex flex-col justify-between">
          
          {/* Header */}
          <div>
            <div className="flex items-center gap-4 mb-16">
              <div 
                className="w-14 h-14 rounded-md flex items-center justify-center border-2 border-[var(--accent-cyan)] bg-[var(--bg-elevated)]"
                aria-hidden="true"
              >
                <Heart className="h-8 w-8 text-[var(--accent-cyan)]" strokeWidth={2.5} />
              </div>
              <span className="text-3xl font-mono font-bold tracking-tight text-white">CareOrbit</span>
            </div>

            <div className="space-y-6 mb-12 pb-12 border-b-2 border-[var(--border-strong)]">
              <h1 className="text-4xl xl:text-5xl font-bold leading-tight text-white">
                Your health,<br />intelligently managed.
              </h1>
              <p className="text-xl text-[var(--text-primary)] leading-relaxed max-w-lg">
                Upload prescriptions, track medications, and get AI-powered health insights — available in Hindi or English.
              </p>
            </div>

            {/* Features List */}
            <div className="space-y-8" role="list" aria-label="Key features">
              {[
                { icon: Shield, label: "Drug interaction alerts", desc: "Get notified before taking conflicting medications." },
                { icon: Activity, label: "AI health score tracking", desc: "Monitor your vitals with intelligent analysis." },
                { icon: FileText, label: "Smart prescription extraction", desc: "Automatically digitize your paper records." },
              ].map((feature, idx) => (
                <div key={idx} className="flex items-start gap-5" role="listitem">
                  <div className="mt-1 w-12 h-12 rounded-full bg-[var(--bg-elevated)] border-2 border-[var(--border-default)] flex items-center justify-center shrink-0">
                    <feature.icon className="h-7 w-7 text-[var(--accent-cyan)]" aria-hidden="true" strokeWidth={2} />
                  </div>
                  <div>
                    <h2 className="text-xl font-bold text-white mb-1">{feature.label}</h2>
                    <p className="text-lg text-[var(--text-primary)]">{feature.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Footer */}
          <div className="pt-8 border-t-2 border-[var(--border-strong)] mt-12">
            <p className="text-lg font-medium text-[var(--text-primary)]">
              Built for Indian patients
            </p>
          </div>
        </div>
      </div>

      {/* Right Panel - Login Form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-6 sm:p-12 bg-[var(--bg-base)]">
        <div className="w-full max-w-md">
          
          {/* Mobile Logo (Hidden on Desktop) */}
          <div className="lg:hidden flex flex-col items-center justify-center gap-4 mb-10 pb-8 border-b-2 border-[var(--border-strong)]">
            <div 
              className="w-16 h-16 rounded-md flex items-center justify-center border-2 border-[var(--accent-cyan)] bg-[var(--bg-surface)]"
              aria-hidden="true"
            >
              <Heart className="h-8 w-8 text-[var(--accent-cyan)]" strokeWidth={2.5} />
            </div>
            <h1 className="text-3xl font-mono font-bold text-white">CareOrbit</h1>
            <p className="text-lg text-[var(--text-primary)] text-center">Healthcare AI Platform</p>
          </div>

          <div className="bg-[var(--bg-card)] rounded-xl border-2 border-[var(--border-strong)] p-8 shadow-2xl">
            <div className="mb-8 border-b-2 border-[var(--border-strong)] pb-6">
              <h2 className="text-3xl font-bold text-white mb-2" id="login-heading">Welcome back</h2>
              <p className="text-lg text-[var(--text-primary)]">Sign in to your healthcare dashboard</p>
            </div>

            <form 
              id="login-form"
              onSubmit={handleSubmit} 
              className="space-y-8" 
              aria-labelledby="login-heading"
              noValidate
            >
              {/* Email Field */}
              <div className="space-y-3">
                <label 
                  htmlFor="email" 
                  className="block text-lg font-bold text-white"
                >
                  Email address
                  <span className="text-[var(--accent-rose)] ml-1" aria-hidden="true">*</span>
                  <span className="sr-only"> (required)</span>
                </label>
                <input
                  ref={emailInputRef}
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => {
                    setEmail(e.target.value);
                    if (emailError) setEmailError("");
                  }}
                  className={`w-full h-14 px-4 bg-[var(--bg-base)] border-2 ${
                    emailError ? 'border-[var(--accent-rose)]' : 'border-[var(--border-strong)]'
                  } rounded-lg text-lg text-white placeholder-[var(--text-muted)] focus:outline-none focus:ring-4 focus:ring-[var(--accent-cyan)] focus:border-transparent transition-shadow`}
                  placeholder="you@example.com"
                  aria-required="true"
                  aria-invalid={emailError ? "true" : "false"}
                  aria-describedby={emailError ? "email-error" : undefined}
                  data-testid="input-email"
                  tabIndex={1}
                />
                {emailError && (
                  <div id="email-error" className="flex items-center gap-2 text-[var(--accent-rose)] mt-2 font-medium" role="alert">
                    <AlertCircle className="h-5 w-5 shrink-0" aria-hidden="true" />
                    <span className="text-base">{emailError}</span>
                  </div>
                )}
              </div>

              {/* Password Field */}
              <div className="space-y-3">
                <label 
                  htmlFor="password" 
                  className="block text-lg font-bold text-white"
                >
                  Password
                  <span className="text-[var(--accent-rose)] ml-1" aria-hidden="true">*</span>
                  <span className="sr-only"> (required)</span>
                </label>
                <div className="relative">
                  <input
                    id="password"
                    type={showPassword ? "text" : "password"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full h-14 px-4 pr-16 bg-[var(--bg-base)] border-2 border-[var(--border-strong)] rounded-lg text-lg text-white placeholder-[var(--text-muted)] focus:outline-none focus:ring-4 focus:ring-[var(--accent-cyan)] focus:border-transparent transition-shadow"
                    placeholder="Enter your password"
                    aria-required="true"
                    data-testid="input-password"
                    tabIndex={2}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-2 top-2 h-10 w-12 flex items-center justify-center rounded focus:outline-none focus:ring-4 focus:ring-[var(--accent-cyan)] text-[var(--text-primary)] hover:text-white hover:bg-[var(--bg-hover)] transition-colors"
                    aria-label={showPassword ? "Hide password" : "Show password"}
                    aria-pressed={showPassword}
                    data-testid="button-toggle-password"
                    tabIndex={3}
                  >
                    {showPassword ? (
                      <EyeOff className="h-6 w-6" aria-hidden="true" />
                    ) : (
                      <Eye className="h-6 w-6" aria-hidden="true" />
                    )}
                  </button>
                </div>
              </div>

              {/* Sign In Button */}
              <button
                type="submit"
                disabled={loading}
                className="w-full h-16 mt-4 flex items-center justify-center gap-3 bg-[var(--accent-cyan)] text-black font-bold text-xl rounded-lg border-2 border-transparent focus:outline-none focus:ring-4 focus:ring-white focus:ring-offset-4 focus:ring-offset-[var(--bg-card)] hover:bg-[#00bfe6] disabled:opacity-70 transition-all shadow-[0_4px_14px_rgba(0,212,255,0.25)]"
                data-testid="button-login"
                tabIndex={4}
                aria-disabled={loading}
              >
                <LogIn className="h-6 w-6" aria-hidden="true" strokeWidth={2.5} />
                {loading ? "Signing in..." : "Sign In"}
              </button>
            </form>
          </div>

          {/* Registration Link */}
          <div className="mt-8 text-center bg-[var(--bg-surface)] p-6 rounded-lg border-2 border-[var(--border-default)]">
            <p className="text-lg text-[var(--text-primary)]">
              Don't have an account?{" "}
              <a 
                href="/register" 
                className="inline-block mt-2 sm:mt-0 sm:ml-2 font-bold text-[var(--accent-cyan)] underline decoration-2 underline-offset-4 hover:text-[#4dffff] focus:outline-none focus:ring-4 focus:ring-[var(--accent-cyan)] focus:ring-offset-4 focus:ring-offset-[var(--bg-base)] rounded px-1"
                data-testid="link-register"
                tabIndex={5}
              >
                Register for CareOrbit
              </a>
            </p>
          </div>
          
        </div>
      </div>
    </div>
  );
}
