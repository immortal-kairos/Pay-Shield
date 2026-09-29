"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function AdminRedirectPage() {
  const router = useRouter();
  useEffect(() => {
    // Admins share the executive dashboard view
    router.replace("/dashboard");
  }, [router]);

  return null;
}