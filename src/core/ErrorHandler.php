<?php

/**
 * Error Handler
 *
 * Global error and exception handler for the application
 */
class ErrorHandler
{
    /**
     * @var bool Development mode flag
     */
    protected static bool $developmentMode = true;

    /**
     * @var string Log file path
     */
    protected static string $logFile = '';

    /**
     * Register error and exception handlers
     *
     * @param bool $developmentMode Enable development mode
     * @param string $logFile Path to log file
     * @return void
     */
    public static function register(bool $developmentMode = true, string $logFile = ''): void
    {
        self::$developmentMode = $developmentMode;
        self::$logFile = $logFile ?: __DIR__ . '/../logs/error.log';

        // Set error handler
        set_error_handler([self::class, 'handleError']);

        // Set exception handler
        set_exception_handler([self::class, 'handleException']);

        // Set shutdown handler for fatal errors
        register_shutdown_function([self::class, 'handleShutdown']);
    }

    /**
     * Handle PHP errors
     *
     * @param int $errno Error number
     * @param string $errstr Error message
     * @param string $errfile File where error occurred
     * @param int $errline Line where error occurred
     * @return bool
     */
    public static function handleError(int $errno, string $errstr, string $errfile, int $errline): bool
    {
        // Don't handle errors suppressed with @
        if (!(error_reporting() & $errno)) {
            return false;
        }

        $errorType = self::getErrorType($errno);

        // Log the error
        self::logError("[{$errorType}] {$errstr} in {$errfile} on line {$errline}");

        // Convert to ErrorException
        throw new ErrorException($errstr, 0, $errno, $errfile, $errline);
    }

    /**
     * Handle uncaught exceptions
     *
     * @param Throwable $exception
     * @return void
     */
    public static function handleException(Throwable $exception): void
    {
        // Log the exception
        self::logException($exception);

        // Handle ValidationException specially
        if ($exception instanceof ValidationException) {
            $response = $exception->getResponse();
            $response->send();
            exit();
        }

        // Send error response
        self::sendErrorResponse($exception);
    }

    /**
     * Handle fatal errors on shutdown
     *
     * @return void
     */
    public static function handleShutdown(): void
    {
        $error = error_get_last();

        if ($error !== null && in_array($error['type'], [E_ERROR, E_PARSE, E_CORE_ERROR, E_COMPILE_ERROR])) {
            $exception = new ErrorException(
                $error['message'],
                0,
                $error['type'],
                $error['file'],
                $error['line']
            );

            self::logException($exception);
            self::sendErrorResponse($exception);
        }
    }

    /**
     * Send error response to client
     *
     * @param Throwable $exception
     * @return void
     */
    protected static function sendErrorResponse(Throwable $exception): void
    {
        // Prevent any previous output
        if (ob_get_level()) {
            ob_clean();
        }

        // Create error controller
        require_once __DIR__ . '/../app/Controllers/ErrorController.php';
        require_once __DIR__ . '/Request.php';
        require_once __DIR__ . '/Response.php';
        require_once __DIR__ . '/Controller.php';
        require_once __DIR__ . '/View.php';

        $errorController = new ErrorController();
        $request = Request::capture();

        try {
            $response = $errorController->error500($request, $exception);
            $response->send();
        } catch (Exception $e) {
            // Fallback if error page fails
            http_response_code(500);
            echo self::$developmentMode
                ? "<h1>Error</h1><p>{$exception->getMessage()}</p><pre>{$exception->getTraceAsString()}</pre>"
                : "<h1>500 Internal Server Error</h1><p>An error occurred. Please try again later.</p>";
        }

        exit();
    }

    /**
     * Log an error message
     *
     * @param string $message Error message
     * @return void
     */
    protected static function logError(string $message): void
    {
        $timestamp = date('Y-m-d H:i:s');
        $logMessage = "[{$timestamp}] {$message}\n";

        // Create logs directory if it doesn't exist
        $logDir = dirname(self::$logFile);
        if (!is_dir($logDir)) {
            @mkdir($logDir, 0755, true);
        }

        @error_log($logMessage, 3, self::$logFile);
    }

    /**
     * Log an exception
     *
     * @param Throwable $exception
     * @return void
     */
    protected static function logException(Throwable $exception): void
    {
        $message = sprintf(
            "[%s] %s in %s:%d\nStack trace:\n%s",
            get_class($exception),
            $exception->getMessage(),
            $exception->getFile(),
            $exception->getLine(),
            $exception->getTraceAsString()
        );

        self::logError($message);
    }

    /**
     * Get error type name
     *
     * @param int $errno Error number
     * @return string
     */
    protected static function getErrorType(int $errno): string
    {
        $types = [
            E_ERROR => 'ERROR',
            E_WARNING => 'WARNING',
            E_PARSE => 'PARSE',
            E_NOTICE => 'NOTICE',
            E_CORE_ERROR => 'CORE_ERROR',
            E_CORE_WARNING => 'CORE_WARNING',
            E_COMPILE_ERROR => 'COMPILE_ERROR',
            E_COMPILE_WARNING => 'COMPILE_WARNING',
            E_USER_ERROR => 'USER_ERROR',
            E_USER_WARNING => 'USER_WARNING',
            E_USER_NOTICE => 'USER_NOTICE',
            E_STRICT => 'STRICT',
            E_RECOVERABLE_ERROR => 'RECOVERABLE_ERROR',
            E_DEPRECATED => 'DEPRECATED',
            E_USER_DEPRECATED => 'USER_DEPRECATED',
        ];

        return $types[$errno] ?? 'UNKNOWN';
    }
}
