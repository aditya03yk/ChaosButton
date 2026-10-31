/** Presentation-only formatting helpers (no metric calculation lives in the frontend). */

/** The backend sends naive UTC timestamps; treat them as UTC. */
export function parseUtc(value: string): Date {
  return new Date(/[zZ]|[+-]\d\d:?\d\d$/.test(value) ? value : `${value}Z`);
}

export const fmtMs = (v: number | null | undefined) => (v == null ? "n/a" : `${Math.round(v)} ms`);
export const fmtPct = (v: number | null | undefined) => (v == null ? "n/a" : `${v.toFixed(1)}%`);
export const fmtSeconds = (v: number | null | undefined) => (v == null ? "unavailable" : `${v.toFixed(2)} s`);
export const fmtScore = (v: number | null | undefined) => (v == null ? "n/a" : v.toFixed(0));
export const fmtTime = (v: string) => parseUtc(v).toLocaleTimeString();
export const fmtDateTime = (v: string | null) => (v ? parseUtc(v).toLocaleString() : "n/a");

export const FAULT_LABELS: Record<string, string> = {
  latency: "Latency", timeout: "Timeout", http_500: "HTTP 500", http_503: "HTTP 503",
};
