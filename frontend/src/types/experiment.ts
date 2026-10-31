import type { Metrics } from "./metrics";

export type FaultType = "latency" | "timeout" | "http_500" | "http_503";
export type FaultScope = "inbound" | "dependency";
export type ExperimentStatus =
  "CREATED" | "VALIDATING" | "BASELINE" | "RUNNING" | "RECOVERING" | "COMPLETED" | "STOPPED" | "FAILED";

export const TERMINAL: ExperimentStatus[] = ["COMPLETED", "STOPPED", "FAILED"];

export interface FaultParams {
  scope: FaultScope;
  dependency_route: string | null;
  delay_ms: number | null;
  timeout_ms: number | null;
  duration_s: number;
  max_affected: number;
  baseline_requests: number;
  request_timeout_ms: number;
  concurrency: number;
  interval_ms: number;
}

export interface Experiment {
  id: string;
  target_id: number;
  target_name: string | null;
  suite_id: string | null;
  name: string;
  mode: "auto" | "manual";
  route: string;
  method: string;
  fault_type: FaultType;
  fault_configuration: FaultParams;
  status: ExperimentStatus;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
  duration: number | null;
  parent_experiment_id: string | null;
  created_at: string;
  metrics: Metrics | null;
}

export interface ExperimentInput {
  target_id: number;
  route: string;
  method: string;
  fault_type: FaultType;
  fault_configuration: Partial<FaultParams>;
  notes?: string;
}

export interface RequestEvent {
  timestamp: string; phase: "baseline" | "fault" | "recovery"; status_code: number | null;
  latency_ms: number; success: boolean; timed_out: boolean; fault_applied: boolean; fallback_used: boolean;
}

export interface TimelineEvent { id?: number; timestamp: string; level: "info" | "warning" | "error" | "success"; message: string }

export interface Page<T> { items: T[]; total: number; offset: number; limit: number }

export interface Suite {
  suite_id: string;
  finished: boolean;
  experiments: Experiment[];
  consolidated: {
    scenarios_completed: number; scenarios_total: number; average_success_rate: number | null;
    average_resilience_score: number | null; weakest_scenario: string | null;
  };
}
