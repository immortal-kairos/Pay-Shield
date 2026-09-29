"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { getToken, clearToken } from "@/lib/auth/token-storage";
import { parseJwt, isTokenExpired, getDefaultRouteForRole } from "@/lib/auth/session";
import { Spinner } from "@/components/ui/spinner";

export default function RootRedirect() {
  const router = useRouter();

  useEffect(() => {
    const token = getToken();
    
    if (token) {
      if (isTokenExpired(token)) {
        clearToken();
        router.replace("/login");
      } else {
        const user = parseJwt(token);
        if (user) {
          router.replace(getDefaultRouteForRole(user.role));
        } else {
          router.replace("/login");
        }
      }
    } else {
      router.replace("/login");
    }
  }, [router]);

  return (
    <div className="flex h-screen w-full items-center justify-center">
      <Spinner className="h-8 w-8 text-blue-600" />
    </div>
  );
}