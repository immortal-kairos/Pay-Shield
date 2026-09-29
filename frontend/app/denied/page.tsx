"use client";

import { useAuth } from "@/components/auth/auth-provider";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { ShieldAlert } from "lucide-react";
import Link from "next/link";
import { getDefaultRouteForRole } from "@/lib/auth/roles";

export default function DeniedPage() {
  const { user, isAuthenticated } = useAuth();
  
  return (
    <div className="h-screen flex items-center justify-center bg-gray-50 p-4">
      <Card className="max-w-md w-full p-8 text-center space-y-6">
        <div className="flex justify-center">
          <div className="p-3 bg-red-100 rounded-full text-red-600">
            <ShieldAlert size={48} />
          </div>
        </div>
        <h1 className="text-2xl font-bold text-gray-900">Access Restricted</h1>
        <p className="text-gray-600">
          Your account role ({user?.role || "Guest"}) does not have permissions to access the requested resource.
        </p>
        <div className="pt-4">
          {isAuthenticated && user ? (
            <Link href={getDefaultRouteForRole(user.role)}>
              <Button className="w-full">Back to Workspace</Button>
            </Link>
          ) : (
            <Link href="/login">
              <Button className="w-full">Return to Login</Button>
            </Link>
          )}
        </div>
      </Card>
    </div>
  );
}