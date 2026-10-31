import { Copy } from "lucide-react";
import type { Analysis } from "../../types/analysis";
import CodeBlock from "../common/CodeBlock";
import SeverityBadge from "../common/SeverityBadge";

function List({ title, items }: { title: string; items: string[] }) {
  return (
    <div><h2 className="mb-1">{title}</h2><ul className="list-disc space-y-0.5 pl-5 text-xs text-ink2">{items.map((i) => <li key={i}>{i}</li>)}</ul></div>
  );
}

export default function AnalysisPanel({ analysis }: { analysis: Analysis }) {
  const recommendation = analysis.recommended_actions.map((a) => `- ${a}`).join("\n");
  return (
    <article className="card space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2"><SeverityBadge severity={analysis.severity} /><h2 className="text-base">{analysis.finding}</h2></div>
        <span className="mono text-muted">{analysis.model_name}</span>
      </div>
      <div className="rounded border border-warn/50 bg-warn/10 px-3 py-1.5 text-xs font-medium text-warn">AI-GENERATED PROPOSAL — HUMAN REVIEW REQUIRED</div>
      <p className="text-xs text-ink2"><span className="text-ink">Severity rationale: </span>{analysis.severity_rationale}</p>
      {analysis.what_happened && <p className="text-xs text-ink2"><span className="text-ink">What happened: </span>{analysis.what_happened}</p>}
      {analysis.user_impact && <p className="text-xs text-ink2"><span className="text-ink">User impact: </span>{analysis.user_impact}</p>}
      <List title="Evidence" items={analysis.evidence} />
      <p className="text-xs text-ink2"><span className="text-ink">Likely cause (hypothesis): </span>{analysis.likely_cause}</p>
      <div>
        <div className="mb-1 flex items-center justify-between"><h2>Recommended actions</h2>
          <button className="btn px-2 py-0.5 text-xs" onClick={() => navigator.clipboard.writeText(recommendation)}><Copy size={12} /> Copy recommendation</button></div>
        <ul className="list-disc space-y-0.5 pl-5 text-xs text-ink2">{analysis.recommended_actions.map((a) => <li key={a}>{a}</li>)}</ul>
      </div>
      <CodeBlock code={analysis.code_example.snippet} language={analysis.code_example.language} />
      {analysis.code_example.assumptions && <p className="text-xs text-muted">Assumptions: {analysis.code_example.assumptions}</p>}
      <List title="Verification steps" items={analysis.verification_steps} />
    </article>
  );
}
