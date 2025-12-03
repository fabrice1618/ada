<?php

/**
 * Logging System
 *
 * PSR-3 compatible logging with multiple log levels.
 * Writes logs to files with automatic rotation by date.
 */
class Logger
{
    /**
     * Log levels according to PSR-3
     */
    const EMERGENCY = 'emergency';
    const ALERT     = 'alert';
    const CRITICAL  = 'critical';
    const ERROR     = 'error';
    const WARNING   = 'warning';
    const NOTICE    = 'notice';
    const INFO      = 'info';
    const DEBUG     = 'debug';

    /**
     * Log level priorities (lower = more severe)
     *
     * @var array
     */
    private static $levels = [
        self::EMERGENCY => 0,
        self::ALERT     => 1,
        self::CRITICAL  => 2,
        self::ERROR     => 3,
        self::WARNING   => 4,
        self::NOTICE    => 5,
        self::INFO      => 6,
        self::DEBUG     => 7,
    ];

    /**
     * Current log level threshold
     *
     * @var string
     */
    private static $threshold = self::INFO;

    /**
     * Log file path
     *
     * @var string
     */
    private static $logPath;

    /**
     * Initialize logger with configuration
     *
     * @param string $path Log file path
     * @param string $level Minimum log level
     * @return void
     */
    public static function init(string $path, string $level = self::INFO): void
    {
        self::$logPath = $path;
        self::$threshold = $level;

        // Ensure log directory exists
        $dir = dirname($path);
        if (!is_dir($dir)) {
            @mkdir($dir, 0755, true);
        }
    }

    /**
     * Log a message at specified level
     *
     * @param string $level Log level
     * @param string $message Log message
     * @param array $context Additional context data
     * @return bool True if logged successfully
     */
    public static function log(string $level, string $message, array $context = []): bool
    {
        // Check if level should be logged
        if (!self::shouldLog($level)) {
            return false;
        }

        // Format the log entry
        $entry = self::formatEntry($level, $message, $context);

        // Write to log file
        return self::write($entry);
    }

    /**
     * Emergency: System is unusable
     *
     * @param string $message Log message
     * @param array $context Additional context
     * @return bool True if logged
     */
    public static function emergency(string $message, array $context = []): bool
    {
        return self::log(self::EMERGENCY, $message, $context);
    }

    /**
     * Alert: Action must be taken immediately
     *
     * @param string $message Log message
     * @param array $context Additional context
     * @return bool True if logged
     */
    public static function alert(string $message, array $context = []): bool
    {
        return self::log(self::ALERT, $message, $context);
    }

    /**
     * Critical: Critical conditions
     *
     * @param string $message Log message
     * @param array $context Additional context
     * @return bool True if logged
     */
    public static function critical(string $message, array $context = []): bool
    {
        return self::log(self::CRITICAL, $message, $context);
    }

    /**
     * Error: Runtime errors that don't require immediate action
     *
     * @param string $message Log message
     * @param array $context Additional context
     * @return bool True if logged
     */
    public static function error(string $message, array $context = []): bool
    {
        return self::log(self::ERROR, $message, $context);
    }

    /**
     * Warning: Exceptional occurrences that are not errors
     *
     * @param string $message Log message
     * @param array $context Additional context
     * @return bool True if logged
     */
    public static function warning(string $message, array $context = []): bool
    {
        return self::log(self::WARNING, $message, $context);
    }

    /**
     * Notice: Normal but significant events
     *
     * @param string $message Log message
     * @param array $context Additional context
     * @return bool True if logged
     */
    public static function notice(string $message, array $context = []): bool
    {
        return self::log(self::NOTICE, $message, $context);
    }

    /**
     * Info: Interesting events
     *
     * @param string $message Log message
     * @param array $context Additional context
     * @return bool True if logged
     */
    public static function info(string $message, array $context = []): bool
    {
        return self::log(self::INFO, $message, $context);
    }

    /**
     * Debug: Detailed debug information
     *
     * @param string $message Log message
     * @param array $context Additional context
     * @return bool True if logged
     */
    public static function debug(string $message, array $context = []): bool
    {
        return self::log(self::DEBUG, $message, $context);
    }

