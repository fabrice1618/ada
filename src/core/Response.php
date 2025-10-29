<?php

/**
 * Response Class
 *
 * Handles HTTP responses including status codes, headers, and content
 */
class Response
{
    /**
     * @var int HTTP status code
     */
    protected int $statusCode = 200;

    /**
     * @var array Response headers
     */
    protected array $headers = [];

    /**
     * @var string Response content
     */
    protected string $content = '';

    /**
     * Constructor
     *
     * @param string $content Response content
     * @param int $statusCode HTTP status code
     * @param array $headers Response headers
     */
    public function __construct(string $content = '', int $statusCode = 200, array $headers = [])
    {
        $this->content = $content;
        $this->statusCode = $statusCode;
        $this->headers = $headers;
    }

    /**
     * Set HTTP status code
     *
     * @param int $code HTTP status code
     * @return $this
     */
    public function setStatus(int $code): self
    {
        $this->statusCode = $code;
        return $this;
    }

    /**
     * Get HTTP status code
     *
     * @return int
     */
    public function getStatus(): int
    {
        return $this->statusCode;
    }

    /**
     * Set a response header
     *
     * @param string $name Header name
     * @param string $value Header value
     * @return $this
     */
    public function setHeader(string $name, string $value): self
    {
        $this->headers[$name] = $value;
        return $this;
    }

    /**
     * Get a response header
     *
     * @param string $name Header name
     * @return string|null
     */
    public function getHeader(string $name): ?string
    {
        return $this->headers[$name] ?? null;
    }

    /**
     * Get all headers
     *
     * @return array
     */
    public function getHeaders(): array
    {
        return $this->headers;
    }

    /**
     * Set response content
     *
     * @param string $content Response content
     * @return $this
     */
    public function setContent(string $content): self
    {
        $this->content = $content;
        return $this;
    }

    /**
     * Get response content
     *
     * @return string
     */
    public function getContent(): string
    {
        return $this->content;
    }

    /**
     * Send the response to the client
     *
     * @return void
     */
    public function send(): void
    {
        // Set HTTP status code
        http_response_code($this->statusCode);

        // Send headers
        foreach ($this->headers as $name => $value) {
            header("$name: $value");
        }

        // Output content
        echo $this->content;
    }

    /**
     * Create a redirect response
     *
     * @param string $url URL to redirect to
     * @param int $statusCode HTTP status code (default 302)
     * @return Response
     */
    public static function redirect(string $url, int $statusCode = 302): Response
    {
        $response = new self('', $statusCode);
        $response->setHeader('Location', $url);
        return $response;
    }

    /**
     * Create a JSON response
     *
     * @param mixed $data Data to encode as JSON
     * @param int $statusCode HTTP status code
     * @return Response
     */
    public static function json($data, int $statusCode = 200): Response
    {
        $content = json_encode($data);
        $response = new self($content, $statusCode);
        $response->setHeader('Content-Type', 'application/json');
        return $response;
    }

    /**
     * Create a view response
     *
     * @param string $template Template name
     * @param array $data Data to pass to the view
     * @param int $statusCode HTTP status code
     * @return Response
     */
    public static function view(string $template, array $data = [], int $statusCode = 200): Response
    {
        $view = new View();
        $content = $view->render($template, $data);
        $response = new self($content, $statusCode);
        $response->setHeader('Content-Type', 'text/html; charset=UTF-8');
        return $response;
    }

    /**
     * Flash data to session and redirect
     *
     * @param string $key Flash data key
     * @param mixed $value Flash data value
     * @return $this
     */
    public function with(string $key, $value): self
    {
        if (class_exists('Session')) {
            Session::flash($key, $value);
        }
        return $this;
    }

    /**
     * Flash errors to session and redirect
     *
     * @param array $errors Array of errors
     * @return $this
     */
    public function withErrors(array $errors): self
    {
        return $this->with('errors', $errors);
    }

    /**
     * Flash input data to session and redirect
     *
     * @param array $input Input data to flash
     * @return $this
     */
    public function withInput(array $input = []): self
    {
        if (empty($input) && isset($_POST)) {
            $input = $_POST;
        }
        return $this->with('old', $input);
    }

    /**
     * Create a redirect back response
     *
     * @return Response
     */
    public static function back(): Response
    {
        $referer = $_SERVER['HTTP_REFERER'] ?? '/';
        return self::redirect($referer);
    }

    /**
     * Create a download response
     *
     * @param string $filePath Path to file to download
     * @param string|null $name Optional filename for download
     * @return Response
     */
    public static function download(string $filePath, ?string $name = null): Response
    {
        if (!file_exists($filePath)) {
            throw new Exception("File not found: {$filePath}");
        }

        $content = file_get_contents($filePath);
        $fileName = $name ?? basename($filePath);

        $response = new self($content, 200);
        $response->setHeader('Content-Type', 'application/octet-stream');
        $response->setHeader('Content-Disposition', 'attachment; filename="' . $fileName . '"');
        $response->setHeader('Content-Length', (string) filesize($filePath));

        return $response;
    }

    /**
     * Create a file response (inline display)
     *
     * @param string $filePath Path to file
     * @param string|null $mimeType Optional MIME type
     * @return Response
     */
    public static function file(string $filePath, ?string $mimeType = null): Response
    {
        if (!file_exists($filePath)) {
            throw new Exception("File not found: {$filePath}");
        }

        $content = file_get_contents($filePath);

        if ($mimeType === null) {
            $finfo = finfo_open(FILEINFO_MIME_TYPE);
            $mimeType = finfo_file($finfo, $filePath);
            finfo_close($finfo);
        }

        $response = new self($content, 200);
        $response->setHeader('Content-Type', $mimeType);
        $response->setHeader('Content-Length', (string) filesize($filePath));

        return $response;
    }

    /**
     * Set multiple headers at once
     *
     * @param array $headers Associative array of headers
     * @return $this
     */
    public function withHeaders(array $headers): self
    {
        foreach ($headers as $name => $value) {
            $this->setHeader($name, $value);
        }
        return $this;
    }

    /**
     * Set cookie
     *
     * @param string $name Cookie name
     * @param string $value Cookie value
     * @param int $expire Expiration time
     * @param string $path Cookie path
     * @param string $domain Cookie domain
     * @param bool $secure Secure flag
     * @param bool $httponly HttpOnly flag
     * @return $this
     */
    public function withCookie(string $name, string $value, int $expire = 0, string $path = '/', string $domain = '', bool $secure = false, bool $httponly = true): self
    {
        setcookie($name, $value, $expire, $path, $domain, $secure, $httponly);
        return $this;
    }

    /**
     * Create a no content response (204)
     *
     * @return Response
     */
    public static function noContent(): Response
    {
        return new self('', 204);
    }

    /**
     * Create a created response (201)
     *
     * @param mixed $data Optional data
     * @param string|null $location Optional Location header
     * @return Response
     */
    public static function created($data = null, ?string $location = null): Response
    {
        $response = $data !== null
            ? self::json($data, 201)
            : new self('', 201);

        if ($location !== null) {
            $response->setHeader('Location', $location);
        }

        return $response;
    }
}
