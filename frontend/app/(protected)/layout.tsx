"use client";

import { useAuth } from "@/components/auth/auth-provider";
import { LogoutButton } from "@/components/auth/logout-button";
import { Spinner } from "@/components/ui/spinner";
import { redirect } from "next/navigation";
import { useEffect } from "react";

export default function ProtectedLayout({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isHydrating, user } = useAuth();

  useEffect(() => {
    if (!isHydrating && !isAuthenticated) {
      redirect("/login");
    }
  }, [isHydrating, isAuthenticated]);

  if (isHydrating) {
    return (
      <div className="h-screen w-full flex items-center justify-center">
        <Spinner className="w-8 h-8 text-blue-600" />
      </div>
    );
  }

  if (!isAuthenticated) return null;

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <header className="bg-white border-b h-16 flex items-center justify-between px-6 sticky top-0 z-10">
        <div className="flex items-center gap-4">
          <span className="font-bold text-blue-900 text-xl tracking-tight">PayShield</span>
          <div className="h-6 w-[1px] bg-gray-200" />
          <div className="text-sm">
            <span className="text-gray-500">Org:</span> <span className="font-medium text-gray-900">{user?.orgId.slice(0, 8)}...</span>
          </div>
        </div>
        
        <div className="flex items-center gap-6">
          <div className="text-right hidden sm:block">
            <p className="text-sm font-medium text-gray-900">{user?.email}</p>
            <p className="text-xs text-blue-600 font-semibold">{user?.role}</p>
          </div>
          <LogoutButton />
        </div>
      </header>

      <div className="flex flex-1">
        <aside className="w-64 bg-white border-r hidden md:block p-4">
          <nav className="space-y-1">
            <div className="p-2 text-xs font-semibold text-gray-400 uppercase tracking-wider">Menu</div>
            <div className="p-2 text-sm text-gray-600 hover:bg-gray-50 rounded cursor-pointer">Overview</div>
          </nav>
        </aside>
        <main className="flex-1 p-8">{children}</main>
      </div>
    </div>
  );
}