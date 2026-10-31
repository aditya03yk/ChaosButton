import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import AnalysisPanel from "../components/ai/AnalysisPanel";
import EmptyState from "../components/common/EmptyState";
import ErrorState from "../components/common/ErrorState";
import LoadingState from "../components/common/LoadingState";
import PageHeader from "../components/common/PageHeader";
import ExperimentTable from "../components/experiments/ExperimentTable";
import { useAsync } from "../hooks/useAsync";
import { analyse, listExperiments } from "../services/experimentService";
import { getAIStatus, getReport } from "../services/reportService";

function ExperimentPicker() {
  const { data, error, loading, reload } = useAsync(() => listExperiments({ status: "COMPLETED", limit: 20 }));
  return (
    <>
      <PageHeader title="AI Assistant" subtitle="Pick a completed experiment to analyse with local Gemma." />
      {loading ? <LoadingState /> : error ? <ErrorState message={error} onRetry={reload} /> :
        !data?.items.length ? <EmptyState title="No completed experiments" text="Run a chaos test first." /> :
        <section className="card"><ExperimentTable items={data.items} /></section>}
    </>
  );
}

export default function AIAnalysis() {
  const { id } = useParams();
  if (!id) return <ExperimentPicker />;
  return <AnalysisView id={id} />;
}

function AnalysisView({ id }: { id: string }) {
  const report = useAsync(() => getReport(id), [id]);
  const ai = useAsync(getAIStatus);
  const [context, setContext] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = async () => {
    setBusy(true); setError(null);
    try { await analyse(id, context); await report.reload(); }
    catch (e) { setError((e as Error).message); await ai.reload(); }
    setBusy(false);
  };

  if (report.loading && !report.data) return <LoadingState />;
  if (report.error || !report.data) return <ErrorState message={report.error ?? "Not found"} onRetry={report.reload} />;
  const analyses = report.data.analyses;
  const status = ai.data;
  const ready = status?.reachable && status.model_available;

  return (
    <>
      <PageHeader title="AI analysis" subtitle={`${id} · ${report.data.experiment.target_name}`}
        actions={<Link className="btn" to={`/experiments/${id}/fixes`}>Fix workspace</Link>} />
      <section className="card mb-4 space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
          <span>Model <span className="mono text-ink">{status?.model ?? "…"}</span> ·{" "}
            <span className={ready ? "text-ok" : "text-bad"}>{status ? status.message : "checking…"}</span></span>
          <button className="btn px-2 py-0.5 text-xs" onClick={ai.reload}>Recheck</button>
        </div>
        {status && !ready && <div role="alert" className="rounded border border-warn/50 bg-warn/10 p-2 text-xs text-warn">{status.hint} Non-AI features keep working.</div>}
        <div><label className="label" htmlFor="ctx">Code context (optional): paste the relevant source so Gemma can reference it</label>
          <textarea id="ctx" className="input mono" rows={4} value={context} onChange={(e) => setContext(e.target.value)} /></div>
        {error && <div role="alert" className="rounded border border-bad/50 bg-bad/10 p-2 text-xs text-bad">{error}
          <button className="btn ml-3 px-2 py-0.5" onClick={run}>Retry analysis</button></div>}
        <button className="btn btn-primary" disabled={busy || !report.data.metrics} onClick={run}>
          {busy ? "Gemma is analysing…" : analyses.length ? "Reanalyse" : "Analyse experiment"}</button>
        {!report.data.metrics && <span className="ml-2 text-xs text-muted">This experiment has no measurements to analyse.</span>}
      </section>
      {analyses.length === 0 ? <EmptyState title="No analysis yet" text="Run the analysis to get a diagnosis and a proposed fix." /> : (
        <div className="space-y-4">
          <AnalysisPanel analysis={analyses[0]} />
          {analyses.length > 1 && <p className="text-xs text-muted">{analyses.length - 1} earlier analysis run(s) are stored in the report.</p>}
        </div>
      )}
    </>
  );
}
