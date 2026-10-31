import { useState } from "react";
import type { ExperimentInput, FaultScope, FaultType } from "../../types/experiment";
import type { Target } from "../../types/target";
import FaultSelector from "../faults/FaultSelector";
import TargetSelector from "./TargetSelector";

interface Props { targets: Target[]; limits: Record<string, number>; submitting: boolean; onSubmit: (input: ExperimentInput) => void }

const LATENCY_PRESETS = [100, 250, 500, 1000];

export default function ExperimentForm({ targets, limits, submitting, onSubmit }: Props) {
  const [targetId, setTargetId] = useState<number | null>(null);
  const [route, setRoute] = useState("/product");
  const [method, setMethod] = useState("GET");
  const [fault, setFault] = useState<FaultType>("latency");
  const [scope, setScope] = useState<FaultScope>("inbound");
  const [depRoute, setDepRoute] = useState("/inventory");
  const [delay, setDelay] = useState(500);
  const [timeoutMs, setTimeoutMs] = useState(2000);
  const [duration, setDuration] = useState(30);
  const [maxAffected, setMaxAffected] = useState(10);
  const [notes, setNotes] = useState("");
  const [errors, setErrors] = useState<string[]>([]);

  const max = (key: string, fallback: number) => limits[key] ?? fallback;

  const validate = (): string[] => {
    const found: string[] = [];
    if (targetId === null) found.push("Select a target.");
    if (!route.startsWith("/") || route === "/") found.push("Route must start with '/' and be narrower than '/'.");
    if (scope === "dependency" && !depRoute.startsWith("/")) found.push("Dependency route must start with '/'.");
    if (fault === "latency" && (delay < 1 || delay > max("max_injected_delay_ms", 5000))) found.push(`Delay must be 1–${max("max_injected_delay_ms", 5000)} ms.`);
    if (fault === "timeout" && (timeoutMs < 1 || timeoutMs > max("max_injected_delay_ms", 5000))) found.push(`Timeout must be 1–${max("max_injected_delay_ms", 5000)} ms.`);
    if (duration < 1 || duration > max("max_experiment_duration", 120)) found.push(`Duration must be 1–${max("max_experiment_duration", 120)} s.`);
    if (maxAffected < 1 || maxAffected > max("max_affected_requests", 100)) found.push(`Maximum affected requests must be 1–${max("max_affected_requests", 100)}.`);
    return found;
  };

  const submit = () => {
    const found = validate();
    setErrors(found);
    if (found.length || targetId === null) return;
    onSubmit({
      target_id: targetId, route, method, fault_type: fault, notes,
      fault_configuration: {
        scope, dependency_route: scope === "dependency" ? depRoute : null, duration_s: duration, max_affected: maxAffected,
        delay_ms: fault === "latency" ? delay : null, timeout_ms: fault === "timeout" ? timeoutMs : null,
      },
    });
  };

  return (
    <div className="space-y-4">
      <TargetSelector targets={targets} value={targetId} onChange={setTargetId} />
      <div className="grid gap-3 sm:grid-cols-[1fr_120px]">
        <div><label className="label" htmlFor="route">Target route</label><input id="route" className="input" value={route} onChange={(e) => setRoute(e.target.value)} /></div>
        <div><label className="label" htmlFor="method">HTTP method</label>
          <select id="method" className="input" value={method} onChange={(e) => setMethod(e.target.value)}>
            {["GET", "POST", "PUT", "PATCH", "DELETE"].map((m) => <option key={m}>{m}</option>)}
          </select></div>
      </div>
      <FaultSelector value={fault} onChange={setFault} />
      <div className="grid gap-3 sm:grid-cols-2">
        <div><label className="label" htmlFor="scope">Injection point</label>
          <select id="scope" className="input" value={scope} onChange={(e) => setScope(e.target.value as FaultScope)}>
            <option value="inbound">Inbound: requests to the target route</option>
            <option value="dependency">Dependency: the target's upstream calls</option>
          </select></div>
        {scope === "dependency" && (
          <div><label className="label" htmlFor="dep">Dependency route</label><input id="dep" className="input" value={depRoute} onChange={(e) => setDepRoute(e.target.value)} /></div>
        )}
      </div>
      <div className="grid gap-3 sm:grid-cols-3">
        {fault === "latency" && (
          <div><label className="label" htmlFor="delay">Delay (ms)</label>
            <input id="delay" type="number" className="input" value={delay} onChange={(e) => setDelay(Number(e.target.value))} />
            <div className="mt-1 flex gap-1">{LATENCY_PRESETS.map((p) => <button key={p} type="button" className="btn px-1.5 py-0.5 text-xs" onClick={() => setDelay(p)}>{p}</button>)}</div></div>
        )}
        {fault === "timeout" && (
          <div><label className="label" htmlFor="timeout">Timeout threshold (ms)</label><input id="timeout" type="number" className="input" value={timeoutMs} onChange={(e) => setTimeoutMs(Number(e.target.value))} /></div>
        )}
        <div><label className="label" htmlFor="duration">Duration (s)</label><input id="duration" type="number" className="input" value={duration} onChange={(e) => setDuration(Number(e.target.value))} /></div>
        <div><label className="label" htmlFor="cap">Max affected requests</label><input id="cap" type="number" className="input" value={maxAffected} onChange={(e) => setMaxAffected(Number(e.target.value))} /></div>
      </div>
      <div><label className="label" htmlFor="notes">Notes (optional)</label><textarea id="notes" className="input" rows={2} value={notes} onChange={(e) => setNotes(e.target.value)} /></div>

      <div className="rounded border border-line bg-bg p-3 text-xs text-ink2">
        <div className="mb-1 font-medium text-ink">Scope and safety limits</div>
        {fault} fault on <span className="mono">{scope === "dependency" ? depRoute : route}</span> ({scope}) · at most {maxAffected} requests ·
        expires after {duration}s · hard limits: {max("max_affected_requests", 100)} requests, {max("max_experiment_duration", 120)}s, {max("max_injected_delay_ms", 5000)} ms.
        Only this route is affected; the experiment can be stopped at any time.
      </div>
      {errors.length > 0 && <ul role="alert" className="list-disc pl-5 text-xs text-bad">{errors.map((e) => <li key={e}>{e}</li>)}</ul>}
      <button className="btn btn-primary" disabled={submitting} onClick={submit}>{submitting ? "Starting…" : "Create and start experiment"}</button>
    </div>
  );
}
