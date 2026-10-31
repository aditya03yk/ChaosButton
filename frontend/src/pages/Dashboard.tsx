import { Link } from "react-router-dom";
import EmptyState from "../components/common/EmptyState";
import ErrorState from "../components/common/ErrorState";
import LoadingState from "../components/common/LoadingState";
import MetricCard from "../components/common/MetricCard";
import PageHeader from "../components/common/PageHeader";
import SystemHealth from "../components/dashboard/SystemHealth";
import EventTimeline from "../components/experiments/EventTimeline";
import ExperimentTable from "../components/experiments/ExperimentTable";
import { useAsync } from "../hooks/useAsync";
import { fmtPct, fmtScore } from "../lib/format";
import { getDashboard, getSystemStatus } from "../services/reportService";

export default function Dashboard() {
  const dash = useAsync(getDashboard);
  const system = useAsync(getSystemStatus);

  if (dash.loading && !dash.data) return <LoadingState />;
  if (dash.error || !dash.data) return <ErrorState message={dash.error ?? "No data"} onRetry={dash.reload} />;
  const d = dash.data;

  return (
    <>
      <PageHeader title="Overview" subtitle="Resilience testing environment" actions={<>
        <Link className="btn btn-primary" to="/auto">Start Auto Chaos Test</Link>
        <Link className="btn" to="/manual">Create Manual Test</Link>
        <Link className="btn" to="/targets">Connect a Target</Link>
        <Link className="btn" to="/experiments">Previous Reports</Link>
      </>} />
      <div className="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-6">
        <MetricCard label="Experiments" value={String(d.total_experiments)} />
        <MetricCard label="Requests tested" value={String(d.total_requests)} />
        <MetricCard label="Avg success rate" value={fmtPct(d.average_success_rate)} />
        <MetricCard label="Avg resilience score" value={fmtScore(d.average_resilience_score)} />
        <MetricCard label="Critical findings" value={String(d.critical_findings)} tone={d.critical_findings ? "bad" : "default"} />
        <MetricCard label="Last experiment" value={d.last_experiment_status ?? "none"} />
      </div>
      <div className="mt-5 grid gap-4 lg:grid-cols-3">
        <section className="card lg:col-span-2">
          <h2 className="mb-3">Recent experiments</h2>
          {d.recent_experiments.length
            ? <ExperimentTable items={d.recent_experiments} />
            : <EmptyState title="No experiments yet" text="Register a target, then run your first chaos test."
                action={<Link className="btn btn-primary" to="/targets">Connect a target</Link>} />}
        </section>
        <section className="card">
          <h2 className="mb-2">System health</h2>
          {system.data ? <SystemHealth status={system.data} /> : <LoadingState />}
          {system.data && !system.data.ai.reachable && <p className="mt-2 text-xs text-warn">{system.data.ai.hint}</p>}
        </section>
      </div>
      <section className="card mt-4"><h2 className="mb-3">Activity</h2><EventTimeline events={[...d.activity].reverse()} /></section>
    </>
  );
}
