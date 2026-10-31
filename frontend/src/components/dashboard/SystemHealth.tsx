import type { SystemStatus } from "../../types/system";

function Row({ label, ok, detail }: { label: string; ok: boolean; detail?: string }) {
  return (
    <li className="flex items-center justify-between py-1.5 text-xs">
      <span className="flex items-center gap-2"><span className={`h-1.5 w-1.5 rounded-full ${ok ? "bg-ok" : "bg-bad"}`} />{label}</span>
      <span className="text-ink2">{detail}</span>
    </li>
  );
}

export default function SystemHealth({ status }: { status: SystemStatus }) {
  const { ai } = status;
  return (
    <ul className="divide-y divide-line">
      <Row label="Backend" ok={status.backend === "ok"} detail={status.backend} />
      <Row label="Database" ok={status.database === "ok"} detail={status.database} />
      <Row label="Ollama" ok={ai.reachable} detail={ai.reachable ? "reachable" : "not reachable"} />
      <Row label="Gemma model" ok={ai.model_available} detail={ai.model} />
      <Row label="Active experiments" ok detail={String(status.active_experiments)} />
    </ul>
  );
}
