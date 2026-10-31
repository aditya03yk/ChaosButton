import type { Experiment, TimelineEvent, RequestEvent } from "./experiment";
import type { Metrics } from "./metrics";
import type { Analysis, Fix } from "./analysis";
import type { ComparisonResult } from "./metrics";
import type { Target } from "./target";

export interface AIStatus {
  provider: string; model: string; reachable: boolean; model_available: boolean; message: string; hint: string | null;
}
export interface SystemStatus { backend: string; database: string; ai: AIStatus; active_experiments: number }
export interface SystemConfig {
  app_name: string; app_env: string; ollama_base_url: string; ollama_model: string;
  limits: Record<string, number>; allowed_remote_hosts: string[]; upstream_url: string;
}
export interface Dashboard {
  total_experiments: number; total_requests: number; average_success_rate: number | null;
  average_resilience_score: number | null; critical_findings: number; last_experiment_status: string | null;
  active_experiments: number; recent_experiments: Experiment[]; activity: TimelineEvent[];
}
export interface Report {
  experiment: Experiment; target: Target; metrics: Metrics | null; status_distribution: Record<string, number>;
  request_events: RequestEvent[]; timeline: TimelineEvent[]; analyses: Analysis[]; fixes: Fix[];
  retests: { experiment: Experiment; comparison?: ComparisonResult }[]; disclaimer: string;
}
