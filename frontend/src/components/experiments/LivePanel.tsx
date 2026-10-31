import { useState } from "react";
import { Link } from "react-router-dom";
import { useExperiment } from "../../hooks/useExperiment";
import { FAULT_LABELS, fmtMs, fmtPct } from "../../lib/format";
import { stopExperiment } from "../../services/experimentService";
import { TERMINAL } from "../../types/experiment";
import { ErrorDistributionChart, OutcomeChart, VolumeChart } from "../charts/DistributionCharts";
import LatencyChart from "../charts/LatencyChart";
import ConfirmationDialog from "../common/ConfirmationDialog";
import EmptyState from "../common/EmptyState";
import ErrorState from "../common/ErrorState";
import LoadingState from "../common/LoadingState";
import MetricCard from "../common/MetricCard";
import StatusBadge from "../common/StatusBadge";
import EventTimeline from "./EventTimeline";
import ProgressIndicator from "./ProgressIndicator";

/** Live monitor: every number shown here is produced by the backend (SSE `metrics` events). */
export default function LivePanel({ experimentId }: { experimentId: string }) {
  const { experiment, requests, timeline, live, error, connected, streaming, refresh } = useExperiment(experimentId);
  const [confirmStop, setConfirmStop] = useState(false);
  const [stopError, setStopError] = useState<string | null>(null);

  if (error) return <ErrorState message={error} onRetry={refresh} />;
  if (!experiment) return <LoadingState label="Loading experiment…" />;

  const finished = TERMINAL.includes(experiment.status);
  const stop = async () => {
    setConfirmStop(false);
    try { await stopExperiment(experimentId); } catch (e) { setStopError((e as Error).message); }
  };

  return (
    <div className="space-y-4">
      <div className="card space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <div className="font-medium">{FAULT_LABELS[experiment.fault_type]} on <span className="mono">{experiment.route}</span></div>
            <div className="mono text-muted">{experiment.id} · {experiment.target_name}</div>
          </div>
          <div className="flex items-center gap-3">
            <StatusBadge status={experiment.status} />
            {!finished && <button className="btn btn-danger" onClick={() => setConfirmStop(true)}>Stop now</button>}
            {finished && <Link className="btn" to={`/experiments/${experiment.id}/results`}>View results</Link>}
          </div>
        </div>
        <ProgressIndicator status={experiment.status} />
        {experiment.error_message && <div className="text-xs text-warn">{experiment.error_message}</div>}
        {streaming && !connected && <div className="text-xs text-warn">Live stream disconnected, reconnecting…</div>}
        {stopError && <div role="alert" className="text-xs text-bad">{stopError}</div>}
      </div>

      {live ? (
        <div className="grid grid-cols-2 gap-3 md:grid-cols-5">
          <MetricCard label="Total requests" value={String(live.total)} />
          <MetricCard label="Successful" value={String(live.successful)} tone="ok" />
          <MetricCard label="Failed" value={String(live.failed)} tone={live.failed ? "bad" : "default"} />
          <MetricCard label="Error rate" value={fmtPct(live.error_rate)} tone={live.error_rate ? "bad" : "default"} />
          <MetricCard label="Timeouts" value={String(live.timeouts)} />
          <MetricCard label="Avg latency" value={fmtMs(live.average_latency)} />
          <MetricCard label="Median (P50)" value={fmtMs(live.p50_latency)} />
          <MetricCard label="P95 latency" value={fmtMs(live.p95_latency)} />
          <MetricCard label="Active faults" value={String(live.active_faults)} tone={live.active_faults ? "warn" : "default"} />
          <MetricCard label="Duration" value={`${live.duration_s}s`} />
        </div>
      ) : (
        <EmptyState title="Waiting for fault-period requests" text="Live metrics start once the fault is active." />
      )}

      <div className="grid gap-4 lg:grid-cols-2">
        <section className="card"><h2 className="mb-2">Latency over time</h2><LatencyChart requests={requests} /></section>
        <section className="card"><h2 className="mb-2">Request volume</h2><VolumeChart requests={requests} /></section>
        <section className="card"><h2 className="mb-2">Success vs failure</h2>
          <OutcomeChart successful={live?.successful ?? 0} failed={live?.failed ?? 0} /></section>
        <section className="card"><h2 className="mb-2">HTTP status distribution</h2>
          <ErrorDistributionChart counts={live?.status_counts ?? {}} /></section>
      </div>
      <section className="card"><h2 className="mb-3">Event timeline</h2><EventTimeline events={timeline} /></section>

      <ConfirmationDialog open={confirmStop} title="Stop experiment?" confirmLabel="Stop now"
        message="The kill switch removes the fault immediately and cancels the run. Collected data is kept."
        onConfirm={stop} onCancel={() => setConfirmStop(false)} />
    </div>
  );
}
