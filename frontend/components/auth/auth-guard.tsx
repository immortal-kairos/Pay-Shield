"use client";

import { Spinner } from "@/components/ui/spinner";
import { getToken } from "@/lib/auth/token-storage";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

export const AuthGuard = ({ children }: { children: React.ReactNode }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const router = useRouter();

  useEffect(() => {
    const token = getToken();
    if (!token) {
      router.replace("/login");
    } else {
      setIsAuthenticated(true);
    }
  }, [router]);

  if (!isAuthenticated) {
    return (
      <div className="flex h-screen w-full items-center justify-center">
        <Spinner className="h-8 w-8 text-blue-600" />
      </div>
    );
  }

  return <>{children}</>;
};