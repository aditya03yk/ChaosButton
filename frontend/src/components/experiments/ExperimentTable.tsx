import { Link } from "react-router-dom";
import { FAULT_LABELS, fmtDateTime, fmtScore } from "../../lib/format";
import type { Experiment } from "../../types/experiment";
import StatusBadge from "../common/StatusBadge";

interface Props { items: Experiment[]; selected?: string[]; onToggle?: (id: string) => void }

export default function ExperimentTable({ items, selected, onToggle }: Props) {
  return (
    <div className="overflow-x-auto">
      <table className="table">
        <thead><tr>
          {onToggle && <th />}<th>Experiment</th><th>Target</th><th>Fault</th><th>Date</th><th>Status</th><th>Score</th><th />
        </tr></thead>
        <tbody>
          {items.map((e) => (
            <tr key={e.id}>
              {onToggle && <td><input type="checkbox" aria-label={`Select ${e.id}`} checked={selected?.includes(e.id)} onChange={() => onToggle(e.id)} /></td>}
              <td className="mono">{e.id}</td><td>{e.target_name}</td><td>{FAULT_LABELS[e.fault_type]}</td>
              <td className="text-ink2">{fmtDateTime(e.created_at)}</td><td><StatusBadge status={e.status} /></td>
              <td className="mono">{fmtScore(e.metrics?.resilience_score)}</td>
              <td><Link className="text-accent hover:underline" to={`/experiments/${e.id}/report`}>View report</Link></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
