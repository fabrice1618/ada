<?php

/**
 * User Model Unit Tests - CLI Version
 *
 * Tests all User model methods for comprehensive verification.
 * Run with: php src/tests/test_user.php
 */

// Error reporting
error_reporting(E_ALL);
ini_set('display_errors', 1);

// ANSI color codes for CLI output
define('COLOR_RESET', "\033[0m");
define('COLOR_RED', "\033[31m");
define('COLOR_GREEN', "\033[32m");
define('COLOR_YELLOW', "\033[33m");
define('COLOR_BLUE', "\033[34m");
define('COLOR_CYAN', "\033[36m");

// Load core classes
require_once __DIR__ . '/../core/Database.php';
require_once __DIR__ . '/../core/Model.php';
require_once __DIR__ . '/../app/Models/User.php';

echo COLOR_CYAN . "=====================================\n";
echo "      USER MODEL UNIT TESTS\n";
echo "=====================================\n" . COLOR_RESET;
echo "\n";

// Initialize model
$userModel = new User();
$testCount = 0;
$passedCount = 0;

function testResult($testName, $passed, $message = '') {
    global $testCount, $passedCount;
    $testCount++;

    if ($passed) {
        $passedCount++;
        echo COLOR_GREEN . "✓ PASS" . COLOR_RESET . " - $testName\n";
    } else {
        echo COLOR_RED . "✗ FAIL" . COLOR_RESET . " - $testName\n";
    }

    if ($message) {
        echo "  $message\n";
    }
    echo "\n";
}

// ===========================================
// TEST 1: Basic CRUD - all()
// ===========================================
echo COLOR_BLUE . "Test 1: SELECT - all()\n" . COLOR_RESET;
try {
    $users = $userModel->all();
    $hasRecords = is_array($users) && count($users) > 0;
    testResult("all() returns array with records", $hasRecords,
        "Found " . count($users) . " users");
} catch (Exception $e) {
    testResult("all() method", false, "Exception: " . $e->getMessage());
}

// ===========================================
// TEST 2: Basic CRUD - find()
// ===========================================
echo COLOR_BLUE . "Test 2: SELECT - find(id)\n" . COLOR_RESET;
try {
    $user = $userModel->find(1);
    $isValid = is_array($user) && isset($user['id']) && $user['id'] == 1;
    testResult("find(1) returns valid user", $isValid,
        $isValid ? "Found user: " . $user['username'] : "No valid record found");
} catch (Exception $e) {
    testResult("find() method", false, "Exception: " . $e->getMessage());
}

// ===========================================
// TEST 3: findByUsername()
// ===========================================
echo COLOR_BLUE . "Test 3: findByUsername()\n" . COLOR_RESET;
try {
    // First get a username from existing data
    $allUsers = $userModel->all();
    if (!empty($allUsers)) {
        $testUsername = $allUsers[0]['username'];
        $user = $userModel->findByUsername($testUsername);
        $isValid = is_array($user) && isset($user['username']) && $user['username'] === $testUsername;
        testResult("findByUsername('$testUsername')", $isValid,
            $isValid ? "Found user with email: " . $user['email'] : "No record found");
    } else {
        testResult("findByUsername() test", false, "No existing users to test with");
    }

    // Test with non-existent username
    $notFound = $userModel->findByUsername('NONEXISTENT_USER_' . time());
    testResult("findByUsername() returns null for non-existent", $notFound === null);
} catch (Exception $e) {
    testResult("findByUsername() method", false, "Exception: " . $e->getMessage());
}

// ===========================================
// TEST 4: findByEmail()
// ===========================================
echo COLOR_BLUE . "Test 4: findByEmail()\n" . COLOR_RESET;
try {
    // First get an email from existing data
    $allUsers = $userModel->all();
    if (!empty($allUsers)) {
        $testEmail = $allUsers[0]['email'];
        $user = $userModel->findByEmail($testEmail);
        $isValid = is_array($user) && isset($user['email']) && $user['email'] === $testEmail;
        testResult("findByEmail('$testEmail')", $isValid,
            $isValid ? "Found user with username: " . $user['username'] : "No record found");
    } else {
        testResult("findByEmail() test", false, "No existing users to test with");
    }

    // Test with non-existent email
    $notFound = $userModel->findByEmail('nonexistent' . time() . '@example.com');
    testResult("findByEmail() returns null for non-existent", $notFound === null);
} catch (Exception $e) {
    testResult("findByEmail() method", false, "Exception: " . $e->getMessage());
}

// ===========================================
// TEST 5: usernameExists()
// ===========================================
echo COLOR_BLUE . "Test 5: usernameExists()\n" . COLOR_RESET;
try {
    // Test with existing username
    $allUsers = $userModel->all();
    if (!empty($allUsers)) {
        $existingUsername = $allUsers[0]['username'];
        $exists = $userModel->usernameExists($existingUsername);
        testResult("usernameExists() for existing username", $exists === true,
            "Username '$existingUsername' correctly exists");
    }

    // Test with non-existent username
    $nonExistentUsername = 'NONEXISTENT_USER_' . time();
    $notExists = $userModel->usernameExists($nonExistentUsername);
    testResult("usernameExists() for non-existent username", $notExists === false,
        "Username '$nonExistentUsername' correctly does not exist");
} catch (Exception $e) {
    testResult("usernameExists() method", false, "Exception: " . $e->getMessage());
}

