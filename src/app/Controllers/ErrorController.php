<?php

/**
 * Error Controller
 *
 * Handles error pages (404, 500, 403)
 */
class ErrorController extends Controller
{
    /**
     * Handle 404 Not Found errors
     *
     * @param Request $request
     * @param string $uri Requested URI
     * @return Response
     */
    public function error404(Request $request, string $uri = ''): Response
    {
        $data = [
            'title' => '404 Not Found',
            'code' => '404',
            'heading' => 'Page Not Found',
            'message' => 'The page you are looking for could not be found.',
            'details' => $uri ? "Requested URI: {$uri}" : '',
            'suggestion' => 'Please check the URL or return to the homepage.'
        ];

        return Response::view('errors/404', $data)->setStatus(404);
    }

    /**
     * Handle 500 Internal Server errors
     *
     * @param Request $request
     * @param Exception|null $exception Exception that caused the error
     * @return Response
     */
    public function error500(Request $request, ?Exception $exception = null): Response
    {
        $data = [
            'title' => '500 Internal Server Error',
            'code' => '500',
            'heading' => 'Internal Server Error',
            'message' => 'Something went wrong on our end. We are working to fix it.',
            'details' => '',
            'suggestion' => 'Please try again later or contact support if the problem persists.'
        ];

        // In development mode, show exception details
        if (ini_get('display_errors') && $exception) {
            $data['details'] = $exception->getMessage();
            $data['trace'] = $exception->getTraceAsString();
        }

        return Response::view('errors/500', $data)->setStatus(500);
    }

    /**
     * Handle 403 Forbidden errors
     *
     * @param Request $request
     * @param string $reason Reason for access denial
     * @return Response
     */
    public function error403(Request $request, string $reason = ''): Response
    {
        $data = [
            'title' => '403 Forbidden',
            'code' => '403',
            'heading' => 'Access Denied',
            'message' => 'You do not have permission to access this resource.',
            'details' => $reason,
            'suggestion' => 'Please log in or contact an administrator if you believe this is an error.'
        ];

        return Response::view('errors/403', $data)->setStatus(403);
    }
}
