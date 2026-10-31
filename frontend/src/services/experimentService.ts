import type { Analysis, Fix, FixItem, FixStatus } from "../types/analysis";
import type { Experiment, ExperimentInput, FaultScope, Page, RequestEvent, Suite, TimelineEvent } from "../types/experiment";
import type { ComparisonResult } from "../types/metrics";
import { patch, post, request } from "./api";

export interface ListParams { search?: string; target_id?: string; fault_type?: string; status?: string; newest_first?: boolean; offset?: number; limit?: number }

export function listExperiments(params: ListParams = {}) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => v !== undefined && v !== "" && query.set(k, String(v)));
  return request<Page<Experiment>>(`/api/experiments?${query}`);
}
export const getExperiment = (id: string) => request<Experiment>(`/api/experiments/${id}`);
export const createExperiment = (input: ExperimentInput) => post<Experiment>("/api/experiments", input);
export const startExperiment = (id: string) => post<Experiment>(`/api/experiments/${id}/start`);
export const stopExperiment = (id: string) => post<Experiment>(`/api/experiments/${id}/stop`);
export const getEvents = (id: string) =>
  request<{ requests: RequestEvent[]; timeline: TimelineEvent[] }>(`/api/experiments/${id}/events`);
export const retest = (id: string, target_id?: number) => post<Experiment>(`/api/experiments/${id}/retest`, { target_id });
export const compareRuns = (id: string, other_experiment_id: string, explain: boolean) =>
  post<ComparisonResult>(`/api/experiments/${id}/compare`, { other_experiment_id, explain });
export const analyse = (id: string, code_context?: string) =>
  post<{ analysis: Analysis; fix: Fix }>(`/api/experiments/${id}/ai-analysis`, { code_context: code_context || null });
export const listFixes = (id: string) => request<FixItem[]>(`/api/experiments/${id}/fixes`);
export const updateFix = (id: number, body: { status?: FixStatus; developer_notes?: string }) =>
  patch<Fix>(`/api/fixes/${id}`, body);

export interface SuiteInput { target_id: number; route: string; method: string; scope: FaultScope; dependency_route: string | null }
export const startSuite = (input: SuiteInput) => post<Suite>("/api/suites", input);
export const getSuite = (id: string) => request<Suite>(`/api/suites/${id}`);
export const stopSuite = (id: string) => post<Suite>(`/api/suites/${id}/stop`);