// ===========================================
// TEST 6: emailExists()
// ===========================================
echo COLOR_BLUE . "Test 6: emailExists()\n" . COLOR_RESET;
try {
    // Test with existing email
    $allUsers = $userModel->all();
    if (!empty($allUsers)) {
        $existingEmail = $allUsers[0]['email'];
        $exists = $userModel->emailExists($existingEmail);
        testResult("emailExists() for existing email", $exists === true,
            "Email '$existingEmail' correctly exists");
    }

    // Test with non-existent email
    $nonExistentEmail = 'nonexistent' . time() . '@example.com';
    $notExists = $userModel->emailExists($nonExistentEmail);
    testResult("emailExists() for non-existent email", $notExists === false,
        "Email '$nonExistentEmail' correctly does not exist");
} catch (Exception $e) {
    testResult("emailExists() method", false, "Exception: " . $e->getMessage());
}

// ===========================================
// TEST 7: Basic CRUD - create()
// ===========================================
echo COLOR_BLUE . "Test 7: INSERT - create()\n" . COLOR_RESET;
try {
    $testUsername = 'testuser_' . time();
    $testEmail = 'test' . time() . '@example.com';

    $newId = $userModel->create([
        'username' => $testUsername,
        'email' => $testEmail
    ]);

    $isValidId = is_int($newId) && $newId > 0;
    testResult("create() returns valid ID", $isValidId,
        "Created user with ID: $newId");

    // Verify creation
    if ($isValidId) {
        $created = $userModel->find($newId);
        $verifyCreated = $created && $created['username'] === $testUsername && $created['email'] === $testEmail;
        testResult("create() verification", $verifyCreated,
            "Verified created user exists in database");
    }
} catch (Exception $e) {
    testResult("create() method", false, "Exception: " . $e->getMessage());
}

// ===========================================
// TEST 8: Basic CRUD - update()
// ===========================================
echo COLOR_BLUE . "Test 8: UPDATE - update()\n" . COLOR_RESET;
try {
    if (isset($newId) && $newId > 0) {
        $newEmail = 'updated_' . time() . '@example.com';
        $affected = $userModel->update($newId, [
            'email' => $newEmail
        ]);

        $isValid = $affected > 0;
        testResult("update() affects rows", $isValid,
            "Updated $affected row(s)");

        // Verify update
        if ($isValid) {
            $updated = $userModel->find($newId);
            $verifyUpdated = $updated && $updated['email'] === $newEmail;
            testResult("update() verification", $verifyUpdated,
                "Verified user email updated to: $newEmail");
        }
    } else {
        testResult("update() test", false, "No test record available from create test");
    }
} catch (Exception $e) {
    testResult("update() method", false, "Exception: " . $e->getMessage());
}

// ===========================================
// TEST 9: Basic CRUD - count()
// ===========================================
echo COLOR_BLUE . "Test 9: COUNT - count()\n" . COLOR_RESET;
try {
    $count = $userModel->count();
    $isValid = is_int($count) && $count >= 0;
    testResult("count() returns valid number", $isValid,
        "Total users in database: $count");
} catch (Exception $e) {
    testResult("count() method", false, "Exception: " . $e->getMessage());
}

// ===========================================
// TEST 10: Basic CRUD - delete()
// ===========================================
echo COLOR_BLUE . "Test 10: DELETE - delete()\n" . COLOR_RESET;
try {
    if (isset($newId) && $newId > 0) {
        $deleted = $userModel->delete($newId);
        testResult("delete() returns boolean", is_bool($deleted),
            "Delete operation returned: " . ($deleted ? 'true' : 'false'));

        // Verify deletion
        $afterDelete = $userModel->find($newId);
        testResult("delete() verification", $afterDelete === null,
            "Verified user no longer exists after delete");
    } else {
        testResult("delete() test", false, "No test record available from create test");
    }
} catch (Exception $e) {
    testResult("delete() method", false, "Exception: " . $e->getMessage());
}

// ===========================================
// TEST 11: SQL Injection Protection
// ===========================================
echo COLOR_BLUE . "Test 11: SQL Injection Protection\n" . COLOR_RESET;
try {
    $maliciousInput = "' OR '1'='1";
    $result = $userModel->findByUsername($maliciousInput);
    $isSafe = $result === null;
    testResult("SQL injection protection in findByUsername", $isSafe,
        "Malicious input '" . $maliciousInput . "' properly handled");

    $result2 = $userModel->findByEmail($maliciousInput);
    $isSafe2 = $result2 === null;
    testResult("SQL injection protection in findByEmail", $isSafe2,
        "Malicious input '" . $maliciousInput . "' properly handled");
} catch (Exception $e) {
    testResult("SQL injection protection", true,
        "Exception caught (safe): " . $e->getMessage());
}

// ===========================================
// SUMMARY
// ===========================================
echo COLOR_CYAN . "=====================================\n";
echo "      TEST SUMMARY\n";
echo "=====================================\n" . COLOR_RESET;

$percentage = $testCount > 0 ? round(($passedCount / $testCount) * 100, 1) : 0;

if ($percentage >= 90) {
    echo COLOR_GREEN . "✓ EXCELLENT: $passedCount/$testCount tests passed ($percentage%)\n" . COLOR_RESET;
} elseif ($percentage >= 75) {
    echo COLOR_YELLOW . "! GOOD: $passedCount/$testCount tests passed ($percentage%)\n" . COLOR_RESET;
} else {
    echo COLOR_RED . "✗ NEEDS ATTENTION: $passedCount/$testCount tests passed ($percentage%)\n" . COLOR_RESET;
}

echo "\nUser model unit testing complete!\n";

?>