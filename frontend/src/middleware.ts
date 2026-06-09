import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const token = request.cookies.get('auth_token')?.value;
  const { pathname } = request.nextUrl;

  // Paths that do not require authentication
  if (pathname.startsWith('/login') || pathname.startsWith('/_next') || pathname === '/favicon.ico') {
    // If user has a valid session token, redirect away from the login portal
    if (token && pathname.startsWith('/login')) {
      return NextResponse.redirect(new URL('/pipeline', request.url));
    }
    return NextResponse.next();
  }

  // Enforce session presence on all internal CRM dashboards
  if (!token) {
    return NextResponse.redirect(new URL('/login', request.url));
  }

  // Redirect root path to the dynamic pipeline workspace
  if (pathname === '/') {
    return NextResponse.redirect(new URL('/pipeline', request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    // Apply middleware to all routes, skipping Next.js internals, assets, and api proxies
    '/((?!api/|_next/static|_next/image|favicon.ico).*)',
  ],
};
