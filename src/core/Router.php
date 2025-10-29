<?php

/**
 * Router Class
 *
 * Handles route registration, matching, and dispatching with support for
 * named routes, route groups, middleware, and dynamic parameters.
 */
class Router
{
    /**
     * Registered routes
     *
     * @var array
     */
    protected array $routes = [];

    /**
     * Named routes for URL generation
     *
     * @var array
     */
    protected array $namedRoutes = [];

    /**
     * Current route group configuration
     *
     * @var array
     */
    protected array $groupStack = [];

    /**
     * Global middleware applied to all routes
     *
     * @var array
     */
    protected array $globalMiddleware = [];

    /**
     * Add a GET route
     *
     * @param string $uri Route URI
     * @param string|callable $action Controller@method or callable
     * @param array $options Additional options (name, middleware)
     * @return self
     */
    public function get(string $uri, $action, array $options = []): self
    {
        return $this->addRoute('GET', $uri, $action, $options);
    }

    /**
     * Add a POST route
     *
     * @param string $uri Route URI
     * @param string|callable $action Controller@method or callable
     * @param array $options Additional options
     * @return self
     */
    public function post(string $uri, $action, array $options = []): self
    {
        return $this->addRoute('POST', $uri, $action, $options);
    }

    /**
     * Add a PUT route
     *
     * @param string $uri Route URI
     * @param string|callable $action Controller@method or callable
     * @param array $options Additional options
     * @return self
     */
    public function put(string $uri, $action, array $options = []): self
    {
        return $this->addRoute('PUT', $uri, $action, $options);
    }

    /**
     * Add a DELETE route
     *
     * @param string $uri Route URI
     * @param string|callable $action Controller@method or callable
     * @param array $options Additional options
     * @return self
     */
    public function delete(string $uri, $action, array $options = []): self
    {
        return $this->addRoute('DELETE', $uri, $action, $options);
    }

    /**
     * Add a PATCH route
     *
     * @param string $uri Route URI
     * @param string|callable $action Controller@method or callable
     * @param array $options Additional options
     * @return self
     */
    public function patch(string $uri, $action, array $options = []): self
    {
        return $this->addRoute('PATCH', $uri, $action, $options);
    }

    /**
     * Add a route for any HTTP method
     *
     * @param string $uri Route URI
     * @param string|callable $action Controller@method or callable
     * @param array $options Additional options
     * @return self
     */
    public function any(string $uri, $action, array $options = []): self
    {
        $methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH'];
        foreach ($methods as $method) {
            $this->addRoute($method, $uri, $action, $options);
        }
        return $this;
    }

    /**
     * Create a route group
     *
     * @param array $attributes Group attributes (prefix, middleware)
     * @param callable $callback Callback to define routes
     * @return void
     */
    public function group(array $attributes, callable $callback): void
    {
        // Add current group to stack
        $this->groupStack[] = $attributes;

        // Execute callback to register routes
        $callback($this);

        // Remove group from stack
        array_pop($this->groupStack);
    }

    /**
     * Add a route to the routing table
     *
     * @param string $method HTTP method
     * @param string $uri Route URI
     * @param string|callable $action Controller@method or callable
     * @param array $options Additional options
     * @return self
     */
    protected function addRoute(string $method, string $uri, $action, array $options = []): self
    {
        // Apply group attributes
        $uri = $this->applyGroupPrefix($uri);
        $middleware = $this->mergeGroupMiddleware($options['middleware'] ?? []);

        // Store route
        $this->routes[] = [
            'method' => strtoupper($method),
            'uri' => $uri,
            'action' => $action,
            'middleware' => $middleware,
            'name' => $options['name'] ?? null,
        ];

        // Store named route
        if (isset($options['name'])) {
            $this->namedRoutes[$options['name']] = $uri;
        }

        return $this;
    }

    /**
     * Apply group prefix to URI
     *
     * @param string $uri Route URI
     * @return string Prefixed URI
     */
    protected function applyGroupPrefix(string $uri): string
    {
        foreach ($this->groupStack as $group) {
            if (isset($group['prefix'])) {
                $prefix = trim($group['prefix'], '/');
                $uri = '/' . trim($prefix . '/' . trim($uri, '/'), '/');
            }
        }

        return $uri ?: '/';
    }

    /**
     * Merge group middleware with route middleware
     *
     * @param array $routeMiddleware Route-specific middleware
     * @return array Combined middleware
     */
    protected function mergeGroupMiddleware(array $routeMiddleware): array
    {
        $middleware = [];

        foreach ($this->groupStack as $group) {
            if (isset($group['middleware'])) {
                $middleware = array_merge($middleware, (array)$group['middleware']);
            }
        }

        return array_merge($middleware, $routeMiddleware);
    }

    /**
     * Set global middleware
     *
     * @param array $middleware Middleware classes
     * @return void
     */
    public function setGlobalMiddleware(array $middleware): void
    {
        $this->globalMiddleware = $middleware;
    }

    /**
     * Match and dispatch a request
     *
     * @param Request $request Request object
     * @return Response Response object
     * @throws Exception
     */
    public function dispatch(Request $request): Response
    {
        $method = $request->method();
        $uri = $this->normalizeUri($request->uri());

        // Find matching route
        $match = $this->match($method, $uri);

        if ($match === null) {
            // 404 Not Found
            if (class_exists('Logger')) {
                Logger::warning("Route not found: {$method} {$uri}");
            }
            return $this->handleNotFound($request);
        }

        // Extract route and parameters
        ['route' => $route, 'params' => $params] = $match;

        // Set route parameters in request
        foreach ($params as $key => $value) {
            $request->setRouteParam($key, $value);
        }

        // Combine global and route middleware
        $middleware = array_merge($this->globalMiddleware, $route['middleware']);

        // Execute middleware pipeline
        return $this->runMiddleware($middleware, $request, function($request) use ($route, $params) {
            return $this->callAction($route['action'], $request, $params);
        });
    }

