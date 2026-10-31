import type { Target, TargetInput, ValidationResult } from "../types/target";
import { patch, post, request } from "./api";

export const listTargets = () => request<Target[]>("/api/targets");
export const createTarget = (input: TargetInput) => post<Target>("/api/targets", input);
export const updateTarget = (id: number, input: Partial<TargetInput>) => patch<Target>(`/api/targets/${id}`, input);
export const deleteTarget = (id: number) => request<null>(`/api/targets/${id}`, { method: "DELETE" });
export const revalidateTarget = (id: number) => post<ValidationResult>(`/api/targets/${id}/validate`);
export const validateUrl = (base_url: string, ownership_confirmed: boolean, environment_type: string) =>
  post<ValidationResult>("/api/targets/validate", { base_url, ownership_confirmed, environment_type });

export const addDemoTargets = () => post<Target[]>("/api/targets/demo");
