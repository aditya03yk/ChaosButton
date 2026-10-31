const STYLES: Record<string, string> = {
  COMPLETED: "text-ok", RUNNING: "text-accent", BASELINE: "text-info", VALIDATING: "text-info",
  RECOVERING: "text-info", STOPPED: "text-warn", FAILED: "text-bad", CREATED: "text-ink2",
};

export default function StatusBadge({ status }: { status: string }) {
  return (
    <span className={`inline-flex items-center gap-1.5 text-xs font-medium ${STYLES[status] ?? "text-ink2"}`}>
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      {status}
    </span>
  );
}
