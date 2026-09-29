"use client";

import { Button } from "@/components/ui/button";
import { clearToken } from "@/lib/auth/token-storage";
import { LogOut } from "lucide-react";
import { useRouter } from "next/navigation";

export const LogoutButton = () => {
  const router = useRouter();

  const handleLogout = () => {
    clearToken();
    router.push("/login");
  };

  return (
    <Button className="bg-transparent text-gray-700 hover:bg-gray-100" onClick={handleLogout}>
      <LogOut className="mr-2 h-4 w-4" />
      Logout
    </Button>
  );
};