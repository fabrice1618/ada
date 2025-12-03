<?php

/**
 * Session Middleware
 *
 * Initializes secure session management for the application
 */
class SessionMiddleware extends Middleware
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
        // Start secure session
        Session::start();

        // Regenerate session ID periodically (every 30 minutes)
        $lastRegeneration = Session::get('last_regeneration', 0);
        $currentTime = time();

        if ($currentTime - $lastRegeneration > 1800) {
            session_regenerate_id(true);
            Session::set('last_regeneration', $currentTime);
        }

        // Update last activity timestamp
        Session::set('last_activity', $currentTime);

        // Proceed to next middleware
        return $next($request);
    }
}
