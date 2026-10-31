import type { FaultType } from "../../types/experiment";

const FAULTS: { id: FaultType; title: string; text: string }[] = [
  { id: "latency", title: "Latency", text: "Delay matching requests, then forward them." },
  { id: "timeout", title: "Timeout", text: "Hold requests past a threshold, then fail with 504." },
  { id: "http_500", title: "HTTP 500", text: "Answer matching requests with a server error." },
  { id: "http_503", title: "HTTP 503", text: "Answer matching requests with service unavailable." },
];

export default function FaultSelector({ value, onChange }: { value: FaultType; onChange: (f: FaultType) => void }) {
  return (
    <fieldset>
      <legend className="label">Fault type</legend>
      <div className="grid gap-2 sm:grid-cols-2">
        {FAULTS.map((f) => (
          <label key={f.id} className={`cursor-pointer rounded border p-3 transition-colors ${
            value === f.id ? "border-accent bg-surface2" : "border-line hover:border-ink2"}`}>
            <input type="radio" name="fault" className="sr-only" checked={value === f.id} onChange={() => onChange(f.id)} />
            <div className="font-medium">{f.title}</div>
            <div className="text-xs text-ink2">{f.text}</div>
          </label>
        ))}
      </div>
    </fieldset>
  );
}
