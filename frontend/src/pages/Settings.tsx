import ErrorState from "../components/common/ErrorState";
import LoadingState from "../components/common/LoadingState";
import PageHeader from "../components/common/PageHeader";
import { useAsync } from "../hooks/useAsync";
import { getAIStatus, getConfig } from "../services/reportService";

export default function Settings() {
  const config = useAsync(getConfig);
  const ai = useAsync(getAIStatus);
  if (config.loading) return <LoadingState />;
  if (config.error || !config.data) return <ErrorState message={config.error ?? "No data"} onRetry={config.reload} />;
  const c = config.data;

  return (
    <>
      <PageHeader title="Settings" subtitle="Read-only. Change values in the backend .env file and restart." />
      <div className="grid gap-4 lg:grid-cols-2">
        <section className="card space-y-2">
          <h2>Gemma / Ollama</h2>
          <div className="text-xs">Model <span className="mono">{c.ollama_model}</span> at <span className="mono">{c.ollama_base_url}</span></div>
          {ai.data && <div className={`text-xs ${ai.data.reachable && ai.data.model_available ? "text-ok" : "text-bad"}`}>{ai.data.message} {ai.data.hint}</div>}
          <button className="btn" onClick={ai.reload}>Retry connection check</button>
          <p className="text-xs text-muted">Setup: <span className="mono">ollama serve</span> then <span className="mono">ollama pull {c.ollama_model}</span></p>
        </section>
        <section className="card">
          <h2 className="mb-2">Hard safety limits</h2>
          <table className="table"><tbody>{Object.entries(c.limits).map(([k, v]) => <tr key={k}><td className="mono">{k}</td><td className="mono">{v}</td></tr>)}</tbody></table>
        </section>
        <section className="card text-xs">
          <h2 className="mb-2">Targets and upstream</h2>
          <div>Allowed remote hosts: <span className="mono">{c.allowed_remote_hosts.join(", ") || "none (loopback only)"}</span></div>
          <div className="mt-1">Demo upstream: <span className="mono">{c.upstream_url}</span></div>
          <div className="mt-1">Environment: {c.app_env}</div>
        </section>
      </div>
    </>
  );
}
