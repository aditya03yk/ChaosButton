import { Menu } from "lucide-react";
import { useEffect } from "react";
import { useAsync } from "../../hooks/useAsync";
import { getSystemStatus } from "../../services/reportService";

function Dot({ ok }: { ok: boolean | null }) {
  return <span className={`h-1.5 w-1.5 rounded-full ${ok === null ? "bg-muted" : ok ? "bg-ok" : "bg-bad"}`} />;
}

export default function Topbar({ onMenu }: { onMenu: () => void }) {
  const { data, error, reload } = useAsync(getSystemStatus);
  useEffect(() => {
    const timer = setInterval(() => void reload(), 15000);
    return () => clearInterval(timer);
  }, [reload]);

  const backendOk = error ? false : data ? data.backend === "ok" : null;
  const ai = data?.ai;
  const aiOk = ai ? ai.reachable && ai.model_available : error ? false : null;
  return (
    <header className="flex h-11 items-center justify-between border-b border-line bg-bg px-4">
      <button className="btn lg:hidden" onClick={onMenu} aria-label="Toggle navigation"><Menu size={14} /></button>
      <div className="ml-auto flex items-center gap-4 text-xs text-ink2">
        <span className="flex items-center gap-1.5"><Dot ok={backendOk} /> Backend</span>
        <span className="flex items-center gap-1.5" title={ai?.hint ?? ai?.message}>
          <Dot ok={aiOk} /> Gemma <span className="mono text-muted">{ai?.model ?? ""}</span>
        </span>
      </div>
    </header>
  );
}
