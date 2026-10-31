export type Severity = "critical" | "high" | "medium" | "low";
export type FixStatus = "proposed" | "reviewed" | "applied" | "verified";

export interface Analysis {
  id: number; experiment_id: string; model_name: string; finding: string; severity: Severity;
  severity_rationale: string; what_happened: string; user_impact: string; evidence: string[];
  likely_cause: string; recommended_actions: string[];
  code_example: { language: string; snippet: string; assumptions: string };
  verification_steps: string[]; created_at: string;
}

export interface Fix { id: number; experiment_id: string; analysis_id: number; status: FixStatus; developer_notes: string }
export interface FixItem { fix: Fix; analysis: Analysis }
