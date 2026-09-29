import { LoginRequest, LoginResponse } from "@/types/auth";
import { clearToken } from "../auth/token-storage";
import { apiClient } from "./client";

export const authApi = {
  login: async (payload: LoginRequest): Promise<LoginResponse> => {
    const response = await apiClient.post<LoginResponse>("/api/auth/login", payload);
    return response.data;
  },

  logout: async (): Promise<void> => {
    // Purely client-side for US-15
    clearToken();
  },
};