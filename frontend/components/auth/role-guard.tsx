"use client";

import { Role } from "@/types/auth";
import { redirect } from "next/navigation";
import { useEffect } from "react";
import { Spinner } from "../ui/spinner";
import { useAuth } from "./auth-provider";

interface RoleGuardProps {
  allow: Role[];
  children: React.ReactNode;
}

export const RoleGuard = ({ allow, children }: RoleGuardProps) => {
  const { user, isAuthenticated, isHydrating } = useAuth();

  useEffect(() => {
    if (!isHydrating) {
      if (!isAuthenticated) redirect("/login");
      if (user && !allow.includes(user.role)) redirect("/denied");
    }
  }, [isHydrating, isAuthenticated, user, allow]);

  if (isHydrating) {
    return (
      <div className="flex h-32 w-full items-center justify-center">
        <Spinner className="w-6 h-6 text-blue-600" />
      </div>
    );
  }

  if (!isAuthenticated || !user || !allow.includes(user.role)) {
    return null;
  }

  return <>{children}</>;
};