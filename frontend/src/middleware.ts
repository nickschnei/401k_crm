import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Redirect root path to the dynamic pipeline workspace
  if (pathname === '/') {
    return NextResponse.redirect(new URL('/pipeline', request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    '/((?!api/|_next/static|_next/image|favicon.ico).*)',
  ],
};
