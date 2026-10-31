import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { RequestEvent } from "../../types/experiment";

const COLORS = { baseline: "#6599D8", fault: "#E45D5D", recovery: "#42B883" };

export default function LatencyChart({ requests }: { requests: RequestEvent[] }) {
  const data = requests.map((r, i) => ({
    n: i + 1,
    baseline: r.phase === "baseline" ? r.latency_ms : null,
    fault: r.phase === "fault" ? r.latency_ms : null,
    recovery: r.phase === "recovery" ? r.latency_ms : null,
  }));
  return (
    <ResponsiveContainer width="100%" height={220}>
      <LineChart data={data}>
        <CartesianGrid stroke="#293038" vertical={false} />
        <XAxis dataKey="n" stroke="#68727D" fontSize={11} />
        <YAxis stroke="#68727D" fontSize={11} unit=" ms" width={60} />
        <Tooltip contentStyle={{ background: "#15191D", border: "1px solid #293038", fontSize: 12 }} />
        {(Object.keys(COLORS) as (keyof typeof COLORS)[]).map((k) => (
          <Line key={k} dataKey={k} stroke={COLORS[k]} dot={{ r: 2 }} isAnimationActive={false} connectNulls={false} />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}
