import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ErrorDistributionChart, OutcomeChart, VolumeChart } from "../components/charts/DistributionCharts";
import LatencyChart from "../components/charts/LatencyChart";
import EmptyState from "../components/common/EmptyState";
import ErrorState from "../components/common/ErrorState";
import LoadingState from "../components/common/LoadingState";
import MetricCard from "../components/common/MetricCard";
import PageHeader from "../components/common/PageHeader";
import StatusBadge from "../components/common/StatusBadge";
import TargetSelector from "../components/experiments/TargetSelector";
import ScoreBreakdown from "../components/reports/ScoreBreakdown";
import { useAsync } from "../hooks/useAsync";
import { FAULT_LABELS, fmtMs, fmtPct, fmtSeconds } from "../lib/format";
import { retest, startExperiment } from "../services/experimentService";
import { getReport } from "../services/reportService";
import { listTargets } from "../services/targetService";

export default function Results() {
  const { id = "" } = useParams();
  const navigate = useNavigate();
  const report = useAsync(() => getReport(id), [id]);
  const targets = useAsync(listTargets);
  const [retestTarget, setRetestTarget] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  if (report.loading && !report.data) return <LoadingState />;
  if (report.error || !report.data) return <ErrorState message={report.error ?? "Not found"} onRetry={report.reload} />;
  const { experiment: exp, metrics: m } = report.data;
  const requests = report.data.request_events;

  const rerun = async () => {
    try {
      const next = await retest(id, retestTarget ?? undefined);
      await startExperiment(next.id);
      navigate(`/experiments/${next.id}/live`);
    } catch (e) { setError((e as Error).message); }
  };

  return (
    <>
      <PageHeader title={`${FAULT_LABELS[exp.fault_type]} results`} subtitle={`${exp.id} · ${exp.target_name} · ${exp.route}`} actions={<>
        <Link className="btn btn-primary" to={`/experiments/${id}/analysis`}>Analyse with Gemma</Link>
        <Link className="btn" to={`/experiments/${id}/fixes`}>Fix workspace</Link>
        <Link className="btn" to={`/experiments/${id}/report`}>Full report</Link>
      </>} />
      <div className="mb-4"><StatusBadge status={exp.status} />{exp.error_message && <span className="ml-3 text-xs text-warn">{exp.error_message}</span>}</div>
      {!m ? <EmptyState title="No measurements" text="This experiment recorded no fault-period requests." /> : (
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <MetricCard label="Success rate" value={fmtPct(m.success_rate)} tone={m.success_rate === 100 ? "ok" : "warn"} />
            <MetricCard label="Error rate" value={fmtPct(m.error_rate)} tone={m.error_rate ? "bad" : "default"} />
            <MetricCard label="P50 / P95 latency" value={`${fmtMs(m.p50_latency)} / ${fmtMs(m.p95_latency)}`} hint={`baseline p95 ${fmtMs(m.baseline_p95_latency)}`} />
            <MetricCard label="Recovery time" value={fmtSeconds(m.recovery_time)} />
          </div>
          <div className="grid gap-4 lg:grid-cols-2">
            <section className="card"><ScoreBreakdown metrics={m} /></section>
            <section className="card"><h2 className="mb-2">Latency over time</h2><LatencyChart requests={requests} /></section>
            <section className="card"><h2 className="mb-2">Success vs failure</h2><OutcomeChart successful={m.successful_requests} failed={m.failed_requests} /></section>
            <section className="card"><h2 className="mb-2">Status distribution</h2><ErrorDistributionChart counts={report.data.status_distribution} /></section>
            <section className="card lg:col-span-2"><h2 className="mb-2">Request volume</h2><VolumeChart requests={requests} /></section>
          </div>
        </div>
      )}
      <section className="card mt-4 max-w-xl space-y-3">
        <h2>Retest</h2>
        <p className="text-xs text-ink2">Reruns the identical experiment as a new run. Optionally switch the target (for example to the resilient demo shop).</p>
        {targets.data && <TargetSelector targets={targets.data} value={retestTarget} onChange={setRetestTarget} label="Retest on (optional)" />}
        {error && <div role="alert" className="text-xs text-bad">{error}</div>}
        <button className="btn" onClick={rerun}>Rerun this experiment</button>
      </section>
    </>
  );
}
