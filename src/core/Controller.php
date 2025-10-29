<?php

/**
 * Base Controller Class
 *
 * All application controllers should extend this base class.
 * Provides common functionality for rendering views and handling redirects.
 *
 * @package ADA Framework
 * @version 1.0 (Phase 1)
 */
class Controller
{
    /**
     * Render a view template with data
     *
     * @param string $template Template path (e.g., 'home/index')
     * @param array $data Data to pass to the template
     * @return void
     */
    protected function view($template, $data = [])
    {
        try {
            echo View::render($template, $data);
        } catch (Exception $e) {
            // Handle template rendering errors
            $this->error500($e->getMessage());
        }
    }

    /**
     * Redirect to a URL
     *
     * @param string $url URL to redirect to
     * @return void
     */
    protected function redirect($url)
    {
        header("Location: {$url}");
        exit();
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
