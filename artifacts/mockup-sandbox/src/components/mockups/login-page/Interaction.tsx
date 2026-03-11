import React, { useState } from 'react';
import { Heart, LogIn, Shield, Activity, FileText, Eye, EyeOff, Check, Loader2 } from 'lucide-react';
import './_group.css';

export function Interaction() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);

  const isEmailValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  const isPasswordValid = password.length >= 6;

  const getPasswordStrength = () => {
    if (password.length === 0) return 0;
    if (password.length < 6) return 1;
    if (password.length < 10) return 2;
    return 3;
  };
  const strength = getPasswordStrength();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      alert('Logged in successfully!');
    }, 1500);
  };

  return (
    <div className="min-h-screen flex bg-[var(--bg-base)] text-[var(--text-primary)] font-sans relative overflow-hidden">
      <style dangerouslySetInnerHTML={{ __html: `
        @keyframes float-particle {
          0% { transform: translateY(0) translateX(0); opacity: 0; }
          50% { opacity: 0.5; }
          100% { transform: translateY(-100px) translateX(20px); opacity: 0; }
        }
        .particle {
          position: absolute;
          background: rgba(255, 255, 255, 0.1);
          border-radius: 50%;
          animation: float-particle 10s infinite linear;
        }
        .feature-card {
          transition: all 0.3s ease;
          background: var(--bg-surface);
          border: 1px solid var(--border-default);
        }
        .feature-card:hover {
          transform: translateY(-2px);
          box-shadow: 0 8px 24px rgba(0, 212, 255, 0.1);
          border-color: var(--accent-cyan);
        }
        .input-wrapper::after {
          content: '';
          position: absolute;
          bottom: 0;
          left: 0;
          height: 2px;
          width: 0%;
          background: var(--accent-cyan);
          transition: width 0.3s ease;
        }
        .input-wrapper:focus-within::after {
          width: 100%;
        }
        .btn-gradient {
          background: linear-gradient(135deg, var(--accent-cyan), var(--accent-violet));
          background-size: 200% 200%;
          transition: all 0.3s ease;
        }
        .btn-gradient:hover {
          background-position: 100% 0;
          transform: scale(1.02);
          box-shadow: 0 4px 15px var(--accent-violet-dim);
        }
        .social-btn {
          transition: all 0.2s ease;
        }
        .social-btn:hover {
          background: var(--bg-hover);
          transform: translateY(-1px);
        }
        .custom-checkbox {
          transition: all 0.2s ease;
        }
        .custom-checkbox[data-checked="true"] {
          background: var(--accent-cyan);
          border-color: var(--accent-cyan);
        }
      `}} />
      
      {/* Left Panel */}
      <div className="hidden lg:flex w-[520px] flex-col justify-between p-12 relative border-r border-[var(--border-subtle)] z-10 overflow-hidden">
        {/* Particles */}
        {Array.from({ length: 20 }).map((_, i) => (
          <div key={i} className="particle" style={{
            width: Math.random() * 6 + 2 + 'px',
            height: Math.random() * 6 + 2 + 'px',
            left: Math.random() * 100 + '%',
            top: Math.random() * 100 + '%',
            animationDelay: \`\${Math.random() * 5}s\`,
            animationDuration: \`\${Math.random() * 10 + 10}s\`
          }} />
        ))}
        
        {/* Brand */}
        <div className="relative z-10">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-12 h-12 rounded-xl flex items-center justify-center bg-[var(--accent-cyan)] shadow-[0_0_20px_var(--accent-cyan-dim)]">
              <Heart className="h-6 w-6 text-white" />
            </div>
            <span className="text-3xl font-mono font-bold text-white tracking-tight">CareOrbit</span>
          </div>
          <p className="text-[var(--text-secondary)] font-medium tracking-wide uppercase text-sm">HEALTHCARE AI PLATFORM</p>
        </div>

        {/* Content */}
        <div className="relative z-10 space-y-8">
          <div>
            <h2 className="text-4xl font-bold text-white leading-tight mb-4">
              Your health,<br />intelligently managed.
            </h2>
            <p className="text-[var(--text-secondary)] text-lg leading-relaxed">
              Upload prescriptions, track medications, get AI-powered health insights — all in Hindi or English.
            </p>
          </div>

          <div className="space-y-4">
            {[
              { icon: Shield, title: "Drug interaction alerts", desc: "Stay safe with AI checks", color: "var(--accent-cyan)" },
              { icon: Activity, title: "AI health score tracking", desc: "Monitor your vitals", color: "var(--accent-violet)" },
              { icon: FileText, title: "Smart prescription extraction", desc: "Auto-digitize your docs", color: "var(--accent-emerald)" },
            ].map((feature, i) => (
              <div 
                key={i} 
                className="feature-card p-4 rounded-xl flex items-start gap-4 cursor-default"
                style={{ animationDelay: \`\${i * 0.1}s\` }}
              >
                <div className="w-10 h-10 rounded-lg flex items-center justify-center shrink-0" style={{ background: \`color-mix(in srgb, \${feature.color} 20%, transparent)\` }}>
                  <feature.icon className="h-5 w-5" style={{ color: feature.color }} />
                </div>
                <div>
                  <h3 className="font-semibold text-white mb-1">{feature.title}</h3>
                  <p className="text-sm text-[var(--text-muted)]">{feature.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="relative z-10 flex items-center gap-2 text-[var(--text-muted)] text-sm font-medium">
          <Heart className="w-4 h-4 text-[var(--accent-rose)] fill-[var(--accent-rose)]" />
          Built for Indian patients
        </div>
      </div>

      {/* Right Panel */}
      <div className="flex-1 flex items-center justify-center p-6 relative z-10 bg-[var(--bg-surface)]">
        <div className="w-full max-w-[440px]">
          {/* Mobile Header */}
          <div className="lg:hidden flex items-center justify-center gap-3 mb-10">
            <div className="w-12 h-12 rounded-xl flex items-center justify-center bg-[var(--accent-cyan)] shadow-[0_0_20px_var(--accent-cyan-dim)]">
              <Heart className="h-6 w-6 text-white" />
            </div>
            <span className="text-3xl font-mono font-bold text-white tracking-tight">CareOrbit</span>
          </div>

          <div className="bg-[var(--bg-card)] rounded-2xl p-8 border border-[var(--border-subtle)] shadow-2xl">
            <div className="mb-8">
              <h1 className="text-2xl font-bold text-white mb-2">Welcome back</h1>
              <p className="text-[var(--text-secondary)]">Sign in to your healthcare dashboard</p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Email */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-[var(--text-secondary)]">Email Address</label>
                <div className="relative input-wrapper bg-[var(--bg-base)] rounded-lg border border-[var(--border-default)] overflow-hidden transition-colors hover:border-[var(--border-strong)] focus-within:border-[var(--border-strong)]">
                  <input
                    type="email"
                    data-testid="input-email"
                    placeholder="you@example.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full h-12 bg-transparent px-4 text-white placeholder-[var(--text-muted)] outline-none"
                    required
                  />
                  {isEmailValid && (
                    <div className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--accent-emerald)]">
                      <Check className="w-5 h-5" />
                    </div>
                  )}
                </div>
              </div>

              {/* Password */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-[var(--text-secondary)]">Password</label>
                <div className="relative input-wrapper bg-[var(--bg-base)] rounded-lg border border-[var(--border-default)] overflow-hidden transition-colors hover:border-[var(--border-strong)] focus-within:border-[var(--border-strong)]">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    data-testid="input-password"
                    placeholder="Enter your password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full h-12 bg-transparent pl-4 pr-24 text-white placeholder-[var(--text-muted)] outline-none"
                    required
                  />
                  <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-2">
                    {isPasswordValid && (
                      <Check className="w-5 h-5 text-[var(--accent-emerald)]" />
                    )}
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="p-1.5 rounded-md hover:bg-[var(--bg-hover)] text-[var(--text-muted)] hover:text-white transition-colors"
                      data-testid="btn-toggle-password"
                    >
                      {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                    </button>
                  </div>
                </div>
                
                {/* Password Strength */}
                {password.length > 0 && (
                  <div className="pt-1 flex gap-1 h-1.5">
                    <div className={`flex-1 rounded-full ${strength >= 1 ? (strength === 1 ? 'bg-red-500' : strength === 2 ? 'bg-yellow-500' : 'bg-emerald-500') : 'bg-[var(--bg-hover)]'}`} />
                    <div className={`flex-1 rounded-full ${strength >= 2 ? (strength === 2 ? 'bg-yellow-500' : 'bg-emerald-500') : 'bg-[var(--bg-hover)]'}`} />
                    <div className={`flex-1 rounded-full ${strength >= 3 ? 'bg-emerald-500' : 'bg-[var(--bg-hover)]'}`} />
                  </div>
                )}
              </div>

              {/* Options */}
              <div className="flex items-center justify-between">
                <button
                  type="button"
                  onClick={() => setRememberMe(!rememberMe)}
                  className="flex items-center gap-2 group outline-none"
                >
                  <div 
                    data-checked={rememberMe}
                    className="w-5 h-5 custom-checkbox rounded border-2 border-[var(--border-strong)] flex items-center justify-center bg-transparent group-hover:border-[var(--accent-cyan)] group-focus-visible:ring-2 group-focus-visible:ring-[var(--accent-cyan-dim)]"
                  >
                    {rememberMe && <Check className="w-3.5 h-3.5 text-white" />}
                  </div>
                  <span className="text-sm text-[var(--text-secondary)] group-hover:text-white transition-colors">Remember me</span>
                </button>
                <a href="#" className="text-sm text-[var(--accent-cyan)] hover:text-white transition-colors">Forgot password?</a>
              </div>

              {/* Submit */}
              <button
                type="submit"
                disabled={loading}
                data-testid="button-login"
                className="w-full h-12 rounded-xl btn-gradient text-white font-semibold flex items-center justify-center gap-2 disabled:opacity-70 disabled:cursor-not-allowed disabled:transform-none"
              >
                {loading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <>
                    <LogIn className="w-5 h-5" />
                    Sign In
                  </>
                )}
              </button>
            </form>

            {/* Social Logins */}
            <div className="mt-8">
              <div className="relative mb-6">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-[var(--border-subtle)]"></div>
                </div>
                <div className="relative flex justify-center text-sm">
                  <span className="px-2 bg-[var(--bg-card)] text-[var(--text-muted)]">Or continue with</span>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <button type="button" className="social-btn h-11 rounded-lg border border-[var(--border-default)] flex items-center justify-center gap-2 text-sm font-medium text-white">
                  <svg className="w-5 h-5" viewBox="0 0 24 24">
                    <path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                    <path fill="currentColor" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                    <path fill="currentColor" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                    <path fill="currentColor" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
                  </svg>
                  Google
                </button>
                <button type="button" className="social-btn h-11 rounded-lg border border-[var(--border-default)] flex items-center justify-center gap-2 text-sm font-medium text-white">
                  <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12.152 6.896c-.948 0-2.415-1.078-3.96-1.04-2.04.027-3.91 1.183-4.961 3.014-2.117 3.675-.546 9.103 1.519 12.09 1.013 1.454 2.208 3.09 3.792 3.039 1.52-.065 2.09-.987 3.935-.987 1.831 0 2.35.987 3.96.948 1.637-.026 2.676-1.48 3.676-2.948 1.156-1.688 1.636-3.325 1.662-3.415-.039-.013-3.182-1.221-3.22-4.857-.026-3.04 2.48-4.494 2.597-4.559-1.43-2.09-3.603-2.324-4.335-2.376-2.053-.169-3.924 1.253-4.665 1.253zM15.504 4.542c.83-1.006 1.385-2.399 1.233-3.793-1.144.047-2.585.761-3.447 1.761-.692.805-1.353 2.227-1.171 3.603 1.28.1 2.553-.665 3.385-1.571z"/>
                  </svg>
                  Apple
                </button>
              </div>
            </div>
          </div>

          <p className="text-center mt-6 text-[var(--text-secondary)]">
            Don't have an account?{' '}
            <a href="#" className="text-[var(--accent-cyan)] font-medium hover:text-white transition-colors" data-testid="link-register">
              Register
            </a>
          </p>
        </div>
      </div>
    </div>
  );
}
