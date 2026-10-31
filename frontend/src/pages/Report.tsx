import { Link, useParams } from "react-router-dom";
import AnalysisPanel from "../components/ai/AnalysisPanel";
import EmptyState from "../components/common/EmptyState";
import ErrorState from "../components/common/ErrorState";
import LoadingState from "../components/common/LoadingState";
import MetricCard from "../components/common/MetricCard";
import PageHeader from "../components/common/PageHeader";
import StatusBadge from "../components/common/StatusBadge";
import EventTimeline from "../components/experiments/EventTimeline";
import ComparisonTable from "../components/reports/ComparisonTable";
import ScoreBreakdown from "../components/reports/ScoreBreakdown";
import { useAsync } from "../hooks/useAsync";
import { FAULT_LABELS, fmtDateTime, fmtMs, fmtPct, fmtSeconds } from "../lib/format";
import { getReport, reportDownloadUrl } from "../services/reportService";

export default function Report() {
  const { id = "" } = useParams();
  const { data, error, loading, reload } = useAsync(() => getReport(id), [id]);
  if (loading && !data) return <LoadingState />;
  if (error || !data) return <ErrorState message={error ?? "Not found"} onRetry={reload} />;
  const { experiment: exp, target, metrics: m } = data;
  const failed = data.request_events.filter((e) => e.phase === "fault" && !e.success);

  return (
    <>
      <PageHeader title={`Report ${exp.id}`} subtitle={`${FAULT_LABELS[exp.fault_type]} · ${target.name} · ${fmtDateTime(exp.created_at)}`} actions={<>
        <a className="btn" href={reportDownloadUrl(id)} download>Export JSON</a>
        <Link className="btn" to={`/experiments/${id}/results`}>Results</Link></>} />
      <div className="space-y-4">
        <section className="card grid gap-3 text-xs md:grid-cols-2">
          <div><h2 className="mb-1">Target</h2><div>{target.name} <span className="mono text-muted">{target.base_url}</span></div>
            <div className="text-ink2">{target.technology_stack} · {target.environment_type}</div></div>
          <div><h2 className="mb-1">Configuration</h2>
            <div className="mono">{exp.method} {exp.route} · {exp.fault_type}</div>
            <pre className="mono mt-1 whitespace-pre-wrap text-muted">{JSON.stringify(exp.fault_configuration)}</pre></div>
          <div>Status: <StatusBadge status={exp.status} /> · duration {exp.duration ?? "n/a"} s</div>
          <div className="text-ink2">{exp.error_message}</div>
        </section>

        {!m ? <EmptyState title="No measurements recorded" /> : (<>
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <MetricCard label="Baseline P50 / P95" value={`${fmtMs(m.baseline_p50_latency)} / ${fmtMs(m.baseline_p95_latency)}`} hint={`${m.baseline_requests} requests`} />
            <MetricCard label="Fault P50 / P95" value={`${fmtMs(m.p50_latency)} / ${fmtMs(m.p95_latency)}`} hint={`${m.total_requests} requests`} />
            <MetricCard label="Success / error rate" value={`${fmtPct(m.success_rate)} / ${fmtPct(m.error_rate)}`} />
            <MetricCard label="Recovery · fallback" value={`${fmtSeconds(m.recovery_time)} · ${fmtPct(m.fallback_score)}`} />
          </div>
          <section className="card"><ScoreBreakdown metrics={m} /></section>
        </>)}

        <section className="card"><h2 className="mb-2">Observed failures</h2>
          {failed.length === 0 ? <p className="text-xs text-ink2">No failed requests during the fault period.</p> :
            <p className="text-xs text-ink2">{failed.length} failed requests. Status distribution: <span className="mono">{JSON.stringify(data.status_distribution)}</span></p>}</section>

        <section className="card"><h2 className="mb-2">AI diagnosis</h2>
          {data.analyses.length ? <AnalysisPanel analysis={data.analyses[0]} /> :
            <EmptyState title="No AI analysis yet" action={<Link className="btn" to={`/experiments/${id}/analysis`}>Analyse with Gemma</Link>} />}</section>

        <section className="card"><h2 className="mb-2">Suggested fixes</h2>
          {data.fixes.length ? <ul className="text-xs text-ink2">{data.fixes.map((f) => <li key={f.id}>Fix #{f.id}: <span className="text-ink">{f.status}</span> {f.developer_notes && `— ${f.developer_notes}`}</li>)}</ul>
            : <p className="text-xs text-ink2">None.</p>}</section>

        <section className="card space-y-4"><h2>Retest results</h2>
          {data.retests.length === 0 && <p className="text-xs text-ink2">No retests yet.</p>}
          {data.retests.map((r) => (
            <div key={r.experiment.id}><div className="mb-2 text-xs">Retest <Link className="mono text-accent" to={`/experiments/${r.experiment.id}/report`}>{r.experiment.id}</Link> on {r.experiment.target_name}</div>
              {r.comparison ? <ComparisonTable result={r.comparison} /> : <p className="text-xs text-ink2">No measurements to compare.</p>}</div>))}
        </section>

        <section className="card"><h2 className="mb-3">Timeline</h2><EventTimeline events={data.timeline} /></section>
        <p className="text-xs text-muted">{data.disclaimer}</p>
      </div>
    </>
  );
}
