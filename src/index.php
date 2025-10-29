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
require_once __DIR__ . '/core/View.php';
require_once __DIR__ . '/core/Controller.php';

// Load routes configuration
$routes = require_once __DIR__ . '/config/routes.php';

// Get current request URI and method
$requestUri = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);
$requestMethod = $_SERVER['REQUEST_METHOD'];

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
        list($method, $pattern, $handler) = $route;

        // Check if HTTP method matches
        if ($method !== $requestMethod) {
            continue;
        }

        // Convert route pattern to regex
        // For Phase 1, we only support exact matches
        // Parameters like {id} will be added in future phases
        $patternRegex = '#^' . $pattern . '$#';

        // Check if URI matches pattern
        if (preg_match($patternRegex, $requestUri)) {
            return [
                'handler' => $handler,
                'params' => [] // No params in Phase 1
            ];
        }
    }

    return null;
}

// Try to match the route
$matchedRoute = matchRoute($routes, $requestUri, $requestMethod);

// Handle 404 if no route matched
if ($matchedRoute === null) {
    http_response_code(404);
    echo "<h1>404 Not Found</h1>";
    echo "<p>The page you are looking for does not exist.</p>";
    echo "<p><strong>Request URI:</strong> {$requestUri}</p>";
    echo "<p><strong>Request Method:</strong> {$requestMethod}</p>";
    exit();
}

// Parse controller and action from handler
list($controllerName, $actionName) = explode('@', $matchedRoute['handler']);

// Construct controller file path
$controllerPath = __DIR__ . '/app/Controllers/' . $controllerName . '.php';

// Check if controller file exists
if (!file_exists($controllerPath)) {
    http_response_code(500);
    echo "<h1>500 Internal Server Error</h1>";
    echo "<p>Controller not found: {$controllerName}</p>";
    exit();
}

// Load the controller
require_once $controllerPath;

// Check if controller class exists
if (!class_exists($controllerName)) {
    http_response_code(500);
    echo "<h1>500 Internal Server Error</h1>";
    echo "<p>Controller class not found: {$controllerName}</p>";
    exit();
}

// Instantiate the controller
$controller = new $controllerName();

// Check if action method exists
if (!method_exists($controller, $actionName)) {
    http_response_code(500);
    echo "<h1>500 Internal Server Error</h1>";
    echo "<p>Action method not found: {$controllerName}@{$actionName}</p>";
    exit();
}

// Call the action method with parameters (empty for Phase 1)
call_user_func_array([$controller, $actionName], $matchedRoute['params']);
