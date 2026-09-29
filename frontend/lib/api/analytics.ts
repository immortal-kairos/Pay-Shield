import { DashboardMetrics } from "@/types/api";
import { apiClient } from "./client";

export const analyticsApi = {
  getDashboardMetrics: async (): Promise<DashboardMetrics> => {
    const response = await apiClient.get<DashboardMetrics>("/api/analytics/dashboard");
    return response.data;
  },
};