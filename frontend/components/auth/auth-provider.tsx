"use client";

import { authApi } from "@/lib/api/auth";
import { getDefaultRouteForRole, isTokenExpired, parseJwt } from "@/lib/auth/session";
import { clearToken, getToken, setToken } from "@/lib/auth/token-storage";
import { AuthState, LoginRequest } from "@/types/auth";
import { useRouter } from "next/navigation";
import React, { createContext, useContext, useEffect, useState } from "react";

interface AuthContextType extends AuthState {
  login: (payload: LoginRequest) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<AuthState>({
    user: null,
    token: null,
    isAuthenticated: false,
    isHydrating: true,
  });
  
  const router = useRouter();

  useEffect(() => {
    const initAuth = () => {
      const token = getToken();
      if (token && !isTokenExpired(token)) {
        const user = parseJwt(token);
        setState({ user, token, isAuthenticated: !!user, isHydrating: false });
      } else {
        clearToken();
        setState({ user: null, token: null, isAuthenticated: false, isHydrating: false });
      }
    };
    initAuth();
  }, []);

  const login = async (payload: LoginRequest) => {
    const data = await authApi.login(payload);
    const user = parseJwt(data.access_token);
    
    if (!user) throw new Error("Invalid Token Response");

    setToken(data.access_token);
    setState({
      token: data.access_token,
      user,
      isAuthenticated: true,
      isHydrating: false,
    });

    router.push(getDefaultRouteForRole(user.role));
  };

  const logout = () => {
    clearToken();
    setState({ user: null, token: null, isAuthenticated: false, isHydrating: false });
    router.push("/login");
  };

  return (
    <AuthContext.Provider value={{ ...state, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within AuthProvider");
  return context;
};