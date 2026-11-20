// Pages that can be viewed without signing in. Every other page requires a session;
// the root layout sends signed-out visitors to /login.
const PUBLIC_PATHS = ['/login', '/register', '/setup'];

export function isPublicPath(pathname: string): boolean {
    return PUBLIC_PATHS.some((p) => pathname === p || pathname.startsWith(`${p}/`));
}
