<?php

/**
 * Request Class
 *
 * Handles HTTP request data including GET, POST, SERVER, and FILES
 */
class Request
{
    /**
     * @var array GET parameters
     */
    protected array $get;

    /**
     * @var array POST parameters
     */
    protected array $post;

    /**
     * @var array SERVER parameters
     */
    protected array $server;

    /**
     * @var array FILES parameters
     */
    protected array $files;

    /**
     * @var array Route parameters
     */
    protected array $routeParams = [];

    /**
     * Constructor
     *
     * @param array $get GET parameters
     * @param array $post POST parameters
     * @param array $server SERVER parameters
     * @param array $files FILES parameters
     */
    public function __construct(array $get = [], array $post = [], array $server = [], array $files = [])
    {
        $this->get = $get;
        $this->post = $post;
        $this->server = $server;
        $this->files = $files;
    }

    /**
     * Create a Request instance from global variables
     *
     * @return Request
     */
    public static function capture(): Request
    {
        return new static($_GET, $_POST, $_SERVER, $_FILES);
    }

    /**
     * Get the HTTP method
     *
     * @return string
     */
    public function method(): string
    {
        return strtoupper($this->server['REQUEST_METHOD'] ?? 'GET');
    }

    /**
     * Get the request URI
     *
     * @return string
     */
    public function uri(): string
    {
        $uri = $this->server['REQUEST_URI'] ?? '/';

        // Remove query string
        if (($pos = strpos($uri, '?')) !== false) {
            $uri = substr($uri, 0, $pos);
        }

        return $uri;
    }

    /**
     * Get the full URL
     *
     * @return string
     */
    public function url(): string
    {
        $protocol = (!empty($this->server['HTTPS']) && $this->server['HTTPS'] !== 'off') ? 'https' : 'http';
        $host = $this->server['HTTP_HOST'] ?? 'localhost';
        return $protocol . '://' . $host . $this->uri();
    }

    /**
     * Get a value from GET parameters
     *
     * @param string $key The parameter key
     * @param mixed $default Default value if key doesn't exist
     * @return mixed
     */
    public function get(string $key, $default = null)
    {
        return $this->get[$key] ?? $default;
    }

    /**
     * Get a value from POST parameters
     *
     * @param string $key The parameter key
     * @param mixed $default Default value if key doesn't exist
     * @return mixed
     */
    public function post(string $key, $default = null)
    {
        return $this->post[$key] ?? $default;
    }

    /**
     * Get a value from GET or POST (POST takes precedence)
     *
     * @param string $key The parameter key
     * @param mixed $default Default value if key doesn't exist
     * @return mixed
     */
    public function input(string $key, $default = null)
    {
        return $this->post[$key] ?? $this->get[$key] ?? $default;
    }

    /**
     * Get all input data (GET and POST merged, POST takes precedence)
     *
     * @return array
     */
    public function all(): array
    {
        return array_merge($this->get, $this->post);
    }

    /**
     * Get only specified keys from input
     *
     * @param array $keys Array of keys to retrieve
     * @return array
     */
    public function only(array $keys): array
    {
        $all = $this->all();
        $result = [];
        foreach ($keys as $key) {
            if (isset($all[$key])) {
                $result[$key] = $all[$key];
            }
        }
        return $result;
    }

    /**
     * Get all input except specified keys
     *
     * @param array $keys Array of keys to exclude
     * @return array
     */
    public function except(array $keys): array
    {
        $all = $this->all();
        foreach ($keys as $key) {
            unset($all[$key]);
        }
        return $all;
    }

    /**
     * Check if input has a specific key
     *
     * @param string $key The key to check
     * @return bool
     */
    public function has(string $key): bool
    {
        $all = $this->all();
        return isset($all[$key]);
    }

    /**
     * Check if request is POST
     *
     * @return bool
     */
    public function isPost(): bool
    {
        return $this->method() === 'POST';
    }

    /**
     * Check if request is GET
     *
     * @return bool
     */
    public function isGet(): bool
    {
        return $this->method() === 'GET';
    }

    /**
     * Check if request is PUT
     *
     * @return bool
     */
    public function isPut(): bool
    {
        return $this->method() === 'PUT';
    }

    /**
     * Check if request is DELETE
     *
     * @return bool
     */
    public function isDelete(): bool
    {
        return $this->method() === 'DELETE';
    }

    /**
     * Check if request is AJAX
     *
     * @return bool
     */
    public function isAjax(): bool
    {
        return !empty($this->server['HTTP_X_REQUESTED_WITH']) &&
               strtolower($this->server['HTTP_X_REQUESTED_WITH']) === 'xmlhttprequest';
    }

