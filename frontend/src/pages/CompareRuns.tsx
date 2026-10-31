import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import ErrorState from "../components/common/ErrorState";
import PageHeader from "../components/common/PageHeader";
import ComparisonTable from "../components/reports/ComparisonTable";
import { useAsync } from "../hooks/useAsync";
import { FAULT_LABELS } from "../lib/format";
import { compareRuns, listExperiments } from "../services/experimentService";
import type { ComparisonResult } from "../types/metrics";

export default function CompareRuns() {
  const [params, setParams] = useSearchParams();
  const runs = useAsync(() => listExperiments({ status: "COMPLETED", limit: 100 }));
  const [explain, setExplain] = useState(false);
  const [result, setResult] = useState<ComparisonResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const a = params.get("a") ?? "";
  const b = params.get("b") ?? "";

  const select = (key: "a" | "b", value: string) => { const next = new URLSearchParams(params); next.set(key, value); setParams(next); };
  const run = async () => {
    setBusy(true); setError(null);
    try { setResult(await compareRuns(a, b, explain)); } catch (e) { setError((e as Error).message); setResult(null); }
    setBusy(false);
  };
  const options = runs.data?.items ?? [];
  const picker = (key: "a" | "b", label: string, value: string) => (
    <div><label className="label" htmlFor={`cmp-${key}`}>{label}</label>
      <select id={`cmp-${key}`} className="input" value={value} onChange={(e) => select(key, e.target.value)}>
        <option value="">Select a run…</option>
        {options.map((o) => <option key={o.id} value={o.id}>{o.id} · {FAULT_LABELS[o.fault_type]} · {o.target_name}</option>)}
      </select></div>
  );

  return (
    <>
      <PageHeader title="Compare runs" subtitle="Before/after comparison using stored measurements." />
      {runs.error && <ErrorState message={runs.error} onRetry={runs.reload} />}
      <section className="card mb-4 grid gap-3 md:grid-cols-2">
        {picker("a", "Original run", a)}{picker("b", "Retest run", b)}
        <label className="flex items-center gap-2 text-xs text-ink2"><input type="checkbox" checked={explain} onChange={(e) => setExplain(e.target.checked)} /> Ask Gemma to explain the comparison</label>
        <div><button className="btn btn-primary" disabled={!a || !b || a === b || busy} onClick={run}>{busy ? "Comparing…" : "Compare"}</button></div>
      </section>
      {error && <ErrorState message={error} />}
      {result && (
        <section className="card space-y-4">
          <ComparisonTable result={result} />
          {result.ai_validation && (
            <div className="rounded border border-line p-3 text-xs text-ink2">
              <div className="mb-1 font-medium text-ink">Gemma's reading (AI-generated, human review required)</div>
              <p>{result.ai_validation.summary}</p>
              {result.ai_validation.remaining_weaknesses.length > 0 && <p className="mt-1">Remaining weaknesses: {result.ai_validation.remaining_weaknesses.join("; ")}</p>}
            </div>
          )}
          {result.ai_validation_error && <div className="text-xs text-warn">AI explanation unavailable: {result.ai_validation_error}</div>}
        </section>
      )}
    </>
  );
}
