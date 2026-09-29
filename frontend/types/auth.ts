export type Role = 'MAKER' | 'CHECKER' | 'ADMIN';

export interface SessionUser {
  userId: string;
  email: string;
  role: Role;
  orgId: string;
  exp: number;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export interface AuthState {
  user: SessionUser | null;
  token: string | null;
  isAuthenticated: boolean;
  isHydrating: boolean;
}