    /**
     * Normalize URI for matching
     *
     * @param string $uri Request URI
     * @return string Normalized URI
     */
    protected function normalizeUri(string $uri): string
    {
        // Remove query string
        $uri = parse_url($uri, PHP_URL_PATH);

        // Trim slashes
        $uri = '/' . trim($uri, '/');

        // Convert empty to root
        return $uri === '/' ? '/' : rtrim($uri, '/');
    }

    /**
     * Match a request to a route
     *
     * @param string $method HTTP method
     * @param string $uri Request URI
     * @return array|null Match result or null
     */
    protected function match(string $method, string $uri): ?array
    {
        foreach ($this->routes as $route) {
            if ($route['method'] !== $method) {
                continue;
            }

            $pattern = $this->compilePattern($route['uri']);

            if (preg_match($pattern, $uri, $matches)) {
                // Extract named parameters
                $params = array_filter($matches, 'is_string', ARRAY_FILTER_USE_KEY);

                return [
                    'route' => $route,
                    'params' => $params,
                ];
            }
        }

        return null;
    }

    /**
     * Compile route URI to regex pattern
     *
     * @param string $uri Route URI
     * @return string Regex pattern
     */
    protected function compilePattern(string $uri): string
    {
        // Escape forward slashes
        $pattern = str_replace('/', '\/', $uri);

        // Replace {param} with named capture groups
        $pattern = preg_replace('/\{([a-zA-Z_][a-zA-Z0-9_]*)\}/', '(?P<$1>[^/]+)', $pattern);

        return '/^' . $pattern . '$/';
    }

    /**
     * Execute middleware pipeline
     *
     * @param array $middleware Middleware stack
     * @param Request $request Request object
     * @param callable $target Final target (controller action)
     * @return Response Response object
     */
    protected function runMiddleware(array $middleware, Request $request, callable $target): Response
    {
        // Create the middleware pipeline
        $pipeline = array_reduce(
            array_reverse($middleware),
            function($next, $middleware) {
                return function($request) use ($middleware, $next) {
                    $instance = new $middleware();
                    return $instance->handle($request, $next);
                };
            },
            $target
        );

        return $pipeline($request);
    }

    /**
     * Call the controller action
     *
     * @param string|callable $action Controller@method or callable
     * @param Request $request Request object
     * @param array $params Route parameters
     * @return Response Response object
     * @throws Exception
     */
    protected function callAction($action, Request $request, array $params): Response
    {
        // Handle callable
        if (is_callable($action)) {
            $result = $action($request, ...$params);
            return $this->prepareResponse($result);
        }

        // Handle Controller@method
        if (is_string($action) && strpos($action, '@') !== false) {
            list($controller, $method) = explode('@', $action);

            $controllerFile = __DIR__ . '/../app/Controllers/' . $controller . '.php';

            if (!file_exists($controllerFile)) {
                throw new Exception("Controller not found: {$controller}");
            }

            require_once $controllerFile;

            if (!class_exists($controller)) {
                throw new Exception("Controller class not found: {$controller}");
            }

            $instance = new $controller();

            if (!method_exists($instance, $method)) {
                throw new Exception("Method not found: {$controller}@{$method}");
            }

            $result = $instance->$method($request, ...$params);
            return $this->prepareResponse($result);
        }

        throw new Exception("Invalid action: " . print_r($action, true));
    }

    /**
     * Prepare response from controller return value
     *
     * @param mixed $result Controller return value
     * @return Response Response object
     */
    protected function prepareResponse($result): Response
    {
        if ($result instanceof Response) {
            return $result;
        }

        if (is_string($result)) {
            $response = new Response();
            $response->setContent($result);
            return $response;
        }

        if (is_array($result)) {
            return Response::json($result);
        }

        throw new Exception("Invalid response type");
    }

    /**
     * Handle 404 Not Found
     *
     * @param Request $request Request object
     * @return Response Response object
     */
    protected function handleNotFound(Request $request): Response
    {
        // Try to use ErrorController if available
        $errorController = __DIR__ . '/../app/Controllers/ErrorController.php';

        if (file_exists($errorController)) {
            require_once $errorController;
            $controller = new ErrorController();
            return $controller->error404($request);
        }

        // Fallback
        $response = new Response();
        $response->setStatus(404);
        $response->setContent('<h1>404 Not Found</h1><p>The requested page could not be found.</p>');
        return $response;
    }

    /**
     * Generate URL for a named route
     *
     * @param string $name Route name
     * @param array $params Route parameters
     * @return string Generated URL
     * @throws Exception
     */
    public function route(string $name, array $params = []): string
    {
        if (!isset($this->namedRoutes[$name])) {
            throw new Exception("Route not found: {$name}");
        }

        $uri = $this->namedRoutes[$name];

        // Replace parameters
        foreach ($params as $key => $value) {
            $uri = str_replace('{' . $key . '}', $value, $uri);
        }

        // Check for missing parameters
        if (preg_match('/\{[a-zA-Z_][a-zA-Z0-9_]*\}/', $uri)) {
            throw new Exception("Missing parameters for route: {$name}");
        }

        return $uri;
    }

    /**
     * Get all registered routes
     *
     * @return array All routes
     */
    public function getRoutes(): array
    {
        return $this->routes;
    }
}
