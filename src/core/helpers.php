<?php

/**
 * Global Helper Functions
 *
 * Provides convenient global functions for common tasks
 */

/**
 * Escape HTML for safe output
 *
 * @param string $value Value to escape
 * @return string
 */
function e(string $value): string
{
    return Security::escape($value);
}

/**
 * Alias for e() function
 *
 * @param string $value Value to escape
 * @return string
 */
function escape(string $value): string
{
    return Security::escape($value);
}

/**
 * Escape for JavaScript context
 *
 * @param string $value Value to escape
 * @return string
 */
function escapeJs(string $value): string
{
    return Security::escapeJs($value);
}

/**
 * Escape for URL context
 *
 * @param string $value Value to escape
 * @return string
 */
function escapeUrl(string $value): string
{
    return Security::escapeUrl($value);
}

/**
 * Generate CSRF token hidden input field
 *
 * @return string HTML hidden input field
 */
function csrfField(): string
{
    $token = Security::generateCsrfToken();
    return '<input type="hidden" name="_csrf_token" value="' . e($token) . '">';
}

/**
 * Get the current CSRF token value
 *
 * @return string|null
 */
function csrfToken(): ?string
{
    return Security::getCsrfToken();
}

/**
 * Generate CSRF meta tag for AJAX requests
 *
 * @return string HTML meta tag
 */
function csrfMeta(): string
{
    $token = Security::generateCsrfToken();
    return '<meta name="csrf-token" content="' . e($token) . '">';
}

/**
 * Get old input value (from flash session)
 *
 * @param string $key Input field name
 * @param mixed $default Default value
 * @return mixed
 */
function old(string $key, $default = '')
{
    $oldInput = Session::getFlash('_old_input', []);
    return $oldInput[$key] ?? $default;
}

/**
 * Generate a URL for a given path
 *
 * @param string $path Path to append to base URL
 * @return string
 */
function url(string $path = ''): string
{
    $protocol = isset($_SERVER['HTTPS']) && $_SERVER['HTTPS'] === 'on' ? 'https' : 'http';
    $host = $_SERVER['HTTP_HOST'] ?? 'localhost';
    $basePath = rtrim($path, '/');

    return $protocol . '://' . $host . $basePath;
}

/**
 * Generate a URL for a public asset
 *
 * @param string $path Path to asset
 * @return string
 */
function asset(string $path): string
{
    return url('/' . ltrim($path, '/'));
}

/**
 * Redirect to a URL
 *
 * @param string $url URL to redirect to
 * @param int $statusCode HTTP status code
 * @return void
 */
function redirect(string $url, int $statusCode = 302): void
{
    header('Location: ' . $url, true, $statusCode);
    exit();
}

/**
 * Redirect back to previous page
 *
 * @return void
 */
function back(): void
{
    $referer = $_SERVER['HTTP_REFERER'] ?? '/';
    redirect($referer);
}

/**
 * Dump and die (for debugging)
 *
 * @param mixed ...$vars Variables to dump
 * @return void
 */
function dd(...$vars): void
{
    echo '<pre>';
    foreach ($vars as $var) {
        var_dump($var);
    }
    echo '</pre>';
    die();
}

/**
 * Render a view and return response
 *
 * @param string $template Template name
 * @param array $data Data to pass to view
 * @return Response
 */
function view(string $template, array $data = []): Response
{
    $view = new View();
    $content = $view->render($template, $data);

    $response = new Response();
    $response->setContent($content);
    return $response;
}

/**
 * Get a configuration value
 *
 * @param string $key Configuration key (dot notation)
 * @param mixed $default Default value
 * @return mixed
 */
function config(string $key, $default = null)
{
    if (class_exists('Config')) {
        return Config::get($key, $default);
    }
    return $default;
}

/**
 * Get environment variable
 *
 * @param string $key Variable name
 * @param mixed $default Default value
 * @return mixed
 */
function env(string $key, $default = null)
{
    if (class_exists('Env')) {
        return Env::get($key, $default);
    }
    return getenv($key) ?: $default;
}

/**
 * Generate URL for named route
 *
 * @param string $name Route name
 * @param array $params Route parameters
 * @return string
 */
function route(string $name, array $params = []): string
{
    global $router;
    if (isset($router) && method_exists($router, 'route')) {
        return $router->route($name, $params);
    }
    throw new Exception("Router not available for route generation");
}

/**
 * Get or set session value
 *
 * @param string|null $key Session key
 * @param mixed $default Default value
 * @return mixed
 */
function session(?string $key = null, $default = null)
{
    if ($key === null) {
        return Session::all();
    }
    return Session::get($key, $default);
}

/**
 * Get flash message
 *
 * @param string $key Flash message key
 * @param mixed $default Default value
 * @return mixed
 */
function flash(string $key, $default = null)
{
    return Session::getFlash($key, $default);
}

/**
 * Log a message
 *
 * @param string $level Log level
 * @param string $message Log message
 * @param array $context Context data
 * @return void
 */
function logger(string $level, string $message, array $context = []): void
{
    if (class_exists('Logger')) {
        Logger::log($level, $message, $context);
    } else {
        error_log("[{$level}] {$message}");
    }
}

/**
 * Abort with HTTP error
 *
 * @param int $code HTTP status code
 * @param string $message Error message
 * @return never
 */
function abort(int $code, string $message = ''): never
{
    http_response_code($code);

    if (empty($message)) {
        $messages = [
            400 => 'Bad Request',
            403 => 'Forbidden',
            404 => 'Not Found',
            500 => 'Internal Server Error',
        ];
        $message = $messages[$code] ?? 'Error';
    }

    echo "<h1>{$code}</h1><p>{$message}</p>";
    exit();
}

/**
 * Check if request is POST
 *
 * @return bool
 */
function isPost(): bool
{
    return $_SERVER['REQUEST_METHOD'] === 'POST';
}

/**
 * Check if request is GET
 *
 * @return bool
 */
function isGet(): bool
{
    return $_SERVER['REQUEST_METHOD'] === 'GET';
}

/**
 * Check if request is AJAX
 *
 * @return bool
 */
function isAjax(): bool
{
    return !empty($_SERVER['HTTP_X_REQUESTED_WITH']) &&
           strtolower($_SERVER['HTTP_X_REQUESTED_WITH']) === 'xmlhttprequest';
}

/**
 * Get client IP address
 *
 * @return string
 */
function getClientIp(): string
{
    if (!empty($_SERVER['HTTP_CLIENT_IP'])) {
        return $_SERVER['HTTP_CLIENT_IP'];
    } elseif (!empty($_SERVER['HTTP_X_FORWARDED_FOR'])) {
        $ips = explode(',', $_SERVER['HTTP_X_FORWARDED_FOR']);
        return trim($ips[0]);
    } elseif (!empty($_SERVER['REMOTE_ADDR'])) {
        return $_SERVER['REMOTE_ADDR'];
    }
    return '0.0.0.0';
}

/**
 * Sanitize string for safe usage
 *
 * @param string $value Value to sanitize
 * @return string
 */
function sanitize(string $value): string
{
    if (class_exists('Security')) {
        return Security::sanitize($value);
    }
    return htmlspecialchars(trim($value), ENT_QUOTES, 'UTF-8');
}

/**
 * Convert array to JSON response
 *
 * @param mixed $data Data to convert
 * @param int $status HTTP status code
 * @return Response
 */
function json($data, int $status = 200): Response
{
    return Response::json($data, $status);
}
