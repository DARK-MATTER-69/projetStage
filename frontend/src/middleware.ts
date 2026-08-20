import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { aAcces } from "@/lib/roles";

const ROUTES_PUBLIQUES = ["/login"];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  if (ROUTES_PUBLIQUES.includes(pathname)) {
    return NextResponse.next();
  }

  if (
    pathname.startsWith("/_next") ||
    pathname.startsWith("/api") ||
    pathname.includes(".")
  ) {
    return NextResponse.next();
  }

  const token = request.cookies.get("access_token")?.value;
  if (!token) {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  const role = request.cookies.get("user_role")?.value;
  if (role && !aAcces(role, pathname)) {
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};