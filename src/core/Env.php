<?php

/**
 * Environment Configuration Loader
 *
 * Simple .env file parser that loads environment variables.
 * Supports basic key=value format with comments and empty lines.
 */
class Env
{
    /**
     * Load environment variables from .env file
     *
     * @param string $path Path to .env file
     * @return bool True if loaded successfully
     */
    public static function load(string $path): bool
    {
        if (!file_exists($path)) {
            error_log("ENV file not found: {$path}");
            return false;
        }

        if (!is_readable($path)) {
            error_log("ENV file not readable: {$path}");
            return false;
        }

        $lines = file($path, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);

        if ($lines === false) {
            error_log("Failed to read ENV file: {$path}");
            return false;
        }

        foreach ($lines as $line) {
            // Skip comments and empty lines
            $line = trim($line);
            if (empty($line) || $line[0] === '#') {
                continue;
            }

            // Parse key=value
            if (strpos($line, '=') === false) {
                continue;
            }

            list($key, $value) = self::parseLine($line);

            if ($key !== null) {
                // Don't override existing environment variables
                if (getenv($key) === false) {
                    putenv("{$key}={$value}");
                    $_ENV[$key] = $value;
                    $_SERVER[$key] = $value;
                }
            }
        }

        return true;
    }

    /**
     * Parse a single line from .env file
     *
     * @param string $line Line to parse
     * @return array [key, value] or [null, null] if invalid
     */
    private static function parseLine(string $line): array
    {
        $parts = explode('=', $line, 2);

        if (count($parts) !== 2) {
            return [null, null];
        }

        $key = trim($parts[0]);
        $value = trim($parts[1]);

        // Remove quotes if present
        if (strlen($value) > 1) {
            $firstChar = $value[0];
            $lastChar = $value[strlen($value) - 1];

            if (($firstChar === '"' && $lastChar === '"') ||
                ($firstChar === "'" && $lastChar === "'")) {
                $value = substr($value, 1, -1);
            }
        }

        // Handle escaped characters
        $value = str_replace(['\n', '\r', '\t'], ["\n", "\r", "\t"], $value);

        return [$key, $value];
    }

    /**
     * Get an environment variable
     *
     * @param string $key Variable name
     * @param mixed $default Default value if not found
     * @return mixed Variable value or default
     */
    public static function get(string $key, $default = null)
    {
        $value = getenv($key);

        if ($value === false) {
            return $default;
        }

        // Convert string booleans to actual booleans
        $lower = strtolower($value);
        if ($lower === 'true') {
            return true;
        }
        if ($lower === 'false') {
            return false;
        }
        if ($lower === 'null') {
            return null;
        }

        return $value;
    }

    /**
     * Check if an environment variable exists
     *
     * @param string $key Variable name
     * @return bool True if exists
     */
    public static function has(string $key): bool
    {
        return getenv($key) !== false;
    }

    /**
     * Set an environment variable
     *
     * @param string $key Variable name
     * @param string $value Variable value
     * @return void
     */
    public static function set(string $key, string $value): void
    {
        putenv("{$key}={$value}");
        $_ENV[$key] = $value;
        $_SERVER[$key] = $value;
    }
}
