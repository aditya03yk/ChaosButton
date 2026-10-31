export interface ScoreComponent { value: number | null; weight: number; available: boolean; effective_weight: number }

export interface Metrics {
  experiment_id: string;
  total_requests: number;
  successful_requests: number;
  failed_requests: number;
  timeout_count: number;
  success_rate: number | null;
  error_rate: number | null;
  p50_latency: number | null;
  p95_latency: number | null;
  average_latency: number | null;
  fallback_score: number | null;
  recovery_time: number | null;
  resilience_score: number | null;
  baseline_requests: number;
  baseline_p50_latency: number | null;
  baseline_p95_latency: number | null;
  sample_size: number;
  score_components: Record<string, ScoreComponent>;
  limitations: string[];
}

export interface LiveMetrics {
  total: number; successful: number; failed: number; timeouts: number; fallbacks: number;
  error_rate: number | null; success_rate: number | null;
  average_latency: number | null; p50_latency: number | null; p95_latency: number | null;
  status_counts: Record<string, number>; active_faults: number; phase: string; duration_s: number;
}

export interface MetricRow {
  metric: string; original: number | null; retest: number | null;
  absolute_diff: number | null; percent_diff: number | null;
  verdict: "improved" | "regressed" | "unchanged" | "unavailable";
}

export interface FixValidation { summary: string; improvements: string[]; regressions: string[]; remaining_weaknesses: string[] }

export interface ComparisonResult {
  comparable: boolean; incompatibilities: string[]; target_changed: boolean;
  original_id: string; retest_id: string; rows: MetricRow[]; improved: number; regressed: number;
  ai_validation?: FixValidation; ai_validation_error?: string;
}
