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
