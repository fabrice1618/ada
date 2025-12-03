<?php

/**
 * Authentication Middleware
 *
 * Checks if user is authenticated before allowing access to protected routes
 */
class AuthMiddleware extends Middleware
{
    /**
     * Handle an incoming request
     *
     * @param Request $request The incoming request object
     * @param callable $next The next middleware in the pipeline
     * @return Response The response object
     */
    public function handle(Request $request, callable $next): Response
    {
        // Check if user is logged in (session check)
        if (!Session::has('user_id')) {
            // User is not authenticated, redirect to login page
            return Response::redirect('/login')
                ->with('error', 'Please log in to access this page.');
        }

        // User is authenticated, update last activity
        Session::set('last_activity', time());

        // Proceed to next middleware
        return $next($request);
    }
}
