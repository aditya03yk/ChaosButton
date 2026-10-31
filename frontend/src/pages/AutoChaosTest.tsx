import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Link } from "react-router-dom";
import ErrorState from "../components/common/ErrorState";
import LoadingState from "../components/common/LoadingState";
import MetricCard from "../components/common/MetricCard";
import PageHeader from "../components/common/PageHeader";
import StatusBadge from "../components/common/StatusBadge";
import LivePanel from "../components/experiments/LivePanel";
import TargetSelector from "../components/experiments/TargetSelector";
import { useAsync } from "../hooks/useAsync";
import { FAULT_LABELS, fmtPct, fmtScore } from "../lib/format";
import { getSuite, startSuite, stopSuite } from "../services/experimentService";
import { listTargets } from "../services/targetService";
import { FaultScope, TERMINAL } from "../types/experiment";

const SCENARIOS = ["Latency (500 ms)", "Timeout (2000 ms)", "HTTP 503"];

function SuiteView({ suiteId }: { suiteId: string }) {
  const suite = useAsync(() => getSuite(suiteId), [suiteId]);
  const [stopError, setStopError] = useState<string | null>(null);
  const finished = suite.data?.finished ?? false;

  useEffect(() => {
    if (finished) return;
    const timer = setInterval(() => void suite.reload(), 1000);
    return () => clearInterval(timer);
  }, [finished, suite.reload]);

  if (suite.error) return <ErrorState message={suite.error} onRetry={suite.reload} />;
  if (!suite.data) return <LoadingState />;
  const { experiments, consolidated } = suite.data;
  const current = experiments.find((e) => !TERMINAL.includes(e.status) && e.status !== "CREATED")
    ?? experiments.find((e) => !TERMINAL.includes(e.status)) ?? experiments[experiments.length - 1];

  return (
    <div className="space-y-4">
      <section className="card">
        <div className="mb-3 flex items-center justify-between">
          <h2>Test suite <span className="mono text-muted">{suiteId}</span></h2>
          {!finished && <button className="btn btn-danger" onClick={() => stopSuite(suiteId).catch((e: Error) => setStopError(e.message))}>Stop suite</button>}
        </div>
        {stopError && <div role="alert" className="mb-2 text-xs text-bad">{stopError}</div>}
        <table className="table">
          <thead><tr><th>Scenario</th><th>Status</th><th>Requests</th><th>Error rate</th><th>Score</th><th /></tr></thead>
          <tbody>{experiments.map((e) => (
            <tr key={e.id} className={e.id === current.id && !finished ? "bg-surface2" : ""}>
              <td>{FAULT_LABELS[e.fault_type]}</td><td><StatusBadge status={e.status} /></td>
              <td className="mono">{e.metrics?.total_requests ?? "–"}</td><td className="mono">{fmtPct(e.metrics?.error_rate)}</td>
              <td className="mono">{fmtScore(e.metrics?.resilience_score)}</td>
              <td><Link className="text-accent hover:underline" to={`/experiments/${e.id}/results`}>Results</Link></td>
            </tr>))}
          </tbody>
        </table>
      </section>

      {finished && (
        <section className="card">
          <h2 className="mb-3">Consolidated report</h2>
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <MetricCard label="Scenarios completed" value={`${consolidated.scenarios_completed}/${consolidated.scenarios_total}`} />
            <MetricCard label="Avg success rate" value={fmtPct(consolidated.average_success_rate)} />
            <MetricCard label="Avg resilience score" value={fmtScore(consolidated.average_resilience_score)} />
            <MetricCard label="Weakest scenario" value={consolidated.weakest_scenario ? FAULT_LABELS[consolidated.weakest_scenario] : "n/a"} />
          </div>
          <p className="mt-3 text-xs text-ink2">Open a scenario's results to analyse it with Gemma, apply a fix and retest.</p>
        </section>
      )}
      <LivePanel key={current.id} experimentId={current.id} />
    </div>
  );
}

export default function AutoChaosTest() {
  const { suiteId } = useParams();
  const navigate = useNavigate();
  const targets = useAsync(listTargets);
  const [targetId, setTargetId] = useState<number | null>(null);
  const [route, setRoute] = useState("/product");
  const [scope, setScope] = useState<FaultScope>("inbound");
  const [depRoute, setDepRoute] = useState("/inventory");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  if (suiteId) return <><PageHeader title="Auto Chaos Test" subtitle="Latency, timeout and HTTP 503 scenarios run one after another." /><SuiteView suiteId={suiteId} /></>;

  const start = async () => {
    if (targetId === null) return setError("Select a target first.");
    setBusy(true);
    try {
      const suite = await startSuite({ target_id: targetId, route, method: "GET", scope, dependency_route: scope === "dependency" ? depRoute : null });
      navigate(`/auto/${suite.suite_id}`);
    } catch (e) { setError((e as Error).message); setBusy(false); }
  };

  return (
    <>
      <PageHeader title="Auto Chaos Test" subtitle="One click runs a bounded suite: latency, timeout and HTTP 503." />
      <div className="grid gap-4 lg:grid-cols-[1fr_320px]">
        <section className="card space-y-4">
          {targets.data && <TargetSelector targets={targets.data} value={targetId} onChange={setTargetId} />}
          {targets.error && <ErrorState message={targets.error} onRetry={targets.reload} />}
          <div className="grid gap-3 sm:grid-cols-2">
            <div><label className="label" htmlFor="a-route">Route to exercise</label><input id="a-route" className="input" value={route} onChange={(e) => setRoute(e.target.value)} /></div>
            <div><label className="label" htmlFor="a-scope">Injection point</label>
              <select id="a-scope" className="input" value={scope} onChange={(e) => setScope(e.target.value as FaultScope)}>
                <option value="inbound">Inbound requests</option><option value="dependency">Upstream dependency calls</option></select></div>
            {scope === "dependency" && <div><label className="label" htmlFor="a-dep">Dependency route</label><input id="a-dep" className="input" value={depRoute} onChange={(e) => setDepRoute(e.target.value)} /></div>}
          </div>
          <button type="button" className="btn text-xs" onClick={() => { setRoute("/product"); setScope("dependency"); setDepRoute("/inventory"); }}>Use demo shop preset</button>
          {error && <div role="alert" className="text-xs text-bad">{error}</div>}
          <button className="btn btn-primary" disabled={busy} onClick={start}>{busy ? "Starting…" : "Start Auto Chaos Test"}</button>
        </section>
        <section className="card">
          <h2 className="mb-2">Suite</h2>
          <ol className="list-decimal space-y-1 pl-5 text-xs text-ink2">{SCENARIOS.map((s) => <li key={s}>{s}, max 10 affected requests</li>)}</ol>
          <p className="mt-3 text-xs text-muted">Each scenario captures a baseline, injects the fault, removes it and observes recovery. Bounds are enforced by the backend.</p>
        </section>
      </div>
    </>
  );
}
