import type { AIStatus, Dashboard, Report, SystemConfig, SystemStatus } from "../types/system";
import { API_BASE, request } from "./api";

export const getDashboard = () => request<Dashboard>("/api/dashboard");
export const getReport = (id: string) => request<Report>(`/api/experiments/${id}/report`);
export const getSystemStatus = () => request<SystemStatus>("/api/system/status");
export const getAIStatus = () => request<AIStatus>("/api/system/ai-status");
export const getConfig = () => request<SystemConfig>("/api/system/config");
export const reportDownloadUrl = (id: string) => `${API_BASE}/api/experiments/${id}/report?download=true`;
