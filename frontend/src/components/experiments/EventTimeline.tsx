import { fmtTime } from "../../lib/format";
import type { TimelineEvent } from "../../types/experiment";
import EmptyState from "../common/EmptyState";

const TONE = { info: "text-info", success: "text-ok", warning: "text-warn", error: "text-bad" };

export default function EventTimeline({ events }: { events: TimelineEvent[] }) {
  if (!events.length) return <EmptyState title="No events yet" text="Events appear here as the experiment runs." />;
  return (
    <ol className="space-y-1.5">
      {events.map((e, i) => (
        <li key={e.id ?? i} className="flex gap-3 text-xs">
          <span className="mono w-20 shrink-0 text-muted">{fmtTime(e.timestamp)}</span>
          <span className={TONE[e.level]}>●</span>
          <span className="text-ink2">{e.message}</span>
        </li>
      ))}
    </ol>
  );
}
