import { Area, AreaChart, Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { parseUtc } from "../../lib/format";
import type { RequestEvent } from "../../types/experiment";

const AXIS = { stroke: "#68727D", fontSize: 11 };
const TOOLTIP = { contentStyle: { background: "#15191D", border: "1px solid #293038", fontSize: 12 } };

/** HTTP status code distribution (counts supplied by the backend). */
export function ErrorDistributionChart({ counts }: { counts: Record<string, number> }) {
  const data = Object.entries(counts).map(([status, count]) => ({ status, count }));
  return (
    <ResponsiveContainer width="100%" height={180}>
      <BarChart data={data}>
        <CartesianGrid stroke="#293038" vertical={false} />
        <XAxis dataKey="status" {...AXIS} /><YAxis allowDecimals={false} {...AXIS} width={30} />
        <Tooltip {...TOOLTIP} />
        <Bar dataKey="count" fill="#6599D8" isAnimationActive={false} />
      </BarChart>
    </ResponsiveContainer>
  );
}

/** Success vs failure totals (counts supplied by the backend). */
export function OutcomeChart({ successful, failed }: { successful: number; failed: number }) {
  const data = [{ name: "Success", value: successful, fill: "#42B883" }, { name: "Failure", value: failed, fill: "#E45D5D" }];
  return (
    <ResponsiveContainer width="100%" height={180}>
      <BarChart data={data}>
        <CartesianGrid stroke="#293038" vertical={false} />
        <XAxis dataKey="name" {...AXIS} /><YAxis allowDecimals={false} {...AXIS} width={30} />
        <Tooltip {...TOOLTIP} />
        <Bar dataKey="value" isAnimationActive={false} />
      </BarChart>
    </ResponsiveContainer>
  );
}

/** Requests per second, bucketed from the recorded event timestamps. */
export function VolumeChart({ requests }: { requests: RequestEvent[] }) {
  const start = requests.length ? parseUtc(requests[0].timestamp).getTime() : 0;
  const buckets: Record<number, number> = {};
  requests.forEach((r) => {
    const s = Math.floor((parseUtc(r.timestamp).getTime() - start) / 1000);
    buckets[s] = (buckets[s] ?? 0) + 1;
  });
  const data = Object.entries(buckets).map(([second, count]) => ({ second: Number(second), count }));
  return (
    <ResponsiveContainer width="100%" height={180}>
      <AreaChart data={data}>
        <CartesianGrid stroke="#293038" vertical={false} />
        <XAxis dataKey="second" unit="s" {...AXIS} /><YAxis allowDecimals={false} {...AXIS} width={30} />
        <Tooltip {...TOOLTIP} />
        <Area dataKey="count" stroke="#D6A84F" fill="#D6A84F33" isAnimationActive={false} />
      </AreaChart>
    </ResponsiveContainer>
  );
}
