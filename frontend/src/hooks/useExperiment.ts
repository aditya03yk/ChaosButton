import { useCallback, useEffect, useState } from "react";
import { getEvents, getExperiment } from "../services/experimentService";
import { ApiError } from "../services/api";
import { Experiment, RequestEvent, TERMINAL, TimelineEvent } from "../types/experiment";
import type { LiveMetrics } from "../types/metrics";
import { useSSE } from "./useSSE";

/**
 * Experiment state for monitor/result pages. Running experiments stream everything over SSE
 * (the server replays history on connect); finished ones are loaded once from the REST API.
 */
export function useExperiment(id: string | undefined) {
  const [experiment, setExperiment] = useState<Experiment | null>(null);
  const [requests, setRequests] = useState<RequestEvent[]>([]);
  const [timeline, setTimeline] = useState<TimelineEvent[]>([]);
  const [live, setLive] = useState<LiveMetrics | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [streaming, setStreaming] = useState(false);

  const refresh = useCallback(async () => {
    if (!id) return;
    try {
      const exp = await getExperiment(id);
      setExperiment(exp);
      if (TERMINAL.includes(exp.status)) {
        setStreaming(false);
        const history = await getEvents(id);
        setRequests(history.requests);
        setTimeline(history.timeline);
      } else {
        setStreaming(true);
      }
      setError(null);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Unexpected error");
    }
  }, [id]);

  useEffect(() => {
    setRequests([]); setTimeline([]); setLive(null); setExperiment(null);
    void refresh();
  }, [refresh]);

  const connected = useSSE(id, streaming, {
    request: (e: RequestEvent) => setRequests((prev) => [...prev, e]),
    timeline: (e: TimelineEvent) => setTimeline((prev) => [...prev, e]),
    metrics: setLive,
    status: (s: { status: Experiment["status"] }) => {
      setExperiment((prev) => (prev ? { ...prev, status: s.status } : prev));
      if (TERMINAL.includes(s.status)) { setStreaming(false); void refresh(); }
    },
  });

  return { experiment, requests, timeline, live, error, connected, streaming, refresh };
}
