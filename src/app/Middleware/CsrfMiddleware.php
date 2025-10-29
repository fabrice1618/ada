<?php

/**
 * CSRF Middleware
 *
 * Validates CSRF tokens for state-changing requests (POST, PUT, DELETE, PATCH)
 */
class CsrfMiddleware extends Middleware
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
        // Check if request is a state-changing method
        if (in_array($request->method(), ['POST', 'PUT', 'DELETE', 'PATCH'])) {
            // Get CSRF token from request
            $csrfToken = $request->post('_csrf_token') ?? $request->header('X-CSRF-TOKEN', '');

            // Validate the token
            if (!Security::validateCsrfToken($csrfToken)) {
                // Return 403 Forbidden response
                return new Response(
                    "<h1>403 Forbidden</h1><p>CSRF token validation failed. This request has been blocked for security reasons.</p>",
                    403
                );
            }
        }

        // Token is valid or not required, proceed to next middleware
        return $next($request);
    }
}
