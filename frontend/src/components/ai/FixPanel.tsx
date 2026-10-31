import { useState } from "react";
import { Link } from "react-router-dom";
import { updateFix } from "../../services/experimentService";
import type { FixItem, FixStatus } from "../../types/analysis";
import CodeBlock from "../common/CodeBlock";
import SeverityBadge from "../common/SeverityBadge";

const ORDER: FixStatus[] = ["proposed", "reviewed", "applied", "verified"];
const NEXT_LABEL: Record<string, string> = { proposed: "Mark as reviewed", reviewed: "Mark as applied (I changed my code)", applied: "Mark as verified" };

interface Props { item: FixItem; route: string; onChanged: () => void; onRetest: () => void }

/** Fix workspace entry. Status changes are manual developer actions; ChaosButton never edits target code. */
export default function FixPanel({ item, route, onChanged, onRetest }: Props) {
  const { fix, analysis } = item;
  const [notes, setNotes] = useState(fix.developer_notes);
  const [error, setError] = useState<string | null>(null);
  const index = ORDER.indexOf(fix.status);

  const save = async (body: { status?: FixStatus; developer_notes?: string }) => {
    try { await updateFix(fix.id, body); setError(null); onChanged(); } catch (e) { setError((e as Error).message); }
  };

  return (
    <article className="card space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2"><SeverityBadge severity={analysis.severity} /><h2 className="text-base">{analysis.finding}</h2></div>
        <ol className="flex gap-1 text-[10px] uppercase">
          {ORDER.map((s, i) => <li key={s} className={`rounded border px-1.5 py-0.5 ${i <= index ? "border-accent text-accent" : "border-line text-muted"}`}>{s}</li>)}
        </ol>
      </div>
      <div className="mono text-muted">Affected route: {route}</div>
      <p className="text-xs text-ink2"><span className="text-ink">Likely cause: </span>{analysis.likely_cause}</p>
      <ul className="list-disc pl-5 text-xs text-ink2">{analysis.recommended_actions.map((a) => <li key={a}>{a}</li>)}</ul>
      <CodeBlock code={analysis.code_example.snippet} language={analysis.code_example.language} />
      <p className="text-xs text-muted">Assumptions: {analysis.code_example.assumptions || "none stated"}</p>
      <div className="text-xs text-ink2"><span className="text-ink">Verify: </span>{analysis.verification_steps.join(" → ")}</div>
      <div><label className="label" htmlFor={`notes-${fix.id}`}>Developer note</label>
        <textarea id={`notes-${fix.id}`} className="input" rows={2} value={notes} onChange={(e) => setNotes(e.target.value)} />
        <button className="btn mt-1" onClick={() => save({ developer_notes: notes })}>Save note</button></div>
      <div className="flex flex-wrap gap-2">
        {NEXT_LABEL[fix.status] && <button className="btn btn-primary" onClick={() => save({ status: ORDER[index + 1] })}>{NEXT_LABEL[fix.status]}</button>}
        <button className="btn" onClick={onRetest}>Rerun the original experiment</button>
        <Link className="btn" to={`/experiments/${fix.experiment_id}/analysis`}>Open analysis</Link>
      </div>
      {error && <div role="alert" className="text-xs text-bad">{error}</div>}
    </article>
  );
}
