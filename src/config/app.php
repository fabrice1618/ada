<?php

/**
 * Application Configuration
 *
 * Core application settings including environment, debugging, timezone, and logging.
 */

return [
    /*
    |--------------------------------------------------------------------------
    | Application Name
    |--------------------------------------------------------------------------
    |
    | This value is the name of your application. It can be used when you
    | need to display the application name in views or notifications.
    |
    */
    'name' => getenv('APP_NAME') ?: 'ADA Framework',

    /*
    |--------------------------------------------------------------------------
    | Application Environment
    |--------------------------------------------------------------------------
    |
    | This value determines the "environment" your application is currently
    | running in. This may determine how you prefer to configure various
    | services your application uses. Set in .env file.
    |
    | Supported: "development", "production", "testing"
    |
    */
    'env' => getenv('APP_ENV') ?: 'development',

    /*
    |--------------------------------------------------------------------------
    | Debug Mode
    |--------------------------------------------------------------------------
    |
    | When debug mode is enabled, detailed error messages with stack traces
    | will be shown on every error. If disabled, a simple generic error page
    | will be shown. Never enable debug mode in production!
    |
    */
    'debug' => getenv('APP_DEBUG') === 'true' || getenv('APP_DEBUG') === '1',

    /*
    |--------------------------------------------------------------------------
    | Application URL
    |--------------------------------------------------------------------------
    |
    | This URL is used by the console to properly generate URLs when using
    | the command line tool. You should set this to the root of your
    | application so that it is used when running commands.
    |
    */
    'url' => getenv('APP_URL') ?: 'http://localhost:8080',

    /*
    |--------------------------------------------------------------------------
    | Application Timezone
    |--------------------------------------------------------------------------
    |
    | Here you may specify the default timezone for your application, which
    | will be used by the PHP date and date-time functions.
    |
    */
    'timezone' => getenv('APP_TIMEZONE') ?: 'UTC',

    /*
    |--------------------------------------------------------------------------
    | Application Locale
    |--------------------------------------------------------------------------
    |
    | The application locale determines the default locale that will be used
    | by localization services (if implemented).
    |
    */
    'locale' => getenv('APP_LOCALE') ?: 'en',

    /*
    |--------------------------------------------------------------------------
    | Application Charset
    |--------------------------------------------------------------------------
    |
    | The charset used by the application for encoding/decoding strings.
    |
    */
    'charset' => 'UTF-8',

    /*
    |--------------------------------------------------------------------------
    | Logging Configuration
    |--------------------------------------------------------------------------
    |
    | Configure logging behavior including log file location and level.
    |
    | Levels: emergency, alert, critical, error, warning, notice, info, debug
    |
    */
    'log' => [
        'path' => __DIR__ . '/../logs/app.log',
        'level' => getenv('LOG_LEVEL') ?: 'info',
        'max_files' => 30, // Maximum number of daily log files to keep
    ],

    /*
    |--------------------------------------------------------------------------
    | Error Display
    |--------------------------------------------------------------------------
    |
    | Control whether errors should be displayed to the user. Should be
    | disabled in production for security reasons.
    |
    */
    'display_errors' => getenv('APP_ENV') === 'development',

    /*
    |--------------------------------------------------------------------------
    | Session Configuration
    |--------------------------------------------------------------------------
    |
    | Session settings including lifetime, cookie settings, etc.
    |
    */
    'session' => [
        'lifetime' => 7200, // 2 hours in seconds
        'cookie_name' => 'ada_session',
        'cookie_path' => '/',
        'cookie_domain' => '',
        'cookie_secure' => getenv('SESSION_SECURE') === 'true', // true for HTTPS only
        'cookie_httponly' => true,
        'cookie_samesite' => 'Lax', // Lax, Strict, or None
    ],

    /*
    |--------------------------------------------------------------------------
    | Security Configuration
    |--------------------------------------------------------------------------
    |
    | Security-related settings for the application.
    |
    */
    'security' => [
        'csrf_token_name' => '_token',
        'hash_algorithm' => PASSWORD_BCRYPT,
        'hash_cost' => 12,
    ],

    /*
    |--------------------------------------------------------------------------
    | View Configuration
    |--------------------------------------------------------------------------
    |
    | Settings for the view/template system.
    |
    */
    'views' => [
        'cache_enabled' => getenv('VIEW_CACHE') === 'true',
        'cache_path' => __DIR__ . '/../cache/views',
    ],

    /*
    |--------------------------------------------------------------------------
    | Maintenance Mode
    |--------------------------------------------------------------------------
    |
    | When enabled, the application will display a maintenance page to all
    | visitors except those from whitelisted IP addresses.
    |
    */
    'maintenance' => [
        'enabled' => getenv('MAINTENANCE_MODE') === 'true',
        'whitelist' => [], // Array of IP addresses allowed during maintenance
    ],

    /*
    |--------------------------------------------------------------------------
    | Performance Settings
    |--------------------------------------------------------------------------
    |
    | Performance-related configuration options.
    |
    */
    'performance' => [
        'cache_config' => getenv('APP_ENV') === 'production',
        'cache_routes' => getenv('APP_ENV') === 'production',
        'lazy_load_db' => true,
    ],
];
