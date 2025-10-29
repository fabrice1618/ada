<?php

/**
 * Database Connection Manager
 *
 * Implements the Singleton pattern to ensure only one database connection
 * exists throughout the application lifecycle.
 */
class Database
{
    /**
     * Singleton instance
     *
     * @var Database|null
     */
    private static ?Database $instance = null;

    /**
     * PDO connection instance
     *
     * @var PDO|null
     */
    private ?PDO $connection = null;

    /**
     * Database configuration
     *
     * @var array
     */
    private array $config;

    /**
     * Private constructor to prevent direct instantiation
     */
    private function __construct()
    {
        $this->config = require __DIR__ . '/../config/database.php';
        $this->connect();
    }

    /**
     * Prevent cloning of the instance
     */
    private function __clone()
    {
    }

    /**
     * Prevent unserialization of the instance
     */
    public function __wakeup()
    {
        throw new Exception("Cannot unserialize singleton");
    }

    /**
     * Get the singleton instance
     *
     * @return Database
     */
    public static function getInstance(): Database
    {
        if (self::$instance === null) {
            self::$instance = new self();
        }

        return self::$instance;
    }

    /**
     * Establish database connection
     *
     * @return void
     * @throws PDOException
     */
    private function connect(): void
    {
        try {
            $dsn = sprintf(
                'mysql:host=%s;dbname=%s;charset=%s',
                $this->config['host'],
                $this->config['database'],
                $this->config['charset']
            );

            $this->connection = new PDO(
                $dsn,
                $this->config['username'],
                $this->config['password'],
                $this->config['options']
            );

            // Set charset for the connection
            $this->connection->exec("SET NAMES '{$this->config['charset']}' COLLATE '{$this->config['collation']}'");
        } catch (PDOException $e) {
            // Log the error (in production, don't expose details)
            if (class_exists('Logger')) {
                Logger::critical("Database connection failed: " . $e->getMessage(), ['exception' => $e]);
            } else {
                error_log("Database connection failed: " . $e->getMessage());
            }
            throw new PDOException("Database connection failed. Please check configuration.");
        }
    }

    /**
     * Get the PDO connection instance
     *
     * @return PDO
     */
    public function getConnection(): PDO
    {
        // Reconnect if connection was lost
        if ($this->connection === null) {
            $this->connect();
        }

        return $this->connection;
    }

    /**
     * Close the database connection
     *
     * @return void
     */
    public function closeConnection(): void
    {
        $this->connection = null;
    }
}
