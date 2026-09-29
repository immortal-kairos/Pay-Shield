"use client";

import { useAuth } from "@/components/auth/auth-provider";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Spinner } from "@/components/ui/spinner";
import { getDefaultRouteForRole } from "@/lib/auth/session";
import { useRouter } from "next/navigation";
import React, { useEffect, useState } from "react";
import { z } from "zod";

const loginSchema = z.object({
  email: z.string().email("Please enter a valid business email"),
  password: z.string().min(8, "Password must be at least 8 characters"),
});

export default function LoginPage() {
  const { login, isAuthenticated, user } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();

  useEffect(() => {
    if (isAuthenticated && user) {
      router.replace(getDefaultRouteForRole(user.role));
    }
  }, [isAuthenticated, user, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    
    const validation = loginSchema.safeParse({ email, password });
    if (!validation.success) {
      setError(validation.error.errors[0].message);
      return;
    }

    setIsLoading(true);
    try {
      await login({ email, password });
    } catch (err: any) {
      if (err.response?.status === 401) {
        setError("Invalid email or password");
      } else {
        setError("System error. Please try again later.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-screen items-center justify-center bg-gray-50 p-4">
      <Card className="w-full max-w-md p-8 shadow-xl">
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-bold text-blue-900">PayShield</h1>
          <p className="text-gray-500 mt-2">B2B Payments Security Platform</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          {error && (
            <div className="p-3 text-sm text-red-600 bg-red-50 border border-red-200 rounded-md">
              {error}
            </div>
          )}
          
          <div className="space-y-2">
            <label className="text-sm font-semibold text-gray-700">Email Address</label>
            <Input 
              type="email" 
              value={email} 
              onChange={(e) => setEmail(e.target.value)} 
              placeholder="name@company.com"
              required
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-semibold text-gray-700">Password</label>
            <Input 
              type="password" 
              value={password} 
              onChange={(e) => setPassword(e.target.value)} 
              placeholder="••••••••"
              required
            />
          </div>

          <Button type="submit" className="w-full h-11" disabled={isLoading}>
            {isLoading ? <Spinner className="mr-2" /> : "Sign In"}
          </Button>
        </form>
      </Card>
    </div>
  );
}