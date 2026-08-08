import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const ROUTES_PUBLIQUES = ["/login"];

/**
 * Middleware Next.js de protection des routes.
 * Redirige vers /login si l'utilisateur n'est pas authentifié.
 * La vérification fine des rôles est faite côté composant.
 */
export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Laisser passer les routes publiques
  if (ROUTES_PUBLIQUES.includes(pathname)) {
    return NextResponse.next();
  }

  // Vérifier la présence du store dans les cookies
  const authCookie = request.cookies.get("sce-auth");

  if (!authCookie) {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  try {
    const auth = JSON.parse(authCookie.value);
    if (!auth?.state?.estConnecte || !auth?.state?.accessToken) {
      return NextResponse.redirect(new URL("/login", request.url));
    }
  } catch {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico).*)"],
};