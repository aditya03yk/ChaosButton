export type TechStack = "python_fastapi" | "python_flask" | "node_express" | "java_spring" | "other";
export type EnvironmentType = "local" | "staging" | "demo";

export interface Target {
  id: number;
  name: string;
  base_url: string;
  description: string;
  technology_stack: TechStack;
  environment_type: EnvironmentType;
  notes: string;
  ownership_confirmed: boolean;
  last_validated_at: string | null;
  last_validation_ok: boolean | null;
}

export type TargetInput = Omit<Target, "id" | "last_validated_at" | "last_validation_ok">;

export interface ValidationResult {
  valid: boolean;
  reachable: boolean;
  normalized_url: string;
  status_code: number | null;
  latency_ms: number | null;
  errors: string[];
  warnings: string[];
}
