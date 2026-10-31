interface Props { label: string; value: string; hint?: string; tone?: "default" | "ok" | "warn" | "bad" }

const TONES = { default: "text-ink", ok: "text-ok", warn: "text-warn", bad: "text-bad" };

export default function MetricCard({ label, value, hint, tone = "default" }: Props) {
  return (
    <div className="card py-3">
      <div className="text-xs text-ink2">{label}</div>
      <div className={`mt-1 font-mono text-xl ${TONES[tone]}`}>{value}</div>
      {hint && <div className="mt-0.5 text-xs text-muted">{hint}</div>}
    </div>
  );
}
