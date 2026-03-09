import { useId } from "react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  RadialBarChart, RadialBar, PieChart, Pie, Cell, BarChart, Bar, Area, AreaChart,
} from "recharts";

const NEON_COLORS = {
  cyan: "#00d9ff",
  purple: "#7c3aed",
  orange: "#fb923c",
  green: "#10b981",
  red: "#ef4444",
  pink: "#ec4899",
};

interface HealthMetricsChartProps {
  data: Array<{ date: string; value: number; value2?: number }>;
  label?: string;
  label2?: string;
  color?: string;
  color2?: string;
  height?: number;
  showArea?: boolean;
}

export function HealthMetricsChart({
  data,
  label = "Value",
  label2,
  color = NEON_COLORS.cyan,
  color2 = NEON_COLORS.purple,
  height = 250,
  showArea = true,
}: HealthMetricsChartProps) {
  const uid = useId();
  const gradId1 = `colorV1-${uid}`;
  const gradId2 = `colorV2-${uid}`;
  const ChartComponent = showArea ? AreaChart : LineChart;
  return (
    <ResponsiveContainer width="100%" height={height}>
      <ChartComponent data={data}>
        <defs>
          <linearGradient id={gradId1} x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor={color} stopOpacity={0.3} />
            <stop offset="95%" stopColor={color} stopOpacity={0} />
          </linearGradient>
          <linearGradient id={gradId2} x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor={color2} stopOpacity={0.3} />
            <stop offset="95%" stopColor={color2} stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.5} />
        <XAxis
          dataKey="date"
          stroke="hsl(var(--muted-foreground))"
          fontSize={12}
          tickLine={false}
          axisLine={false}
        />
        <YAxis
          stroke="hsl(var(--muted-foreground))"
          fontSize={12}
          tickLine={false}
          axisLine={false}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: "hsl(var(--card))",
            border: "1px solid hsl(var(--border))",
            borderRadius: "8px",
            color: "hsl(var(--foreground))",
            fontSize: "12px",
          }}
        />
        {showArea ? (
          <>
            <Area type="monotone" dataKey="value" name={label} stroke={color} strokeWidth={2} fill={`url(#${gradId1})`} dot={{ r: 3, fill: color }} />
            {label2 && <Area type="monotone" dataKey="value2" name={label2} stroke={color2} strokeWidth={2} fill={`url(#${gradId2})`} dot={{ r: 3, fill: color2 }} />}
          </>
        ) : (
          <>
            <Line type="monotone" dataKey="value" name={label} stroke={color} strokeWidth={2} dot={{ r: 3, fill: color }} />
            {label2 && <Line type="monotone" dataKey="value2" name={label2} stroke={color2} strokeWidth={2} dot={{ r: 3, fill: color2 }} />}
          </>
        )}
      </ChartComponent>
    </ResponsiveContainer>
  );
}

interface OrbitScoreRadialProps {
  score: number;
  size?: number;
  label?: string;
}

export function OrbitScoreRadial({ score, size = 200, label = "Orbit Score" }: OrbitScoreRadialProps) {
  const data = [{ name: label, value: score, fill: score >= 70 ? NEON_COLORS.green : score >= 40 ? NEON_COLORS.orange : NEON_COLORS.red }];
  const bgData = [{ name: "bg", value: 100, fill: "hsl(var(--muted))" }];

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <ResponsiveContainer width="100%" height="100%">
        <RadialBarChart cx="50%" cy="50%" innerRadius="70%" outerRadius="90%" startAngle={90} endAngle={-270} data={bgData} barSize={12}>
          <RadialBar dataKey="value" cornerRadius={6} />
        </RadialBarChart>
      </ResponsiveContainer>
      <div className="absolute inset-0">
        <ResponsiveContainer width="100%" height="100%">
          <RadialBarChart cx="50%" cy="50%" innerRadius="70%" outerRadius="90%" startAngle={90} endAngle={90 - (score / 100) * 360} data={data} barSize={12}>
            <RadialBar dataKey="value" cornerRadius={6} />
          </RadialBarChart>
        </ResponsiveContainer>
      </div>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-3xl font-heading font-bold" data-testid="text-orbit-score">{Math.round(score)}</span>
        <span className="text-xs text-muted-foreground">{label}</span>
      </div>
    </div>
  );
}

interface AdherenceDonutProps {
  percentage: number;
  size?: number;
}

export function AdherenceDonut({ percentage, size = 140 }: AdherenceDonutProps) {
  const data = [
    { name: "Taken", value: percentage },
    { name: "Missed", value: 100 - percentage },
  ];
  const colors = [NEON_COLORS.cyan, "hsl(var(--muted))"];

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie data={data} cx="50%" cy="50%" innerRadius="65%" outerRadius="85%" startAngle={90} endAngle={-270} dataKey="value" strokeWidth={0}>
            {data.map((_, index) => (
              <Cell key={index} fill={colors[index]} />
            ))}
          </Pie>
        </PieChart>
      </ResponsiveContainer>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-xl font-heading font-bold" data-testid="text-adherence-score">{percentage}%</span>
        <span className="text-[10px] text-muted-foreground">Adherence</span>
      </div>
    </div>
  );
}

interface CategoryBreakdownBarProps {
  data: Array<{ name: string; value: number; color?: string }>;
  height?: number;
}

export function CategoryBreakdownBar({ data, height = 200 }: CategoryBreakdownBarProps) {
  const palette = [NEON_COLORS.cyan, NEON_COLORS.purple, NEON_COLORS.green, NEON_COLORS.orange, NEON_COLORS.pink];

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} layout="vertical" margin={{ left: 80 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.5} horizontal={false} />
        <XAxis type="number" domain={[0, 100]} stroke="hsl(var(--muted-foreground))" fontSize={12} tickLine={false} />
        <YAxis type="category" dataKey="name" stroke="hsl(var(--muted-foreground))" fontSize={12} tickLine={false} axisLine={false} />
        <Tooltip
          contentStyle={{
            backgroundColor: "hsl(var(--card))",
            border: "1px solid hsl(var(--border))",
            borderRadius: "8px",
            color: "hsl(var(--foreground))",
            fontSize: "12px",
          }}
        />
        <Bar dataKey="value" radius={[0, 6, 6, 0]} barSize={20}>
          {data.map((entry, index) => (
            <Cell key={index} fill={entry.color || palette[index % palette.length]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

interface SparklineProps {
  data: number[];
  color?: string;
  width?: number;
  height?: number;
}

export function Sparkline({ data, color = NEON_COLORS.cyan, width = 120, height = 40 }: SparklineProps) {
  const uid = useId();
  const gradId = `spark-${uid}`;
  const chartData = data.map((v, i) => ({ i, v }));
  return (
    <ResponsiveContainer width={width} height={height}>
      <AreaChart data={chartData}>
        <defs>
          <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor={color} stopOpacity={0.3} />
            <stop offset="95%" stopColor={color} stopOpacity={0} />
          </linearGradient>
        </defs>
        <Area type="monotone" dataKey="v" stroke={color} strokeWidth={1.5} fill={`url(#${gradId})`} dot={false} />
      </AreaChart>
    </ResponsiveContainer>
  );
}
