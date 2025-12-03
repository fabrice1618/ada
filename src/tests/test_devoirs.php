<?php

/**
 * Devoir Model Unit Tests - CLI Version
 *
 * Tests all Devoir model methods for Phase 2 verification.
 * Run with: php src/tests/test_devoirs.php
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
require_once __DIR__ . '/../app/Models/Devoir.php';

echo COLOR_CYAN . "=====================================\n";
echo "   DEVOIR MODEL UNIT TESTS\n";
echo "=====================================\n" . COLOR_RESET;
echo "\n";

// Initialize model
$devoirModel = new Devoir();
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
    $devoirs = $devoirModel->all();
    $hasRecords = is_array($devoirs) && count($devoirs) > 0;
    testResult("all() returns array with records", $hasRecords,
        "Found " . count($devoirs) . " devoirs");
} catch (Exception $e) {
    testResult("all() method", false, "Exception: " . $e->getMessage());
}

// ===========================================
// TEST 2: Basic CRUD - find()
// ===========================================
echo COLOR_BLUE . "Test 2: SELECT - find(id)\n" . COLOR_RESET;
try {
    $devoir = $devoirModel->find(2);
    $isValid = is_array($devoir) && isset($devoir['iddevoirs']) && $devoir['iddevoirs'] == 2;
    testResult("find(2) returns valid devoir", $isValid,
        $isValid ? "Found devoir: " . $devoir['shortcode'] : "No valid record found");
} catch (Exception $e) {
    testResult("find() method", false, "Exception: " . $e->getMessage());
}

// ===========================================
// TEST 3: findByShortcode()
// ===========================================
echo COLOR_BLUE . "Test 3: findByShortcode()\n" . COLOR_RESET;
try {
    $devoir = $devoirModel->findByShortcode('DATABASE-101');
    $isValid = is_array($devoir) && isset($devoir['shortcode']) && $devoir['shortcode'] === 'DATABASE-101';
    testResult("findByShortcode('DATABASE-101')", $isValid,
        $isValid ? "Found devoir with datelimite: " . $devoir['datelimite'] : "No record found");

    // Test with non-existent shortcode
    $notFound = $devoirModel->findByShortcode('NONEXISTENT');
    testResult("findByShortcode() returns null for non-existent", $notFound === null);
} catch (Exception $e) {
    testResult("findByShortcode() method", false, "Exception: " . $e->getMessage());
}

// ===========================================
// TEST 4: getUpcoming()
// ===========================================
echo COLOR_BLUE . "Test 4: getUpcoming()\n" . COLOR_RESET;
try {
    $upcoming = $devoirModel->getUpcoming();
    $isArray = is_array($upcoming);
    testResult("getUpcoming() returns array", $isArray,
        "Found " . count($upcoming) . " upcoming devoirs");

    // Test with specific date
    $futureDate = date('Y-m-d', strtotime('+1 year'));
    $futureUpcoming = $devoirModel->getUpcoming($futureDate);
    testResult("getUpcoming() with future date", is_array($futureUpcoming),
        "Found " . count($futureUpcoming) . " devoirs after $futureDate");

    // Test with past date
    $pastDate = '2020-01-01';
    $pastUpcoming = $devoirModel->getUpcoming($pastDate);
    testResult("getUpcoming() with past date", is_array($pastUpcoming) && count($pastUpcoming) >= count($upcoming),
        "Found " . count($pastUpcoming) . " devoirs after $pastDate (should include all current)");
} catch (Exception $e) {
    testResult("getUpcoming() method", false, "Exception: " . $e->getMessage());
}

// ===========================================
// TEST 5: getPast()
// ===========================================
echo COLOR_BLUE . "Test 5: getPast()\n" . COLOR_RESET;
try {
    $past = $devoirModel->getPast();
    $isArray = is_array($past);
    testResult("getPast() returns array", $isArray,
        "Found " . count($past) . " past devoirs");

    // Test with specific date
    $futureDate = date('Y-m-d', strtotime('+1 year'));
    $futurePast = $devoirModel->getPast($futureDate);
    testResult("getPast() with future date", is_array($futurePast) && count($futurePast) >= count($past),
        "Found " . count($futurePast) . " devoirs before $futureDate (should include all current past)");

    // Test with very old date
    $oldDate = '2000-01-01';
    $oldPast = $devoirModel->getPast($oldDate);
    testResult("getPast() with old date", is_array($oldPast) && count($oldPast) === 0,
        "Found " . count($oldPast) . " devoirs before $oldDate (should be 0)");
} catch (Exception $e) {
    testResult("getPast() method", false, "Exception: " . $e->getMessage());
}

// ===========================================
// TEST 6: isOpen()
// ===========================================
echo COLOR_BLUE . "Test 6: isOpen()\n" . COLOR_RESET;
try {
    // Test with existing devoir
    $isOpen = $devoirModel->isOpen(2);
    $isBool = is_bool($isOpen);
    testResult("isOpen(2) returns boolean", $isBool,
        "Devoir 2 is " . ($isOpen ? "open" : "closed"));

    // Test with non-existent devoir
    $nonExistentOpen = $devoirModel->isOpen(999);
    testResult("isOpen() for non-existent devoir", $nonExistentOpen === false,
        "Non-existent devoir correctly returns false");
} catch (Exception $e) {
    testResult("isOpen() method", false, "Exception: " . $e->getMessage());
}

// ===========================================
// TEST 7: Basic CRUD - create()
// ===========================================
echo COLOR_BLUE . "Test 7: INSERT - create()\n" . COLOR_RESET;
try {
    $testShortcode = 'TEST-' . time();
    $futureDate = date('Y-m-d', strtotime('+30 days'));

    $newId = $devoirModel->create([
        'shortcode' => $testShortcode,
        'datelimite' => $futureDate
    ]);

    $isValidId = is_int($newId) && $newId > 0;
    testResult("create() returns valid ID", $isValidId,
        "Created devoir with ID: $newId");

    // Verify creation
    if ($isValidId) {
        $created = $devoirModel->find($newId);
        $verifyCreated = $created && $created['shortcode'] === $testShortcode;
        testResult("create() verification", $verifyCreated,
            "Verified created devoir exists in database");
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
        $newDate = date('Y-m-d', strtotime('+60 days'));
        $affected = $devoirModel->update($newId, [
            'datelimite' => $newDate
        ]);

        $isValid = $affected > 0;
        testResult("update() affects rows", $isValid,
            "Updated $affected row(s)");

        // Verify update
        if ($isValid) {
            $updated = $devoirModel->find($newId);
            $verifyUpdated = $updated && $updated['datelimite'] === $newDate;
            testResult("update() verification", $verifyUpdated,
                "Verified devoir date updated to: $newDate");
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
    $count = $devoirModel->count();
    $isValid = is_int($count) && $count >= 0;
    testResult("count() returns valid number", $isValid,
        "Total devoirs in database: $count");
} catch (Exception $e) {
    testResult("count() method", false, "Exception: " . $e->getMessage());
}

// ===========================================
// TEST 10: Basic CRUD - delete()
// ===========================================
echo COLOR_BLUE . "Test 10: DELETE - delete()\n" . COLOR_RESET;
try {
    if (isset($newId) && $newId > 0) {
        $deleted = $devoirModel->delete($newId);
        testResult("delete() returns boolean", is_bool($deleted),
            "Delete operation returned: " . ($deleted ? 'true' : 'false'));

        // Verify deletion
        $afterDelete = $devoirModel->find($newId);
        testResult("delete() verification", $afterDelete === null,
            "Verified devoir no longer exists after delete");
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
    $result = $devoirModel->findByShortcode($maliciousInput);
    $isSafe = $result === null;
    testResult("SQL injection protection", $isSafe,
        "Malicious input '" . $maliciousInput . "' properly handled");
} catch (Exception $e) {
    testResult("SQL injection protection", true,
        "Exception caught (safe): " . $e->getMessage());
}

// ===========================================
// SUMMARY
// ===========================================
echo COLOR_CYAN . "=====================================\n";
echo "   TEST SUMMARY\n";
echo "=====================================\n" . COLOR_RESET;

$percentage = $testCount > 0 ? round(($passedCount / $testCount) * 100, 1) : 0;

if ($percentage >= 90) {
    echo COLOR_GREEN . "✓ EXCELLENT: $passedCount/$testCount tests passed ($percentage%)\n" . COLOR_RESET;
} elseif ($percentage >= 75) {
    echo COLOR_YELLOW . "! GOOD: $passedCount/$testCount tests passed ($percentage%)\n" . COLOR_RESET;
} else {
    echo COLOR_RED . "✗ NEEDS ATTENTION: $passedCount/$testCount tests passed ($percentage%)\n" . COLOR_RESET;
}

echo "\nDevoir model unit testing complete!\n";

?>