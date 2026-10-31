import type { Target } from "../../types/target";

interface Props { targets: Target[]; value: number | null; onChange: (id: number) => void; label?: string }

export default function TargetSelector({ targets, value, onChange, label = "Target application" }: Props) {
  return (
    <div>
      <label className="label" htmlFor="target-select">{label}</label>
      <select id="target-select" className="input" value={value ?? ""} onChange={(e) => onChange(Number(e.target.value))}>
        <option value="" disabled>Select a target…</option>
        {targets.map((t) => <option key={t.id} value={t.id}>{t.name} — {t.base_url}</option>)}
      </select>
    </div>
  );
}
