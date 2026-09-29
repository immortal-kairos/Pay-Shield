import { Role, SessionUser } from "@/types/auth";
import { getToken } from "./token-storage";

export const parseJwt = (token: string): SessionUser | null => {
  try {
    const base64Url = token.split(".")[1];
    const base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/");
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split("")
        .map((c) => "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2))
        .join("")
    );
    const decoded = JSON.parse(jsonPayload);

    if (!decoded.sub || !decoded.email || !decoded.role || !decoded.org_id || !decoded.exp) {
      return null;
    }

    return {
      userId: decoded.sub,
      email: decoded.email,
      role: decoded.role as Role,
      orgId: decoded.org_id,
      exp: decoded.exp,
    };
  } catch (error) {
    return null;
  }
};

export const isTokenExpired = (token: string): boolean => {
  const user = parseJwt(token);
  if (!user) return true;
  // JWT exp is in seconds, Date.now() is in ms
  return user.exp * 1000 < Date.now();
};

export const hasValidSession = (): boolean => {
  const token = getToken();
  if (!token) return false;
  return !isTokenExpired(token);
};

export const getDefaultRouteForRole = (role: Role): string => {
  const routes: Record<Role, string> = {
    MAKER: "/maker",
    CHECKER: "/checker",
    ADMIN: "/admin",
  };
  return routes[role] || "/login";
};