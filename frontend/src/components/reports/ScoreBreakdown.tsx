import { fmtScore } from "../../lib/format";
import type { Metrics } from "../../types/metrics";

const LABELS: Record<string, string> = {
  request_success: "Request success", fallback: "Fallback behaviour", recovery: "Recovery time", latency: "Latency impact",
};

export default function ScoreBreakdown({ metrics }: { metrics: Metrics }) {
  return (
    <div>
      <div className="mb-3 flex items-baseline gap-2">
        <span className="mono text-2xl text-accent">{fmtScore(metrics.resilience_score)}</span>
        <span className="text-xs text-ink2">/ 100 resilience score (comparative indicator)</span>
      </div>
      <table className="table">
        <thead><tr><th>Component</th><th>Score</th><th>Weight</th><th>Effective weight</th></tr></thead>
        <tbody>
          {Object.entries(metrics.score_components).map(([key, c]) => (
            <tr key={key}>
              <td>{LABELS[key] ?? key}</td>
              <td className="mono">{c.available ? fmtScore(c.value) : "unavailable"}</td>
              <td className="mono">{(c.weight * 100).toFixed(0)}%</td>
              <td className="mono">{(c.effective_weight * 100).toFixed(0)}%</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="mono mt-3 text-muted">score = Σ(component × effective weight); weights 40/25/20/15, unavailable components re-normalised.</p>
      <p className="mt-1 text-xs text-ink2">Sample size: {metrics.sample_size} requests ({metrics.total_requests} during the fault). Indicative result, not a reliability certification.</p>
      {metrics.limitations.length > 0 && (
        <ul className="mt-2 list-disc pl-5 text-xs text-warn">{metrics.limitations.map((l) => <li key={l}>{l}</li>)}</ul>
      )}
    </div>
  );
}
