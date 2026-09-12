"use client";

interface ScoreBarProps {
  value: number; // 0-1
  label: string;
  color?: string;
  showPercentage?: boolean;
  size?: "sm" | "md";
}

export default function ScoreBar({
  value,
  label,
  color = "bg-blue-500",
  showPercentage = true,
  size = "md",
}: ScoreBarProps) {
  const pct = Math.round(value * 100);
  const height = size === "sm" ? "h-1.5" : "h-2";

  return (
    <div className="w-full">
      <div className="flex items-center justify-between mb-1">
        <span className={`text-zinc-400 ${size === "sm" ? "text-xs" : "text-xs"}`}>{label}</span>
        {showPercentage && (
          <span className={`font-mono tabular-nums ${size === "sm" ? "text-xs" : "text-xs"} text-zinc-300`}>
            {pct}%
          </span>
        )}
      </div>
      <div className={`w-full ${height} bg-zinc-800 rounded-full overflow-hidden`}>
        <div
          className={`${height} ${color} rounded-full transition-all duration-700 ease-out`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

export function ScoreBadge({ value, size = "md" }: { value: number; size?: "sm" | "md" | "lg" }) {
  const pct = Math.round(value * 100);
  let color = "text-red-400 bg-red-500/10 border-red-500/20";
  if (pct >= 80) color = "text-emerald-400 bg-emerald-500/10 border-emerald-500/20";
  else if (pct >= 60) color = "text-amber-400 bg-amber-500/10 border-amber-500/20";
  else if (pct >= 40) color = "text-orange-400 bg-orange-500/10 border-orange-500/20";

  const sizeClass = size === "lg" ? "text-2xl px-3 py-1.5" : size === "md" ? "text-sm px-2 py-0.5" : "text-xs px-1.5 py-0.5";

  return (
    <span className={`font-mono tabular-nums font-semibold rounded border ${color} ${sizeClass}`}>
      {pct}
    </span>
  );
}
