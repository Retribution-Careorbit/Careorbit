import { useQuery } from "@tanstack/react-query";
import { Link } from "wouter";

function getScoreColor(score: number) {
  if (score <= 40) return "var(--accent-rose)";
  if (score <= 60) return "var(--accent-amber)";
  if (score <= 80) return "var(--accent-cyan)";
  return "var(--accent-emerald)";
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
        strokeWidth={2.5}
      />
      <circle
        cx={size / 2}
        cy={size / 2}
        r={r}
        fill="none"
        stroke={color}
        strokeWidth={2.5}
        strokeLinecap="round"
        strokeDasharray={circumference}
        strokeDashoffset={offset}
        transform={`rotate(-90 ${size / 2} ${size / 2})`}
        style={{ transition: "stroke-dashoffset 600ms ease-out" }}
      />
    </svg>
  );
}

export function OrbitScoreBadge() {
  const { data: scoreData } = useQuery<any>({
    queryKey: ["/api/orbit/score"],
  });

  const score = Math.round(scoreData?.total_score || 0);
  const color = scoreData ? getScoreColor(score) : "var(--text-muted)";

  return (
    <Link href="/orbit-score" data-testid="link-orbit-score-badge">
      <div
        className="orbit-score-badge relative rounded-full flex items-center justify-center cursor-pointer shrink-0"
        style={{
          background: "var(--bg-elevated)",
          border: "2px solid var(--border-default)",
        }}
        data-testid="widget-orbit-floater"
        title={`Orbit Score: ${score}`}
        data-color={color}
      >
        <div className="absolute inset-0 flex items-center justify-center orbit-score-ring">
          <MiniRing score={score} size={28} />
        </div>
        <span
          className="font-mono text-[10px] font-bold leading-none z-10"
          style={{ color }}
        >
          {score}
        </span>
      </div>
    </Link>
  );
}
