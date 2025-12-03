<?php

/**
 * Configuration Management Class
 *
 * Provides centralized configuration management with dot notation access.
 * Loads and caches configuration files from the config directory.
 *
 * Usage:
 *   Config::load('app');
 *   $name = Config::get('app.name');
 *   $debug = Config::get('app.debug', false);
 */
class Config
{
    /**
     * Loaded configuration data
     *
     * @var array
     */
    private static $config = [];

    /**
     * Cache of loaded files to prevent re-loading
     *
     * @var array
     */
    private static $loaded = [];

    /**
     * Load a configuration file
     *
     * @param string $file Configuration file name (without .php extension)
     * @return bool True if loaded successfully
     */
    public static function load(string $file): bool
    {
        // Prevent loading the same file twice
        if (isset(self::$loaded[$file])) {
            return true;
        }

        $path = __DIR__ . '/../config/' . $file . '.php';

        if (!file_exists($path)) {
            error_log("Config file not found: {$path}");
            return false;
        }

        $data = require $path;

        if (!is_array($data)) {
            error_log("Config file must return an array: {$path}");
            return false;
        }

        self::$config[$file] = $data;
        self::$loaded[$file] = true;

        return true;
    }

    /**
     * Get a configuration value using dot notation
     *
     * Supports nested access like 'database.host' or 'app.debug'
     *
     * @param string $key Configuration key in dot notation
     * @param mixed $default Default value if key not found
     * @return mixed Configuration value or default
     */
    public static function get(string $key, $default = null)
    {
        $keys = explode('.', $key);
        $file = array_shift($keys);

        // Auto-load config file if not loaded
        if (!isset(self::$loaded[$file])) {
            self::load($file);
        }

        // If file doesn't exist, return default
        if (!isset(self::$config[$file])) {
            return $default;
        }

        $value = self::$config[$file];

        // Navigate through nested keys
        foreach ($keys as $segment) {
            if (!is_array($value) || !array_key_exists($segment, $value)) {
                return $default;
            }
            $value = $value[$segment];
        }

        return $value;
    }

    /**
     * Set a configuration value at runtime
     *
     * @param string $key Configuration key in dot notation
     * @param mixed $value Value to set
     * @return void
     */
    public static function set(string $key, $value): void
    {
        $keys = explode('.', $key);
        $file = array_shift($keys);

        // Ensure file config exists
        if (!isset(self::$config[$file])) {
            self::$config[$file] = [];
            self::$loaded[$file] = true;
        }

        // Navigate to the correct nested location
        $target = &self::$config[$file];

        foreach ($keys as $segment) {
            if (!isset($target[$segment]) || !is_array($target[$segment])) {
                $target[$segment] = [];
            }
            $target = &$target[$segment];
        }

        $target = $value;
    }

    /**
     * Check if a configuration key exists
     *
     * @param string $key Configuration key in dot notation
     * @return bool True if key exists
     */
    public static function has(string $key): bool
    {
        $keys = explode('.', $key);
        $file = array_shift($keys);

        // Auto-load config file if not loaded
        if (!isset(self::$loaded[$file])) {
            self::load($file);
        }

        if (!isset(self::$config[$file])) {
            return false;
        }

        $value = self::$config[$file];

        foreach ($keys as $segment) {
            if (!is_array($value) || !array_key_exists($segment, $value)) {
                return false;
            }
            $value = $value[$segment];
        }

        return true;
    }

    /**
     * Get all configuration for a specific file
     *
     * @param string $file Configuration file name
     * @return array Configuration data
     */
    public static function all(string $file): array
    {
        if (!isset(self::$loaded[$file])) {
            self::load($file);
        }

        return self::$config[$file] ?? [];
    }

    /**
     * Clear all loaded configuration (useful for testing)
     *
     * @return void
     */
    public static function clear(): void
    {
        self::$config = [];
        self::$loaded = [];
    }

    /**
     * Load all configuration files from config directory
     *
     * @return void
     */
    public static function loadAll(): void
    {
        $configDir = __DIR__ . '/../config/';

        if (!is_dir($configDir)) {
            return;
        }

        $files = glob($configDir . '*.php');

        foreach ($files as $file) {
            $name = basename($file, '.php');
            self::load($name);
        }
    }
}
