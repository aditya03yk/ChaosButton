import { ArrowDownRight, ArrowUpRight, Minus } from "lucide-react";
import type { ComparisonResult, MetricRow } from "../../types/metrics";

const LABELS: Record<string, string> = {
  success_rate: "Success rate (%)", error_rate: "Error rate (%)", p50_latency: "P50 latency (ms)", p95_latency: "P95 latency (ms)",
  recovery_time: "Recovery time (s)", fallback_score: "Fallback success (%)", resilience_score: "Resilience score",
};
const num = (v: number | null) => (v == null ? "n/a" : String(v));

function Verdict({ row }: { row: MetricRow }) {
  if (row.verdict === "improved") return <span className="inline-flex items-center gap-1 text-ok"><ArrowUpRight size={13} /> Improved</span>;
  if (row.verdict === "regressed") return <span className="inline-flex items-center gap-1 text-bad"><ArrowDownRight size={13} /> Regressed</span>;
  return <span className="inline-flex items-center gap-1 text-muted"><Minus size={13} /> {row.verdict === "unchanged" ? "Unchanged" : "Unavailable"}</span>;
}

export default function ComparisonTable({ result }: { result: ComparisonResult }) {
  return (
    <div className="space-y-3">
      {!result.comparable && (
        <div role="alert" className="rounded border border-warn/60 bg-warn/10 p-3 text-xs text-warn">
          These runs are not a controlled before/after pair: {result.incompatibilities.join("; ")}.
        </div>
      )}
      {result.target_changed && <div className="text-xs text-info">The target application differs between the runs.</div>}
      <table className="table">
        <thead><tr><th>Metric</th><th>Original</th><th>Retest</th><th>Difference</th><th>Change</th><th /></tr></thead>
        <tbody>
          {result.rows.map((r) => (
            <tr key={r.metric}>
              <td>{LABELS[r.metric] ?? r.metric}</td><td className="mono">{num(r.original)}</td><td className="mono">{num(r.retest)}</td>
              <td className="mono">{num(r.absolute_diff)}</td><td className="mono">{r.percent_diff == null ? "n/a" : `${r.percent_diff}%`}</td>
              <td><Verdict row={r} /></td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="text-xs text-ink2">{result.improved} improved · {result.regressed} regressed (decided by the metrics engine, not by AI).</div>
    </div>
  );
}
