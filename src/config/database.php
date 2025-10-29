<?php

/**
 * Database Configuration
 *
 * This file contains all database-related configuration settings.
 * Credentials are loaded from environment variables for security.
 */

return [
    // Database connection settings
    'host' => 'ada_db', // Docker service name
    'database' => getenv('DB_NAME') ?: 'ada',
    'username' => getenv('DB_USER') ?: 'ada',
    'password' => getenv('DB_PASS') ?: 'ada_pwd',
    'charset' => 'utf8mb4',
    'collation' => 'utf8mb4_unicode_ci',

    // PDO options for security and performance
    'options' => [
        PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
        PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
        PDO::ATTR_EMULATE_PREPARES => false,
        PDO::ATTR_STRINGIFY_FETCHES => false,
    ],
];
