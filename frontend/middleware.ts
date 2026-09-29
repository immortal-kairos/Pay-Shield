import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

export function middleware(request: NextRequest) {
  const hasToken = request.cookies.has("payshield_token_present");
  const { pathname } = request.nextUrl;

  const protectedRoutes = ["/dashboard", "/maker", "/checker", "/admin"];
  const isProtectedRoute = protectedRoutes.some((route) => pathname.startsWith(route));

  if (isProtectedRoute && !hasToken) {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/dashboard/:path*", "/maker/:path*", "/checker/:path*", "/admin/:path*"],
};