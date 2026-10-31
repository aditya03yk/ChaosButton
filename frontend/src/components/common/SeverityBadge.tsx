import type { Severity } from "../../types/analysis";

const STYLES: Record<Severity, string> = {
  critical: "border-bad text-bad", high: "border-warn text-warn",
  medium: "border-info text-info", low: "border-ok text-ok",
};

export default function SeverityBadge({ severity }: { severity: Severity }) {
  return <span className={`rounded border px-1.5 py-0.5 text-xs uppercase ${STYLES[severity]}`}>{severity}</span>;
}
