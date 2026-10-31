import { useState } from "react";
import ConfirmationDialog from "../components/common/ConfirmationDialog";
import EmptyState from "../components/common/EmptyState";
import ErrorState from "../components/common/ErrorState";
import LoadingState from "../components/common/LoadingState";
import PageHeader from "../components/common/PageHeader";
import { useAsync } from "../hooks/useAsync";
import { addDemoTargets, createTarget, deleteTarget, listTargets, revalidateTarget, updateTarget } from "../services/targetService";
import type { Target, TargetInput, ValidationResult } from "../types/target";

const BLANK: TargetInput = {
  name: "", base_url: "http://127.0.0.1:9001", description: "", technology_stack: "python_fastapi",
  environment_type: "local", notes: "", ownership_confirmed: false,
};
const STACKS = [["python_fastapi", "Python / FastAPI"], ["python_flask", "Python / Flask"], ["node_express", "Node.js / Express"],
  ["java_spring", "Java / Spring Boot"], ["other", "Other"]];
export default function Targets() {
  const { data, error, loading, reload } = useAsync(listTargets);
  const [form, setForm] = useState<TargetInput>(BLANK);
  const [editing, setEditing] = useState<number | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [results, setResults] = useState<Record<number, ValidationResult>>({});
  const [removing, setRemoving] = useState<Target | null>(null);

  const set = <K extends keyof TargetInput>(key: K, value: TargetInput[K]) => setForm((f) => ({ ...f, [key]: value }));

  const submit = async () => {
    if (!form.name.trim()) return setFormError("Name is required.");
    if (!/^https?:\/\//.test(form.base_url)) return setFormError("Base URL must start with http:// or https://");
    try {
      editing ? await updateTarget(editing, form) : await createTarget(form);
      setForm(BLANK); setEditing(null); setFormError(null); await reload();
    } catch (e) { setFormError((e as Error).message); }
  };

  const addDemos = async () => {
    setFormError(null);
    try {
      await addDemoTargets();
      await reload();
    } catch (e) {
      setFormError((e as Error).message || "Could not add demo shops. Check that the backend and demo services are running.");
    }
  };

  const validate = async (id: number) => {
    try { const r = await revalidateTarget(id); setResults((prev) => ({ ...prev, [id]: r })); await reload(); }
    catch (e) { setFormError((e as Error).message); }
  };

  const remove = async () => {
    if (!removing) return;
    try { await deleteTarget(removing.id); await reload(); } catch (e) { setFormError((e as Error).message); }
    setRemoving(null);
  };

  return (
    <>
      <PageHeader title="Targets" subtitle="Applications you own or are authorised to test. Loopback addresses are allowed by default."
        actions={<button className="btn" onClick={addDemos}>Add demo shops</button>} />
      <div className="grid gap-4 lg:grid-cols-[1fr_340px]">
        <section className="card">
          {loading && !data ? <LoadingState /> : error ? <ErrorState message={error} onRetry={reload} /> :
            !data?.length ? <EmptyState title="No targets registered" text="Add a target or the two demo shops." /> : (
            <table className="table">
              <thead><tr><th>Name</th><th>URL</th><th>Env</th><th>Validation</th><th /></tr></thead>
              <tbody>{data.map((t) => {
                const r = results[t.id];
                return (
                  <tr key={t.id}>
                    <td>{t.name}</td><td className="mono">{t.base_url}</td><td className="text-ink2">{t.environment_type}</td>
                    <td className="text-xs">
                      {r ? (r.valid ? <span className="text-ok">Valid · {r.latency_ms} ms</span> : <span className="text-bad">{r.errors.join(" ")}</span>)
                        : t.last_validation_ok == null ? <span className="text-muted">Not validated</span>
                        : t.last_validation_ok ? <span className="text-ok">Valid</span> : <span className="text-bad">Failed</span>}
                      {r?.warnings.map((w) => <div key={w} className="text-warn">{w}</div>)}
                    </td>
                    <td className="space-x-1 whitespace-nowrap text-right">
                      <button className="btn px-2 py-0.5 text-xs" onClick={() => validate(t.id)}>Validate</button>
                      <button className="btn px-2 py-0.5 text-xs" onClick={() => { setEditing(t.id); setForm({ ...t }); }}>Edit</button>
                      <button className="btn btn-danger px-2 py-0.5 text-xs" onClick={() => setRemoving(t)}>Remove</button>
                    </td>
                  </tr>
                );
              })}</tbody>
            </table>
          )}
        </section>

        <section className="card space-y-3">
          <h2>{editing ? "Edit target" : "Add target"}</h2>
          <div><label className="label" htmlFor="t-name">Target name</label><input id="t-name" className="input" value={form.name} onChange={(e) => set("name", e.target.value)} /></div>
          <div><label className="label" htmlFor="t-url">Base URL</label><input id="t-url" className="input mono" value={form.base_url} onChange={(e) => set("base_url", e.target.value)} /></div>
          <div><label className="label" htmlFor="t-desc">Description</label><input id="t-desc" className="input" value={form.description} onChange={(e) => set("description", e.target.value)} /></div>
          <div><label className="label" htmlFor="t-stack">Technology stack</label>
            <select id="t-stack" className="input" value={form.technology_stack} onChange={(e) => set("technology_stack", e.target.value as TargetInput["technology_stack"])}>
              {STACKS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}</select></div>
          <div><label className="label" htmlFor="t-env">Environment</label>
            <select id="t-env" className="input" value={form.environment_type} onChange={(e) => set("environment_type", e.target.value as TargetInput["environment_type"])}>
              <option value="local">Local development</option><option value="staging">Authorised staging</option><option value="demo">Demo environment</option></select></div>
          <label className="flex items-start gap-2 text-xs text-ink2">
            <input type="checkbox" checked={form.ownership_confirmed} onChange={(e) => set("ownership_confirmed", e.target.checked)} />
            I own this application or am explicitly authorised to test it (required for remote hosts).
          </label>
          <div><label className="label" htmlFor="t-notes">Notes</label><textarea id="t-notes" className="input" rows={2} value={form.notes} onChange={(e) => set("notes", e.target.value)} /></div>
          {formError && <div role="alert" className="text-xs text-bad">{formError}</div>}
          <div className="flex gap-2">
            <button className="btn btn-primary" onClick={submit}>{editing ? "Save changes" : "Add target"}</button>
            {editing && <button className="btn" onClick={() => { setEditing(null); setForm(BLANK); }}>Cancel</button>}
          </div>
        </section>
      </div>
      <ConfirmationDialog open={!!removing} title="Remove target?" confirmLabel="Remove"
        message={`Remove "${removing?.name}"? Targets with experiment history cannot be removed.`}
        onConfirm={remove} onCancel={() => setRemoving(null)} />
    </>
  );
}
