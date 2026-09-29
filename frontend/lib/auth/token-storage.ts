const TOKEN_KEY = "payshield_access_token";
const COOKIE_NAME = "payshield_token_present";

export const setToken = (token: string): void => {
  if (typeof window === "undefined") return;
  localStorage.setItem(TOKEN_KEY, token);
  setTokenPresentCookie();
};

export const getToken = (): string | null => {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
};

export const clearToken = (): void => {
  if (typeof window === "undefined") return;
  localStorage.removeItem(TOKEN_KEY);
  clearTokenPresentCookie();
};

export const setTokenPresentCookie = (): void => {
  if (typeof window === "undefined") return;
  // Middleware needs this cookie to pre-filter routes
  document.cookie = `${COOKIE_NAME}=true; path=/; SameSite=Lax; Max-Age=86400`;
};

export const clearTokenPresentCookie = (): void => {
  if (typeof window === "undefined") return;
  document.cookie = `${COOKIE_NAME}=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT; SameSite=Lax`;
};