    /**
     * Check if a log level should be logged based on threshold
     *
     * @param string $level Log level to check
     * @return bool True if should log
     */
    private static function shouldLog(string $level): bool
    {
        if (!isset(self::$levels[$level]) || !isset(self::$levels[self::$threshold])) {
            return false;
        }

        return self::$levels[$level] <= self::$levels[self::$threshold];
    }

    /**
     * Format a log entry
     *
     * @param string $level Log level
     * @param string $message Log message
     * @param array $context Additional context
     * @return string Formatted log entry
     */
    private static function formatEntry(string $level, string $message, array $context = []): string
    {
        $timestamp = date('Y-m-d H:i:s');
        $level = strtoupper($level);

        // Replace context placeholders in message
        $message = self::interpolate($message, $context);

        // Format entry
        $entry = "[{$timestamp}] {$level}: {$message}";

        // Add context if any remains
        if (!empty($context)) {
            $entry .= ' ' . json_encode($context, JSON_UNESCAPED_SLASHES);
        }

        // Add exception trace if present
        if (isset($context['exception']) && $context['exception'] instanceof Throwable) {
            $entry .= "\n" . $context['exception']->getTraceAsString();
        }

        return $entry . PHP_EOL;
    }

    /**
     * Interpolate context values into message placeholders
     *
     * @param string $message Message with {placeholders}
     * @param array $context Context values
     * @return string Interpolated message
     */
    private static function interpolate(string $message, array &$context): string
    {
        $replace = [];

        foreach ($context as $key => $val) {
            // Skip exception objects
            if ($key === 'exception') {
                continue;
            }

            // Build replacement array
            if (is_scalar($val) || (is_object($val) && method_exists($val, '__toString'))) {
                $replace['{' . $key . '}'] = $val;
                unset($context[$key]); // Remove from context after interpolation
            }
        }

        return strtr($message, $replace);
    }

    /**
     * Write log entry to file
     *
     * @param string $entry Formatted log entry
     * @return bool True if written successfully
     */
    private static function write(string $entry): bool
    {
        if (empty(self::$logPath)) {
            // Initialize with default path if not set
            self::init(__DIR__ . '/../logs/app.log');
        }

        // Add date to log filename for daily rotation
        $pathInfo = pathinfo(self::$logPath);
        $date = date('Y-m-d');
        $logFile = $pathInfo['dirname'] . '/' . $pathInfo['filename'] . '-' . $date . '.' . $pathInfo['extension'];

        // Ensure log directory exists
        $dir = dirname($logFile);
        if (!is_dir($dir)) {
            @mkdir($dir, 0755, true);
        }

        // Write to log file
        $result = @file_put_contents($logFile, $entry, FILE_APPEND | LOCK_EX);

        // Fallback to error_log if file write fails
        if ($result === false) {
            error_log($entry);
            return false;
        }

        return true;
    }

    /**
     * Clean up old log files
     *
     * @param int $maxDays Maximum number of days to keep logs
     * @return int Number of files deleted
     */
    public static function cleanOldLogs(int $maxDays = 30): int
    {
        if (empty(self::$logPath)) {
            return 0;
        }

        $dir = dirname(self::$logPath);
        $pathInfo = pathinfo(self::$logPath);
        $pattern = $pathInfo['filename'] . '-*.' . $pathInfo['extension'];

        $files = glob($dir . '/' . $pattern);
        $deleted = 0;
        $threshold = time() - ($maxDays * 86400);

        foreach ($files as $file) {
            if (filemtime($file) < $threshold) {
                if (@unlink($file)) {
                    $deleted++;
                }
            }
        }

        return $deleted;
    }

    /**
     * Set log level threshold
     *
     * @param string $level Log level
     * @return void
     */
    public static function setLevel(string $level): void
    {
        if (isset(self::$levels[$level])) {
            self::$threshold = $level;
        }
    }

    /**
     * Get current log level
     *
     * @return string Current log level
     */
    public static function getLevel(): string
    {
        return self::$threshold;
    }
}
