import { auth } from "@/auth";

export default auth((req) => {
  const isLoggedIn = !!req.auth;
  const isAuthRoute = req.nextUrl.pathname.startsWith("/api/auth");

  if (!isLoggedIn && !isAuthRoute) {
    const signInUrl = new URL("/api/auth/signin", req.nextUrl.origin);
    signInUrl.searchParams.set("callbackUrl", req.nextUrl.pathname);
    return Response.redirect(signInUrl);
  }
});

export const config = {
  matcher: [
    /*
     * Protect all routes except static files, images, and favicon.
     */
    "/((?!_next/static|_next/image|favicon.ico).*)",
  ],
};
