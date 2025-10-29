<?php

/**
 * Base Controller Class
 *
 * All application controllers should extend this base class.
 * Provides common functionality for rendering views and handling redirects.
 *
 * @package ADA Framework
 * @version 1.0 (Phase 4)
 */
class Controller
{
    /**
     * Render a view template with data
     *
     * @param string $template Template path (e.g., 'home/index')
     * @param array $data Data to pass to the template
     * @return Response|void Returns Response object (Phase 4+) or outputs directly (legacy)
     */
    protected function view($template, $data = [])
    {
        try {
            // Phase 4: Return Response object for middleware pipeline
            return Response::view($template, $data);
        } catch (Exception $e) {
            // Handle template rendering errors
            return new Response("<h1>500 Internal Server Error</h1><p>{$e->getMessage()}</p>", 500);
        }
    }

    /**
     * Redirect to a URL
     *
     * @param string $url URL to redirect to
     * @return Response
     */
    protected function redirect($url)
    {
        return Response::redirect($url);
    }

    /**
     * Return a JSON response
     *
     * @param mixed $data Data to encode as JSON
     * @param int $statusCode HTTP status code
     * @return Response
     */
    protected function json($data, $statusCode = 200)
    {
        return Response::json($data, $statusCode);
    }

    /**
     * Handle 404 Not Found errors
     *
     * @param string $message Error message
     * @return void
     */
    protected function error404($message = 'Page not found')
    {
        http_response_code(404);
        echo "<h1>404 Not Found</h1>";
        echo "<p>{$message}</p>";
        exit();
    }

    /**
     * Handle 500 Internal Server errors
     *
     * @param string $message Error message
     * @return void
     */
    protected function error500($message = 'Internal server error')
    {
        http_response_code(500);
        echo "<h1>500 Internal Server Error</h1>";
        echo "<p>{$message}</p>";
        exit();
    }
}
