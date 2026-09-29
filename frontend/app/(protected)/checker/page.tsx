"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function CheckerRedirectPage() {
  const router = useRouter();
  useEffect(() => {
    // Checkers share the executive dashboard view
    router.replace("/dashboard");
  }, [router]);

  return null;
}