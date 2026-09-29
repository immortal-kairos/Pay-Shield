const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL;

if (!API_BASE_URL) {
  throw new Error("NEXT_PUBLIC_API_BASE_URL environment variable is missing.");
}

export const env = {
  API_BASE_URL,
  APP_NAME: process.env.NEXT_PUBLIC_APP_NAME || "PayShield",
};