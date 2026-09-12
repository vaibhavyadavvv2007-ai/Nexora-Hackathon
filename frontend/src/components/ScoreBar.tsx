"use client";

interface ScoreBarProps {
  value: number; // 0-1
  label: string;
  weight?: string;
  color?: string;
  showPercentage?: boolean;
  size?: "sm" | "md";
}

export default function ScoreBar({
  value,
  label,
  weight,
  color = "bg-blue-500",
  showPercentage = true,
  size = "md",
}: ScoreBarProps) {
  const pct = Math.round(Math.min(Math.max(value, 0), 1) * 100);
  const height = size === "sm" ? "h-1.5" : "h-2";

  return (
    <div className="w-full">
      <div className="flex items-center justify-between mb-1 text-xs">
        <div className="flex items-center gap-1.5">
          <span className="text-zinc-300 font-medium">{label}</span>
          {weight && (
            <span className="text-[10px] text-zinc-500 font-mono">({weight})</span>
          )}
        </div>
        {showPercentage && (
          <span className="font-mono tabular-nums font-semibold text-zinc-200">
            {pct}%
          </span>
        )}
      </div>
      <div
        role="progressbar"
        aria-valuenow={pct}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={`${label} progress: ${pct}%`}
        className={`w-full ${height} bg-zinc-800/80 rounded-full overflow-hidden`}
      >
        <div
          className={`${height} ${color} rounded-full transition-all duration-500 ease-out`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

export function ScoreBadge({
  value,
  size = "md",
  showLabel = false,
}: {
  value: number;
  size?: "sm" | "md" | "lg";
  showLabel?: boolean;
}) {
  const pct = Math.round(Math.min(Math.max(value, 0), 1) * 100);

  let colorClasses = "text-red-400 bg-red-950/30 border-red-500/30";
  let statusText = "Low";

  if (pct >= 80) {
    colorClasses = "text-emerald-300 bg-emerald-950/30 border-emerald-500/40";
    statusText = "High";
  } else if (pct >= 65) {
    colorClasses = "text-amber-300 bg-amber-950/30 border-amber-500/40";
    statusText = "Moderate";
  } else if (pct >= 50) {
    colorClasses = "text-orange-300 bg-orange-950/30 border-orange-500/40";
    statusText = "Fair";
  }

  const sizeClasses =
    size === "lg"
      ? "text-2xl px-3 py-1 font-bold"
      : size === "md"
        ? "text-xs px-2 py-0.5 font-semibold"
        : "text-[11px] px-1.5 py-0.5 font-medium";

  return (
    <span
      className={`inline-flex items-center gap-1 font-mono tabular-nums rounded border ${colorClasses} ${sizeClasses}`}
      title={`${statusText} score: ${pct}%`}
    >
      <span>{pct}%</span>
      {showLabel && (
        <span className="text-[10px] uppercase font-sans tracking-wider opacity-80">
          {statusText}
        </span>
      )}
    </span>
  );
}
