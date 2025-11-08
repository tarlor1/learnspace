import { NextRequest, NextResponse } from "next/server";
import { auth0 } from "./lib/auth0";

export async function middleware(request: NextRequest) {
	const authResponse = await auth0.middleware(request);

	// If this is an auth route, return the auth response
	if (request.nextUrl.pathname.startsWith("/api/auth")) {
		return authResponse;
	}

	// Protected routes - require authentication
	const protectedRoutes = ["/profile", "/upload", "/study"];
	const isProtectedRoute = protectedRoutes.some((route) =>
		request.nextUrl.pathname.startsWith(route),
	);

	if (isProtectedRoute) {
		// Check if user has a session
		const session = await auth0.getSession(request);

		if (!session) {
			// Redirect to login with returnTo parameter
			const loginUrl = new URL("/api/auth/login", request.url);
			loginUrl.searchParams.set("returnTo", request.nextUrl.pathname);
			return NextResponse.redirect(loginUrl);
		}
	}

	// For other routes, just return the auth response (which handles session cookies)
	return authResponse;
}

export const config = {
	matcher: [
		"/api/auth/:path*",
		"/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)",
	],
};
