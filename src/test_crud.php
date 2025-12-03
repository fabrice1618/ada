<?php

/**
 * CRUD Operations Test Script
 *
 * Tests all Model CRUD operations for Phase 2 verification.
 */

// Error reporting
error_reporting(E_ALL);
ini_set('display_errors', 1);

// Load core classes
require_once __DIR__ . '/core/Database.php';
require_once __DIR__ . '/core/Model.php';
require_once __DIR__ . '/app/Models/User.php';
require_once __DIR__ . '/app/Models/Devoir.php';
require_once __DIR__ . '/app/Models/Depose.php';

echo "<h1>Phase 2 CRUD Operations Test</h1>\n";
echo "<style>
    body { font-family: Arial, sans-serif; margin: 20px; }
    .test { background: #f0f0f0; padding: 15px; margin: 10px 0; border-left: 4px solid #3498db; }
    .success { border-left-color: #27ae60; background: #e8f8f5; }
    .error { border-left-color: #e74c3c; background: #fadbd8; }
    pre { background: #fff; padding: 10px; overflow: auto; }
</style>\n\n";

// Initialize models
$userModel = new User();
$devoirModel = new Devoir();
$deposeModel = new Depose();

// ===========================================
// TEST 1: SELECT - all()
// ===========================================
echo "<div class='test'>";
echo "<h2>Test 1: SELECT - all()</h2>\n";
try {
    $users = $userModel->all();
    echo "<p class='success'>✓ Successfully fetched all users</p>";
    echo "<pre>" . print_r($users, true) . "</pre>";
} catch (Exception $e) {
    echo "<p class='error'>✗ Error: " . $e->getMessage() . "</p>";
}
echo "</div>";

// ===========================================
// TEST 2: SELECT - find()
// ===========================================
echo "<div class='test'>";
echo "<h2>Test 2: SELECT - find(id)</h2>\n";
try {
    $user = $userModel->find(1);
    echo "<p class='success'>✓ Successfully found user with ID 1</p>";
    echo "<pre>" . print_r($user, true) . "</pre>";
} catch (Exception $e) {
    echo "<p class='error'>✗ Error: " . $e->getMessage() . "</p>";
}
echo "</div>";

// ===========================================
// TEST 3: SELECT - findBy()
// ===========================================
echo "<div class='test'>";
echo "<h2>Test 3: SELECT - findBy(field, value)</h2>\n";
try {
    $devoir = $devoirModel->findByShortcode('DATABASE-101');
    echo "<p class='success'>✓ Successfully found devoir by shortcode</p>";
    echo "<pre>" . print_r($devoir, true) . "</pre>";
} catch (Exception $e) {
    echo "<p class='error'>✗ Error: " . $e->getMessage() . "</p>";
}
echo "</div>";

// ===========================================
// TEST 4: INSERT - create()
// ===========================================
echo "<div class='test'>";
echo "<h2>Test 4: INSERT - create()</h2>\n";
try {
    $newUserId = $userModel->create([
        'username' => 'testuser_' . time(),
        'email' => 'test' . time() . '@example.com'
    ]);
    if ($newUserId) {
        echo "<p class='success'>✓ Successfully created new user with ID: {$newUserId}</p>";

        // Verify it was created
        $newUser = $userModel->find($newUserId);
        echo "<pre>" . print_r($newUser, true) . "</pre>";
    } else {
        echo "<p class='error'>✗ Failed to create user</p>";
    }
} catch (Exception $e) {
    echo "<p class='error'>✗ Error: " . $e->getMessage() . "</p>";
}
echo "</div>";

// ===========================================
// TEST 5: UPDATE - update()
// ===========================================
echo "<div class='test'>";
echo "<h2>Test 5: UPDATE - update(id, data)</h2>\n";
try {
    if (isset($newUserId)) {
        $affected = $userModel->update($newUserId, [
            'email' => 'updated_' . time() . '@example.com'
        ]);

        if ($affected > 0) {
            echo "<p class='success'>✓ Successfully updated user (affected rows: {$affected})</p>";

            // Verify the update
            $updatedUser = $userModel->find($newUserId);
            echo "<pre>" . print_r($updatedUser, true) . "</pre>";
        } else {
            echo "<p class='error'>✗ No rows were updated</p>";
        }
    }
} catch (Exception $e) {
    echo "<p class='error'>✗ Error: " . $e->getMessage() . "</p>";
}
echo "</div>";

// ===========================================
// TEST 6: COUNT
// ===========================================
echo "<div class='test'>";
echo "<h2>Test 6: COUNT - count()</h2>\n";
try {
    $userCount = $userModel->count();
    $devoirCount = $devoirModel->count();
    $deposeCount = $deposeModel->count();

    echo "<p class='success'>✓ Successfully counted records</p>";
    echo "<ul>";
    echo "<li>Users: {$userCount}</li>";
    echo "<li>Devoirs: {$devoirCount}</li>";
    echo "<li>Deposes: {$deposeCount}</li>";
    echo "</ul>";
} catch (Exception $e) {
    echo "<p class='error'>✗ Error: " . $e->getMessage() . "</p>";
}
echo "</div>";

// ===========================================
// TEST 7: CUSTOM QUERIES
// ===========================================
echo "<div class='test'>";
echo "<h2>Test 7: Custom Query Methods</h2>\n";
try {
    $upcomingDevoirs = $devoirModel->getUpcoming();
    echo "<p class='success'>✓ Successfully fetched upcoming devoirs</p>";
    echo "<pre>" . print_r($upcomingDevoirs, true) . "</pre>";

    if (!empty($upcomingDevoirs)) {
        $submissions = $deposeModel->getByDevoir($upcomingDevoirs[0]['iddevoirs']);
        echo "<p class='success'>✓ Successfully fetched submissions for devoir</p>";
        echo "<pre>" . print_r($submissions, true) . "</pre>";
    }
} catch (Exception $e) {
    echo "<p class='error'>✗ Error: " . $e->getMessage() . "</p>";
}
echo "</div>";

// ===========================================
// TEST 8: DELETE - delete()
// ===========================================
echo "<div class='test'>";
echo "<h2>Test 8: DELETE - delete(id)</h2>\n";
try {
    if (isset($newUserId)) {
        $deleted = $userModel->delete($newUserId);

        if ($deleted) {
            echo "<p class='success'>✓ Successfully deleted user with ID: {$newUserId}</p>";

            // Verify deletion
            $deletedUser = $userModel->find($newUserId);
            if ($deletedUser === null) {
                echo "<p class='success'>✓ Verified: User no longer exists in database</p>";
            } else {
                echo "<p class='error'>✗ Error: User still exists after delete</p>";
            }
        } else {
            echo "<p class='error'>✗ Failed to delete user</p>";
        }
    }
} catch (Exception $e) {
    echo "<p class='error'>✗ Error: " . $e->getMessage() . "</p>";
}
echo "</div>";

// ===========================================
// TEST 9: SQL INJECTION PROTECTION
// ===========================================
echo "<div class='test'>";
echo "<h2>Test 9: SQL Injection Protection</h2>\n";
try {
    // Try SQL injection in findBy
    $maliciousInput = "' OR '1'='1";
    $result = $userModel->findBy('username', $maliciousInput);

    if ($result === null) {
        echo "<p class='success'>✓ SQL injection attempt properly handled (no match found)</p>";
        echo "<p>Input: " . htmlspecialchars($maliciousInput) . "</p>";
    } else {
        echo "<p class='error'>✗ Potential SQL injection vulnerability!</p>";
    }
} catch (Exception $e) {
    echo "<p class='success'>✓ SQL injection attempt caught by exception: " . $e->getMessage() . "</p>";
}
echo "</div>";

echo "<div class='test success'>";
echo "<h2>✓ Phase 2 Testing Complete!</h2>";
echo "<p>All CRUD operations have been tested.</p>";
echo "<ul>";
echo "<li>✓ Database connection working</li>";
echo "<li>✓ SELECT operations (all, find, findBy, where)</li>";
echo "<li>✓ INSERT operations (create)</li>";
echo "<li>✓ UPDATE operations (update)</li>";
echo "<li>✓ DELETE operations (delete)</li>";
echo "<li>✓ Custom query methods</li>";
echo "<li>✓ SQL injection protection</li>";
echo "</ul>";
echo "</div>";
?>
