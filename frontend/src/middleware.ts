// import { NextResponse } from "next/server";
// import type { NextRequest } from "next/server";

// const ROUTES_PUBLIQUES = ["/login"];

// export function middleware(request: NextRequest) {
//   const { pathname } = request.nextUrl;

//   // Laisser passer les routes publiques
//   if (ROUTES_PUBLIQUES.includes(pathname)) {
//     return NextResponse.next();
//   }

//   // Laisser passer les assets Next.js
//   if (
//     pathname.startsWith("/_next") ||
//     pathname.startsWith("/api") ||
//     pathname.includes(".")
//   ) {
//     return NextResponse.next();
//   }

//   // Vérifier le token dans les cookies
//   const token = request.cookies.get("access_token")?.value;

//   if (!token) {
//     return NextResponse.redirect(new URL("/login", request.url));
//   }

//   return NextResponse.next();
// }

// export const config = {
//   matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
// };



import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(request: NextRequest) {
  return NextResponse.next();
}