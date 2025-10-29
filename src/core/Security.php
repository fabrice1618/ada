<?php

/**
 * Security Class
 *
 * Provides security features including CSRF protection, XSS prevention, and input sanitization
 */
class Security
{
    /**
     * Generate a CSRF token
     *
     * @return string
     */
    public static function generateCsrfToken(): string
    {
        if (!Session::has('_csrf_token')) {
            $token = bin2hex(random_bytes(32));
            Session::set('_csrf_token', $token);
        }

        return Session::get('_csrf_token');
    }

    /**
     * Get the current CSRF token
     *
     * @return string|null
     */
    public static function getCsrfToken(): ?string
    {
        return Session::get('_csrf_token');
    }

    /**
     * Validate a CSRF token
     *
     * @param string $token Token to validate
     * @return bool
     */
    public static function validateCsrfToken(string $token): bool
    {
        $sessionToken = Session::get('_csrf_token');

        if (!$sessionToken) {
            return false;
        }

        // Use timing-safe comparison to prevent timing attacks
        $valid = hash_equals($sessionToken, $token);

        // Regenerate token after validation for added security
        if ($valid) {
            self::regenerateCsrfToken();
        }

        return $valid;
    }

    /**
     * Regenerate the CSRF token
     *
     * @return string New token
     */
    public static function regenerateCsrfToken(): string
    {
        $token = bin2hex(random_bytes(32));
        Session::set('_csrf_token', $token);
        return $token;
    }

    /**
     * Sanitize a string value
     *
     * @param string $value Value to sanitize
     * @param bool $stripTags Whether to strip HTML tags
     * @return string
     */
    public static function sanitize(string $value, bool $stripTags = false): string
    {
        // Trim whitespace
        $value = trim($value);

        // Remove null bytes
        $value = str_replace("\0", '', $value);

        // Strip HTML tags if requested
        if ($stripTags) {
            $value = strip_tags($value);
        }

        return $value;
    }

    /**
     * Sanitize an array of values
     *
     * @param array $data Array to sanitize
     * @param bool $stripTags Whether to strip HTML tags
     * @return array
     */
    public static function sanitizeArray(array $data, bool $stripTags = false): array
    {
        $sanitized = [];

        foreach ($data as $key => $value) {
            if (is_array($value)) {
                $sanitized[$key] = self::sanitizeArray($value, $stripTags);
            } elseif (is_string($value)) {
                $sanitized[$key] = self::sanitize($value, $stripTags);
            } else {
                $sanitized[$key] = $value;
            }
        }

        return $sanitized;
    }

    /**
     * Escape HTML special characters
     *
     * @param string $value Value to escape
     * @return string
     */
    public static function escape(string $value): string
    {
        return htmlspecialchars($value, ENT_QUOTES, 'UTF-8');
    }

    /**
     * Escape for JavaScript context
     *
     * @param string $value Value to escape
     * @return string
     */
    public static function escapeJs(string $value): string
    {
        return json_encode($value, JSON_HEX_TAG | JSON_HEX_AMP | JSON_HEX_APOS | JSON_HEX_QUOT);
    }

    /**
     * Escape for URL context
     *
     * @param string $value Value to escape
     * @return string
     */
    public static function escapeUrl(string $value): string
    {
        return urlencode($value);
    }

    /**
     * Hash a password
     *
     * @param string $password Password to hash
     * @return string
     */
    public static function hashPassword(string $password): string
    {
        return password_hash($password, PASSWORD_BCRYPT);
    }

    /**
     * Verify a password against a hash
     *
     * @param string $password Plain text password
     * @param string $hash Password hash
     * @return bool
     */
    public static function verifyPassword(string $password, string $hash): bool
    {
        return password_verify($password, $hash);
    }
}
