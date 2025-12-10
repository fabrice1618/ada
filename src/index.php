<?php

/**
 * Front Controller / Router
 *
 * Single entry point for all HTTP requests.
 * Routes requests to appropriate controllers and actions.
 *
 * @package ADA Framework
 * @version 1.0 (Phase 1)
 */

// Error reporting (development mode)
error_reporting(E_ALL);
ini_set('display_errors', 1);

// Load core classes
require_once __DIR__ . '/core/Session.php';
require_once __DIR__ . '/core/Security.php';
require_once __DIR__ . '/core/helpers.php';
require_once __DIR__ . '/core/Database.php';
require_once __DIR__ . '/core/Model.php';
require_once __DIR__ . '/core/View.php';
require_once __DIR__ . '/core/Controller.php';
require_once __DIR__ . '/core/Request.php';
require_once __DIR__ . '/core/Response.php';
require_once __DIR__ . '/core/Middleware.php';
require_once __DIR__ . '/core/Validator.php';
require_once __DIR__ . '/core/ValidationException.php';
require_once __DIR__ . '/core/ErrorHandler.php';

// Register error handler
ErrorHandler::register(
    ini_get('display_errors'),
    __DIR__ . '/logs/error.log'
);

// Load routes configuration
$routesConfig = require_once __DIR__ . '/config/routes.php';

// Capture the current request
$request = Request::capture();

// Get current request URI and method
$requestUri = $request->uri();
$requestMethod = $request->method();

// Remove trailing slash (except for root)
if ($requestUri !== '/' && substr($requestUri, -1) === '/') {
    $requestUri = rtrim($requestUri, '/');
}

/**
 * Match route against defined routes
 *
 * @param array $routes Array of route definitions
 * @param string $requestUri Current request URI
 * @param string $requestMethod Current request method
 * @return array|null Matched route or null
 */
function matchRoute($routes, $requestUri, $requestMethod)
{
    foreach ($routes as $route) {
        // Handle both old format and new format with middleware
        if (count($route) >= 3) {
            list($method, $pattern, $handler) = $route;
            $routeMiddleware = $route[3]['middleware'] ?? [];
        } else {
            continue;
        }

        // Check if HTTP method matches
        if ($method !== $requestMethod) {
            continue;
        }

        // Convert route pattern to regex
        // Support for parameters like {id}, {shortcode}, etc.
        $params = [];
        $paramNames = [];
        
        // Extract parameter names from pattern
        if (preg_match_all('/{([a-zA-Z_][a-zA-Z0-9_]*)}/', $pattern, $matches)) {
            $paramNames = $matches[1];
            // Replace {param} with regex capture group
            $patternRegex = preg_replace('/{[a-zA-Z_][a-zA-Z0-9_]*}/', '([^/]+)', $pattern);
            $patternRegex = '#^' . $patternRegex . '$#';
        } else {
            // No parameters, exact match
            $patternRegex = '#^' . $pattern . '$#';
        }

        // Check if URI matches pattern
        if (preg_match($patternRegex, $requestUri, $matches)) {
            // Extract parameter values
            array_shift($matches); // Remove full match
            foreach ($paramNames as $index => $name) {
                $params[$name] = $matches[$index] ?? null;
            }
            
            return [
                'handler' => $handler,
                'params' => $params,
                'middleware' => $routeMiddleware
            ];
        }
    }

    return null;
}

// Get routes and global middleware from config
$routes = $routesConfig['routes'] ?? $routesConfig;
$globalMiddleware = $routesConfig['middleware'] ?? [];

// Try to match the route
$matchedRoute = matchRoute($routes, $requestUri, $requestMethod);

// Handle 404 if no route matched
if ($matchedRoute === null) {
    require_once __DIR__ . '/app/Controllers/ErrorController.php';
    $errorController = new ErrorController();
    $response = $errorController->error404($request, $requestUri);
    $response->send();
    exit();
}

/**
 * Run middleware pipeline
 *
 * @param Request $request Current request
 * @param array $middleware Array of middleware class names
 * @param array $matchedRoute Route information
 * @return Response
 */
function runMiddleware(Request $request, array $middleware, array $matchedRoute): Response
{
    // Create the final handler (controller action)
    $finalHandler = function (Request $request) use ($matchedRoute) {
        list($controllerName, $actionName) = explode('@', $matchedRoute['handler']);

        // Construct controller file path
        $controllerPath = __DIR__ . '/app/Controllers/' . $controllerName . '.php';

        // Check if controller file exists
        if (!file_exists($controllerPath)) {
            return new Response("<h1>500 Internal Server Error</h1><p>Controller not found: {$controllerName}</p>", 500);
        }

        // Load the controller
        require_once $controllerPath;

        // Check if controller class exists
        if (!class_exists($controllerName)) {
            return new Response("<h1>500 Internal Server Error</h1><p>Controller class not found: {$controllerName}</p>", 500);
        }

        // Instantiate the controller
        $controller = new $controllerName();

        // Check if action method exists
        if (!method_exists($controller, $actionName)) {
            return new Response("<h1>500 Internal Server Error</h1><p>Action method not found: {$controllerName}@{$actionName}</p>", 500);
        }

        // Call the action method with request and parameters
        $result = call_user_func_array([$controller, $actionName], array_merge([$request], $matchedRoute['params']));

        // If controller returns a Response, use it; otherwise create one
        if ($result instanceof Response) {
            return $result;
        }

        // If result is null, assume output was already sent (legacy behavior)
        return new Response('', 200);
    };

    // Build middleware pipeline (reverse order)
    $pipeline = $finalHandler;

    for ($i = count($middleware) - 1; $i >= 0; $i--) {
        $middlewareClass = $middleware[$i];
        $next = $pipeline;

        $pipeline = function (Request $request) use ($middlewareClass, $next) {
            // Load middleware file if it exists
            $middlewarePath = __DIR__ . '/app/Middleware/' . $middlewareClass . '.php';
            if (file_exists($middlewarePath)) {
                require_once $middlewarePath;
            }

            if (!class_exists($middlewareClass)) {
                throw new Exception("Middleware class not found: {$middlewareClass}");
            }

            $middlewareInstance = new $middlewareClass();
            return $middlewareInstance->handle($request, $next);
        };
    }

    // Execute the pipeline
    return $pipeline($request);
}

// Get middleware for this route (global + route-specific)
$routeMiddleware = $matchedRoute['middleware'] ?? [];
$middleware = array_merge($globalMiddleware, $routeMiddleware);

// Run the middleware pipeline
try {
    $response = runMiddleware($request, $middleware, $matchedRoute);
    $response->send();
} catch (Exception $e) {
    http_response_code(500);
    echo "<h1>500 Internal Server Error</h1>";
    echo "<p>Error: " . htmlspecialchars($e->getMessage()) . "</p>";
    if (ini_get('display_errors')) {
        echo "<pre>" . htmlspecialchars($e->getTraceAsString()) . "</pre>";
    }
}
