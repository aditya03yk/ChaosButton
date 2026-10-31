import { API_BASE } from "./api";

export type StreamHandlers = Partial<Record<"status" | "request" | "metrics" | "timeline", (data: any) => void>> & {
  onConnection?: (connected: boolean) => void;
};

/** Opens the experiment SSE stream. EventSource reconnects automatically (Last-Event-ID replay). */
export function openExperimentStream(id: string, handlers: StreamHandlers): () => void {
  const source = new EventSource(`${API_BASE}/api/experiments/${id}/stream`);
  (["status", "request", "metrics", "timeline"] as const).forEach((name) => {
    source.addEventListener(name, (e) => handlers[name]?.(JSON.parse((e as MessageEvent).data)));
  });
  source.onopen = () => handlers.onConnection?.(true);
  source.onerror = () => handlers.onConnection?.(false);
  return () => source.close();
}
