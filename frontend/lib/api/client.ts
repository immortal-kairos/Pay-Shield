import { clearToken, getToken } from "@/lib/auth/token-storage";
import { env } from "@/lib/utils/env";
import axios from "axios";

export const apiClient = axios.create({
  baseURL: env.API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

apiClient.interceptors.request.use(
  (config) => {
    const token = getToken();
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      const isLoginPage = typeof window !== "undefined" && window.location.pathname === "/login";
      
      clearToken();
      
      if (typeof window !== "undefined" && !isLoginPage) {
        window.location.href = "/login?error=session_expired";
      }
    }
    return Promise.reject(error);
  }
);