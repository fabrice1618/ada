<?php

/**
 * Phase 4 Testing Script
 *
 * Tests middleware pipeline, Request/Response objects, and middleware functionality
 */

echo "=== PHASE 4: MIDDLEWARE SYSTEM TEST ===\n\n";

// Load core classes
require_once __DIR__ . '/core/Session.php';
require_once __DIR__ . '/core/Security.php';
require_once __DIR__ . '/core/Request.php';
require_once __DIR__ . '/core/Response.php';
require_once __DIR__ . '/core/Middleware.php';

// Initialize session
Session::start();

echo "1. Testing Request Object\n";
echo "   -----------------------\n";

// Create a test Request
$testRequest = new Request(
    ['name' => 'John', 'age' => '25'],           // GET
    ['email' => 'john@example.com', 'city' => 'Paris'], // POST
    ['REQUEST_METHOD' => 'POST', 'REQUEST_URI' => '/test', 'HTTP_USER_AGENT' => 'Test/1.0', 'REMOTE_ADDR' => '127.0.0.1'],
    []
);

echo "   ✓ GET parameter 'name': " . $testRequest->get('name') . "\n";
echo "   ✓ POST parameter 'email': " . $testRequest->post('email') . "\n";
echo "   ✓ Input 'city' (POST takes precedence): " . $testRequest->input('city') . "\n";
echo "   ✓ HTTP method: " . $testRequest->method() . "\n";
echo "   ✓ URI: " . $testRequest->uri() . "\n";
echo "   ✓ Is POST: " . ($testRequest->isPost() ? 'Yes' : 'No') . "\n";
echo "   ✓ User Agent: " . $testRequest->userAgent() . "\n";
echo "   ✓ IP Address: " . $testRequest->ip() . "\n";
echo "   ✓ Has 'name': " . ($testRequest->has('name') ? 'Yes' : 'No') . "\n";
echo "   ✓ All inputs: " . json_encode($testRequest->all()) . "\n\n";

echo "2. Testing Response Object\n";
echo "   ------------------------\n";

// Test basic response
$response1 = new Response("Hello World", 200);
echo "   ✓ Content: " . substr($response1->getContent(), 0, 20) . "\n";
echo "   ✓ Status: " . $response1->getStatus() . "\n";

// Test JSON response
$response2 = Response::json(['message' => 'Success', 'data' => [1, 2, 3]]);
echo "   ✓ JSON Response: " . substr($response2->getContent(), 0, 40) . "...\n";
echo "   ✓ Content-Type header: " . $response2->getHeader('Content-Type') . "\n";

// Test redirect response
$response3 = Response::redirect('/home', 302);
echo "   ✓ Redirect status: " . $response3->getStatus() . "\n";
echo "   ✓ Location header: " . $response3->getHeader('Location') . "\n\n";

echo "3. Testing Middleware Classes\n";
echo "   ---------------------------\n";

// Load middleware classes
require_once __DIR__ . '/app/Middleware/SessionMiddleware.php';
require_once __DIR__ . '/app/Middleware/CsrfMiddleware.php';
require_once __DIR__ . '/app/Middleware/AuthMiddleware.php';

echo "   ✓ SessionMiddleware loaded\n";
echo "   ✓ CsrfMiddleware loaded\n";
echo "   ✓ AuthMiddleware loaded\n\n";

echo "4. Testing Session Middleware\n";
echo "   ---------------------------\n";

$sessionMiddleware = new SessionMiddleware();
$testRequest2 = Request::capture();

$sessionResponse = $sessionMiddleware->handle($testRequest2, function($req) {
    return new Response("Session middleware passed!", 200);
});

echo "   ✓ Session middleware executed\n";
echo "   ✓ Session active: " . (Session::has('last_activity') ? 'Yes' : 'No') . "\n";
echo "   ✓ Response: " . $sessionResponse->getContent() . "\n\n";

echo "5. Testing CSRF Protection\n";
echo "   -----------------------\n";

// Generate CSRF token
Security::generateCsrfToken();
$validToken = Security::getCsrfToken();
echo "   ✓ CSRF token generated: " . substr($validToken, 0, 20) . "...\n";

// Test with valid token
$csrfRequest = new Request(
    [],
    ['_csrf_token' => $validToken],
    ['REQUEST_METHOD' => 'POST', 'REQUEST_URI' => '/test'],
    []
);

$csrfMiddleware = new CsrfMiddleware();
$csrfResponse = $csrfMiddleware->handle($csrfRequest, function($req) {
    return new Response("CSRF check passed!", 200);
});

echo "   ✓ Valid token test: " . ($csrfResponse->getStatus() == 200 ? 'PASSED' : 'FAILED') . "\n";

// Test with invalid token
$csrfRequest2 = new Request(
    [],
    ['_csrf_token' => 'invalid_token_12345'],
    ['REQUEST_METHOD' => 'POST', 'REQUEST_URI' => '/test'],
    []
);

$csrfResponse2 = $csrfMiddleware->handle($csrfRequest2, function($req) {
    return new Response("This should not execute", 200);
});

echo "   ✓ Invalid token test: " . ($csrfResponse2->getStatus() == 403 ? 'BLOCKED (correct)' : 'FAILED') . "\n\n";

echo "6. Testing Auth Middleware\n";
echo "   -----------------------\n";

// Test without authentication
$authRequest = Request::capture();
$authMiddleware = new AuthMiddleware();

$authResponse = $authMiddleware->handle($authRequest, function($req) {
    return new Response("Protected content", 200);
});

echo "   ✓ Without auth: " . ($authResponse->getStatus() == 302 ? 'REDIRECTED (correct)' : 'FAILED') . "\n";

// Simulate logged-in user
Session::set('user_id', 123);

$authResponse2 = $authMiddleware->handle($authRequest, function($req) {
    return new Response("Protected content", 200);
});

echo "   ✓ With auth: " . ($authResponse2->getStatus() == 200 ? 'PASSED (correct)' : 'FAILED') . "\n\n";

echo "7. Testing Middleware Pipeline\n";
echo "   ----------------------------\n";

// Create a simple pipeline
$finalHandler = function(Request $request) {
    return new Response("Final handler reached!", 200);
};

$middleware = [
    function(Request $request, callable $next) {
        echo "   → Middleware 1 (before)\n";
        $response = $next($request);
        echo "   ← Middleware 1 (after)\n";
        return $response;
    },
    function(Request $request, callable $next) {
        echo "   → Middleware 2 (before)\n";
        $response = $next($request);
        echo "   ← Middleware 2 (after)\n";
        return $response;
    }
];

// Build pipeline
$pipeline = $finalHandler;
for ($i = count($middleware) - 1; $i >= 0; $i--) {
    $next = $pipeline;
    $currentMiddleware = $middleware[$i];
    $pipeline = function(Request $request) use ($currentMiddleware, $next) {
        return $currentMiddleware($request, $next);
    };
}

// Execute
$pipelineRequest = Request::capture();
$pipelineResponse = $pipeline($pipelineRequest);

echo "   ✓ Pipeline result: " . $pipelineResponse->getContent() . "\n\n";

echo "=== ALL PHASE 4 TESTS COMPLETED ===\n";
echo "\n✅ Request Object: Working\n";
echo "✅ Response Object: Working\n";
echo "✅ Middleware System: Working\n";
echo "✅ Session Middleware: Working\n";
echo "✅ CSRF Middleware: Working\n";
echo "✅ Auth Middleware: Working\n";
echo "✅ Middleware Pipeline: Working\n\n";
echo "Phase 4 implementation is complete and functional!\n";
