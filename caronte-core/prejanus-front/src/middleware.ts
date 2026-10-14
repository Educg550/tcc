import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(request: NextRequest) {
	const { pathname } = request.nextUrl;

	if (
		pathname.startsWith("/_next/") || // Next.js assets
		pathname.startsWith("/favicon.ico") ||
		pathname.endsWith(".css") ||
		pathname.endsWith(".js") ||
		pathname.endsWith(".png") ||
		pathname.endsWith(".jpg") ||
		pathname.endsWith(".svg")
	) {
		return NextResponse.next();
	}

	const token = request.cookies.get("session")?.value;

	const isAuthRoute = pathname.startsWith("/login") || pathname === "/";

	if (!token && !isAuthRoute) {
		return NextResponse.redirect(new URL("/", request.url));
	}

	return NextResponse.next();
}
