<?php

/**
 * Session Management Class
 *
 * Handles secure session operations with flash message support
 */
class Session
{
    /**
     * Start a secure session
     *
     * @return void
     */
    public static function start(): void
    {
        if (session_status() === PHP_SESSION_NONE) {
            // Set secure session configuration
            ini_set('session.cookie_httponly', '1');
            ini_set('session.cookie_samesite', 'Strict');

            // Use secure cookies if HTTPS is available
            if (isset($_SERVER['HTTPS']) && $_SERVER['HTTPS'] === 'on') {
                ini_set('session.cookie_secure', '1');
            }

            // Use strict session ID generation
            ini_set('session.use_strict_mode', '1');
            ini_set('session.use_only_cookies', '1');

            session_start();

            // Regenerate session ID on first access
            if (!self::has('_session_started')) {
                session_regenerate_id(true);
                self::set('_session_started', true);
                self::set('_session_created', time());
            }

            // Check for session timeout (30 minutes)
            if (self::has('_last_activity')) {
                $timeout = 1800; // 30 minutes
                if (time() - self::get('_last_activity') > $timeout) {
                    self::destroy();
                    self::start();
                }
            }

            // Update last activity timestamp
            self::set('_last_activity', time());
        }
    }

    /**
     * Set a session value
     *
     * @param string $key
     * @param mixed $value
     * @return void
     */
    public static function set(string $key, $value): void
    {
        $_SESSION[$key] = $value;
    }

    /**
     * Get a session value
     *
     * @param string $key
     * @param mixed $default
     * @return mixed
     */
    public static function get(string $key, $default = null)
    {
        return $_SESSION[$key] ?? $default;
    }

    /**
     * Check if session key exists
     *
     * @param string $key
     * @return bool
     */
    public static function has(string $key): bool
    {
        return isset($_SESSION[$key]);
    }

    /**
     * Remove a session value
     *
     * @param string $key
     * @return void
     */
    public static function remove(string $key): void
    {
        if (isset($_SESSION[$key])) {
            unset($_SESSION[$key]);
        }
    }

    /**
     * Destroy the session
     *
     * @return void
     */
    public static function destroy(): void
    {
        $_SESSION = [];

        // Delete session cookie
        if (ini_get('session.use_cookies')) {
            $params = session_get_cookie_params();
            setcookie(
                session_name(),
                '',
                time() - 42000,
                $params['path'],
                $params['domain'],
                $params['secure'],
                $params['httponly']
            );
        }

        session_destroy();
    }

    /**
     * Set a flash message
     *
     * @param string $key
     * @param mixed $value
     * @return void
     */
    public static function flash(string $key, $value): void
    {
        $_SESSION['_flash'][$key] = $value;
    }

    /**
     * Get a flash message and remove it
     *
     * @param string $key
     * @param mixed $default
     * @return mixed
     */
    public static function getFlash(string $key, $default = null)
    {
        if (isset($_SESSION['_flash'][$key])) {
            $value = $_SESSION['_flash'][$key];
            unset($_SESSION['_flash'][$key]);
            return $value;
        }

        return $default;
    }

    /**
     * Check if a flash message exists
     *
     * @param string $key
     * @return bool
     */
    public static function hasFlash(string $key): bool
    {
        return isset($_SESSION['_flash'][$key]);
    }

    /**
     * Get all flash messages and clear them
     *
     * @return array
     */
    public static function getAllFlash(): array
    {
        $flash = $_SESSION['_flash'] ?? [];
        unset($_SESSION['_flash']);
        return $flash;
    }

    /**
     * Regenerate session ID
     *
     * @return void
     */
    public static function regenerate(): void
    {
        session_regenerate_id(true);
    }
}