    /**
     * Get client IP address
     *
     * @return string
     */
    public function ip(): string
    {
        // Check various headers for proxy/load balancer scenarios
        if (!empty($this->server['HTTP_CLIENT_IP'])) {
            return $this->server['HTTP_CLIENT_IP'];
        } elseif (!empty($this->server['HTTP_X_FORWARDED_FOR'])) {
            // X-Forwarded-For may contain multiple IPs, get the first one
            $ips = explode(',', $this->server['HTTP_X_FORWARDED_FOR']);
            return trim($ips[0]);
        } elseif (!empty($this->server['REMOTE_ADDR'])) {
            return $this->server['REMOTE_ADDR'];
        }
        return '0.0.0.0';
    }

    /**
     * Get user agent string
     *
     * @return string
     */
    public function userAgent(): string
    {
        return $this->server['HTTP_USER_AGENT'] ?? '';
    }

    /**
     * Get a specific header value
     *
     * @param string $name Header name
     * @param mixed $default Default value
     * @return mixed
     */
    public function header(string $name, $default = null)
    {
        // Convert header name to SERVER key format
        $key = 'HTTP_' . strtoupper(str_replace('-', '_', $name));
        return $this->server[$key] ?? $default;
    }

    /**
     * Get file from FILES array
     *
     * @param string $key File input name
     * @return array|null
     */
    public function file(string $key): ?array
    {
        return $this->files[$key] ?? null;
    }

    /**
     * Check if a file was uploaded
     *
     * @param string $key File input name
     * @return bool
     */
    public function hasFile(string $key): bool
    {
        return isset($this->files[$key]) && $this->files[$key]['error'] === UPLOAD_ERR_OK;
    }

    /**
     * Validate uploaded file
     *
     * @param string $key File input name
     * @param int $maxSize Maximum file size in bytes (default 10MB)
     * @param array $allowedTypes Allowed MIME types
     * @param array $allowedExtensions Allowed file extensions
     * @return array ['valid' => bool, 'error' => string|null]
     */
    public function validateFile(string $key, int $maxSize = 10485760, array $allowedTypes = [], array $allowedExtensions = []): array
    {
        if (!$this->hasFile($key)) {
            return ['valid' => false, 'error' => 'No file uploaded'];
        }

        $file = $this->files[$key];

        // Check file size
        if ($file['size'] > $maxSize) {
            return ['valid' => false, 'error' => 'File too large'];
        }

        // Check MIME type if specified
        if (!empty($allowedTypes)) {
            $finfo = finfo_open(FILEINFO_MIME_TYPE);
            $mimeType = finfo_file($finfo, $file['tmp_name']);
            finfo_close($finfo);

            if (!in_array($mimeType, $allowedTypes)) {
                return ['valid' => false, 'error' => 'Invalid file type'];
            }
        }

        // Check file extension if specified
        if (!empty($allowedExtensions)) {
            $extension = strtolower(pathinfo($file['name'], PATHINFO_EXTENSION));
            if (!in_array($extension, $allowedExtensions)) {
                return ['valid' => false, 'error' => 'Invalid file extension'];
            }
        }

        return ['valid' => true, 'error' => null];
    }

    /**
     * Move uploaded file to destination
     *
     * @param string $key File input name
     * @param string $destination Destination path
     * @param string|null $newName Optional new filename
     * @return array ['success' => bool, 'path' => string|null, 'error' => string|null]
     */
    public function moveFile(string $key, string $destination, ?string $newName = null): array
    {
        if (!$this->hasFile($key)) {
            return ['success' => false, 'path' => null, 'error' => 'No file uploaded'];
        }

        $file = $this->files[$key];

        // Ensure destination directory exists
        if (!is_dir($destination)) {
            if (!mkdir($destination, 0755, true)) {
                return ['success' => false, 'path' => null, 'error' => 'Failed to create destination directory'];
            }
        }

        // Generate filename
        if ($newName === null) {
            // Generate unique name with original extension
            $extension = pathinfo($file['name'], PATHINFO_EXTENSION);
            $newName = uniqid() . '_' . time() . '.' . $extension;
        }

        $targetPath = rtrim($destination, '/') . '/' . $newName;

        // Move file
        if (move_uploaded_file($file['tmp_name'], $targetPath)) {
            return ['success' => true, 'path' => $targetPath, 'error' => null];
        }

        return ['success' => false, 'path' => null, 'error' => 'Failed to move uploaded file'];
    }

    /**
     * Set a route parameter
     *
     * @param string $key Parameter name
     * @param mixed $value Parameter value
     * @return void
     */
    public function setRouteParam(string $key, $value): void
    {
        $this->routeParams[$key] = $value;
    }

    /**
     * Get a route parameter
     *
     * @param string $key Parameter name
     * @param mixed $default Default value
     * @return mixed
     */
    public function routeParam(string $key, $default = null)
    {
        return $this->routeParams[$key] ?? $default;
    }

    /**
     * Get all route parameters
     *
     * @return array
     */
    public function routeParams(): array
    {
        return $this->routeParams;
    }
}
