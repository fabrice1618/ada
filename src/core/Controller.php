<?php

/**
 * Base Controller Class
 *
 * All application controllers should extend this base class.
 * Provides common functionality for rendering views and handling redirects.
 *
 * @package ADA Framework
 * @version 1.0 (Phase 5)
 */
class Controller
{
    /**
     * @var Request Current request object
     */
    protected Request $request;
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
     * Validate request data
     *
     * @param array $data Data to validate
     * @param array $rules Validation rules
     * @param array $messages Custom error messages
     * @return array Validated data
     * @throws Exception If validation fails (redirects with errors)
     */
    protected function validate(array $data, array $rules, array $messages = []): array
    {
        $validator = Validator::make($data, $rules, $messages);

        if (!$validator->validate()) {
            // Flash errors and old input to session
            Session::flash('_errors', $validator->errors());
            Session::flash('_old_input', $data);

            // Get the referring URL or fallback to /
            $referrer = $_SERVER['HTTP_REFERER'] ?? '/';

            // Return redirect response (will be caught by middleware pipeline)
            throw new ValidationException($this->redirect($referrer));
        }

        return $data;
    }
}
