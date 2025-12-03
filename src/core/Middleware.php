<?php

/**
 * Middleware Base Class
 *
 * All middleware classes should extend this base class and implement
 * the handle() method to process requests in the middleware pipeline.
 */
abstract class Middleware
{
    /**
     * Handle an incoming request
     *
     * @param Request $request The incoming request object
     * @param callable $next The next middleware in the pipeline
     * @return Response The response object
     */
    abstract public function handle(Request $request, callable $next): Response;
}
