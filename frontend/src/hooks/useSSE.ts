import { useEffect, useRef, useState } from "react";
import { openExperimentStream, StreamHandlers } from "../services/eventService";

/** Subscribes to an experiment stream while `enabled`; reports connection state. */
export function useSSE(experimentId: string | undefined, enabled: boolean, handlers: StreamHandlers) {
  const [connected, setConnected] = useState(false);
  const latest = useRef(handlers);
  latest.current = handlers;

  useEffect(() => {
    if (!experimentId || !enabled) return;
    const close = openExperimentStream(experimentId, {
      status: (d) => latest.current.status?.(d),
      request: (d) => latest.current.request?.(d),
      metrics: (d) => latest.current.metrics?.(d),
      timeline: (d) => latest.current.timeline?.(d),
      onConnection: setConnected,
    });
    return () => { close(); setConnected(false); };
  }, [experimentId, enabled]);

  return connected;
}
