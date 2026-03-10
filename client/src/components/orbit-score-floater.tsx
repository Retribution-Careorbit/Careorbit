import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link, useLocation } from "wouter";
import { ArrowRight, X } from "lucide-react";

function getScoreColor(score: number) {
  if (score <= 40) return "var(--accent-rose)";
  if (score <= 60) return "var(--accent-amber)";
  if (score <= 80) return "var(--accent-cyan)";
  return "var(--accent-emerald)";
}

function getScoreLabel(score: number) {
  if (score <= 40) return "Critical";
  if (score <= 60) return "Fair";
  if (score <= 80) return "Good";
  return "Excellent";
}

function getScoreTrend(score: number) {
  if (score >= 70) return { arrow: "↑", delta: "+12" };
  if (score >= 50) return { arrow: "→", delta: "+3" };
  return { arrow: "↓", delta: "-5" };
}

function MiniRing({ score, size }: { score: number; size: number }) {
  const r = (size - 4) / 2;
  const circumference = 2 * Math.PI * r;
  const offset = circumference - (score / 100) * circumference;
  const color = getScoreColor(score);

  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="shrink-0">
      <circle
        cx={size / 2}
        cy={size / 2}
        r={r}
        fill="none"
        stroke="var(--border-subtle)"
        strokeWidth={3}
      />
      <circle
        cx={size / 2}
        cy={size / 2}
        r={r}
        fill="none"
        stroke={color}
        strokeWidth={3}
        strokeLinecap="round"
        strokeDasharray={circumference}
        strokeDashoffset={offset}
        transform={`rotate(-90 ${size / 2} ${size / 2})`}
        style={{ transition: "stroke-dashoffset 600ms ease-out" }}
      />
    </svg>
  );
}

export function OrbitScoreFloater() {
  const [location] = useLocation();
  const [expanded, setExpanded] = useState(false);

  const { data: scoreData } = useQuery<any>({
    queryKey: ["/api/orbit/score"],
    enabled: location === "/",
  });

  if (location !== "/") return null;

  const score = Math.round(scoreData?.total_score || 0);
  const color = getScoreColor(score);
  const label = getScoreLabel(score);
  const trend = getScoreTrend(score);

  if (!scoreData) return null;

  return (
    <div
      className="fixed z-40 animate-floater-entrance hidden lg:block"
      style={{ bottom: 28, left: 280 }}
      data-testid="widget-orbit-floater"
    >
      <div
        className="rounded-[14px] cursor-pointer select-none animate-border-pulse"
        style={{
          width: expanded ? 260 : 220,
          height: expanded ? 172 : 56,
          background: "var(--bg-elevated)",
          border: "1px solid var(--border-default)",
          backdropFilter: "blur(12px) saturate(1.4)",
          boxShadow: "0 8px 32px rgba(0,0,0,0.32), 0 0 0 1px var(--border-subtle)",
          transition: "all 280ms cubic-bezier(0.34, 1.56, 0.64, 1)",
          overflow: "hidden",
        }}
        onClick={() => setExpanded(!expanded)}
      >
        {!expanded ? (
          <div className="flex items-center gap-3 px-3 h-full">
            <MiniRing score={score} size={28} />
            <div className="flex-1 min-w-0">
              <p className="text-[10px] uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>
                Orbit Score
              </p>
              <div className="flex items-center gap-2">
                <span className="font-mono text-lg font-bold leading-none" style={{ color: "var(--text-primary)" }}>
                  {score}
                </span>
                <div
                  className="h-[3px] rounded-full flex-1"
                  style={{ background: "var(--border-subtle)", maxWidth: 80 }}
                >
                  <div
                    className="h-full rounded-full progress-fill"
                    style={{ width: `${score}%`, background: color }}
                  />
                </div>
              </div>
            </div>
            <span className="text-[10px] flex items-center gap-0.5" style={{ color }}>
              {label} {trend.arrow}
            </span>
          </div>
        ) : (
          <div className="p-4 flex flex-col h-full">
            <div className="flex items-center justify-between mb-3">
              <span className="text-[11px] uppercase tracking-wider font-medium" style={{ color: "var(--text-muted)" }}>
                Orbit Score
              </span>
              <button
                onClick={(e) => { e.stopPropagation(); setExpanded(false); }}
                className="h-5 w-5 rounded flex items-center justify-center"
                style={{ color: "var(--text-muted)" }}
              >
                <X className="h-3 w-3" />
              </button>
            </div>

            <div className="flex items-center gap-4 mb-3">
              <div className="relative">
                <MiniRing score={score} size={80} />
                <span
                  className="absolute inset-0 flex items-center justify-center font-mono text-2xl font-bold"
                  style={{ color }}
                >
                  {score}
                </span>
              </div>
              <div className="flex-1">
                <div className="h-[3px] rounded-full w-full" style={{ background: "var(--border-subtle)" }}>
                  <div
                    className="h-full rounded-full progress-fill"
                    style={{ width: `${score}%`, background: color }}
                  />
                </div>
                <div className="flex items-center justify-between mt-2">
                  <span className="text-[11px] font-medium" style={{ color }}>{label}</span>
                  <span className="text-[11px]" style={{ color: "var(--text-muted)" }}>
                    {trend.arrow} {trend.delta} this week
                  </span>
                </div>
              </div>
            </div>

            <Link href="/orbit-score" onClick={(e: any) => e.stopPropagation()}>
              <button
                className="w-full h-8 rounded-lg text-xs font-medium flex items-center justify-center gap-1"
                style={{
                  border: "1px solid var(--border-default)",
                  color: "var(--accent-cyan)",
                  background: "transparent",
                }}
                data-testid="link-floater-orbit"
              >
                View Full Score <ArrowRight className="h-3 w-3" />
              </button>
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
