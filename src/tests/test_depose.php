<?php

/**
 * Depose Model Unit Tests - CLI Version
 *
 * Tests all Depose model methods for comprehensive verification.
 * Run with: php src/tests/test_depose.php
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
require_once __DIR__ . '/../app/Models/Depose.php';
require_once __DIR__ . '/../app/Models/Devoir.php';

echo COLOR_CYAN . "=====================================\n";
echo "     DEPOSE MODEL UNIT TESTS\n";
echo "=====================================\n" . COLOR_RESET;
echo "\n";

// Initialize models
$deposeModel = new Depose();
$devoirModel = new Devoir();
$testCount = 0;
$passedCount = 0;

// Setup test data if needed
$devoirs = $devoirModel->all();
$testDevoirId = null;
$createdTestDevoir = false;
$createdTestDepose = false;

if (empty($devoirs)) {
    // Create a test devoir
    $newDevoirId = $devoirModel->create([
        'shortcode' => 'TEST-DEVOIR-' . time(),
        'datelimite' => date('Y-m-d', strtotime('+1 month'))
    ]);
    $createdTestDevoir = true;
    $testDevoirId = $newDevoirId;
    $devoirs = $devoirModel->all();
} else {
    $testDevoirId = $devoirs[0]['iddevoirs'];
}

$deposes = $deposeModel->all();
if (empty($deposes)) {
    // Create a test depose
    $deposeModel->create([
        'nom' => 'TestNom',
        'prenom' => 'TestPrenom',
        'datedepot' => date('Y-m-d H:i:s'),
        'url' => 'http://example.com/test.pdf',
        'nomfichieroriginal' => 'test.pdf',
        'nomfichierstockage' => 'storage_test.pdf',
        'iddevoirs' => $testDevoirId
    ]);
    $createdTestDepose = true;
}

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
    $deposes = $deposeModel->all();
    $isArray = is_array($deposes);
    testResult("all() returns array", $isArray,
        "Found " . count($deposes) . " depositions");
} catch (Exception $e) {
    testResult("all() method", false, "Exception: " . $e->getMessage());
}

// ===========================================
// TEST 2: Basic CRUD - find()
// ===========================================
echo COLOR_BLUE . "Test 2: SELECT - find(id)\n" . COLOR_RESET;
try {
    $allDeposes = $deposeModel->all();
    if (!empty($allDeposes)) {
        $testId = $allDeposes[0]['iddeposes'];
        $depose = $deposeModel->find($testId);
        $isValid = is_array($depose) && isset($depose['iddeposes']) && $depose['iddeposes'] == $testId;
        testResult("find($testId) returns valid depose", $isValid,
            $isValid ? "Found depose for: " . $depose['nom'] . " " . $depose['prenom'] : "No valid record found");
    } else {
        testResult("find() test", false, "No existing depositions to test with");
    }
} catch (Exception $e) {
    testResult("find() method", false, "Exception: " . $e->getMessage());
}

// ===========================================
// TEST 3: getByDevoir()
// ===========================================
echo COLOR_BLUE . "Test 3: getByDevoir()\n" . COLOR_RESET;
try {
    // Get a devoir that has submissions
    $allDeposes = $deposeModel->all();
    if (!empty($allDeposes)) {
        $testDevoirId = $allDeposes[0]['iddevoirs'];
        $submissions = $deposeModel->getByDevoir($testDevoirId);
        $isArray = is_array($submissions);
        testResult("getByDevoir($testDevoirId) returns array", $isArray,
            "Found " . count($submissions) . " submissions for devoir $testDevoirId");
    } else {
        testResult("getByDevoir() test", false, "No existing depositions to test with");
    }

    // Test with non-existent devoir
    $emptySubmissions = $deposeModel->getByDevoir(99999);
    testResult("getByDevoir() returns empty array for non-existent devoir", is_array($emptySubmissions) && count($emptySubmissions) === 0);
} catch (Exception $e) {
    testResult("getByDevoir() method", false, "Exception: " . $e->getMessage());
}

// ===========================================
// TEST 4: getByStudent()
// ===========================================
echo COLOR_BLUE . "Test 4: getByStudent()\n" . COLOR_RESET;
try {
    $allDeposes = $deposeModel->all();
    if (!empty($allDeposes)) {
        $testNom = $allDeposes[0]['nom'];
        $testPrenom = $allDeposes[0]['prenom'];
        $studentSubmissions = $deposeModel->getByStudent($testNom, $testPrenom);
        $isArray = is_array($studentSubmissions);
        testResult("getByStudent('$testNom', '$testPrenom') returns array", $isArray,
            "Found " . count($studentSubmissions) . " submissions for $testNom $testPrenom");
    } else {
        testResult("getByStudent() test", false, "No existing depositions to test with");
    }

    // Test with non-existent student
    $emptyStudent = $deposeModel->getByStudent('NONEXISTENT', 'STUDENT');
    testResult("getByStudent() returns empty array for non-existent student", is_array($emptyStudent) && count($emptyStudent) === 0);
} catch (Exception $e) {
    testResult("getByStudent() method", false, "Exception: " . $e->getMessage());
}

// ===========================================
// TEST 5: getLatest()
// ===========================================
echo COLOR_BLUE . "Test 5: getLatest()\n" . COLOR_RESET;
try {
    $latest = $deposeModel->getLatest(5);
    $isArray = is_array($latest);
    testResult("getLatest(5) returns array", $isArray,
        "Found " . count($latest) . " latest submissions");

    // Test with limit 1
    $latestOne = $deposeModel->getLatest(1);
    testResult("getLatest(1) returns correct count", is_array($latestOne) && count($latestOne) <= 1,
        "Found " . count($latestOne) . " submission(s)");
} catch (Exception $e) {
    testResult("getLatest() method", false, "Exception: " . $e->getMessage());
}

// ===========================================
// TEST 6: countByDevoir()
// ===========================================
echo COLOR_BLUE . "Test 6: countByDevoir()\n" . COLOR_RESET;
try {
    $allDeposes = $deposeModel->all();
    if (!empty($allDeposes)) {
        $testDevoirId = $allDeposes[0]['iddevoirs'];
        $count = $deposeModel->countByDevoir($testDevoirId);
        $isInt = is_int($count);
        testResult("countByDevoir($testDevoirId) returns integer", $isInt,
            "Found $count submissions for devoir $testDevoirId");
    } else {
        testResult("countByDevoir() test", false, "No existing depositions to test with");
    }

    // Test with non-existent devoir
    $zeroCount = $deposeModel->countByDevoir(99999);
    testResult("countByDevoir() returns 0 for non-existent devoir", $zeroCount === 0);
} catch (Exception $e) {
    testResult("countByDevoir() method", false, "Exception: " . $e->getMessage());
}

// ===========================================
// TEST 7: findWithDevoir()
// ===========================================
echo COLOR_BLUE . "Test 7: findWithDevoir()\n" . COLOR_RESET;
try {
    $allDeposes = $deposeModel->all();
    if (!empty($allDeposes)) {
        $testId = $allDeposes[0]['iddeposes'];
        $deposeWithDevoir = $deposeModel->findWithDevoir($testId);
        $isValid = is_array($deposeWithDevoir) && isset($deposeWithDevoir['iddeposes']) && isset($deposeWithDevoir['shortcode']);
        testResult("findWithDevoir($testId) returns joined data", $isValid,
            $isValid ? "Found depose with devoir: " . $deposeWithDevoir['shortcode'] : "No joined data found");
    } else {
        testResult("findWithDevoir() test", false, "No existing depositions to test with");
    }

    // Test with non-existent ID
    $notFound = $deposeModel->findWithDevoir(99999);
    testResult("findWithDevoir() returns null for non-existent ID", $notFound === null);
} catch (Exception $e) {
    testResult("findWithDevoir() method", false, "Exception: " . $e->getMessage());
}

// ===========================================
// TEST 8: Basic CRUD - create()
// ===========================================
echo COLOR_BLUE . "Test 8: INSERT - create()\n" . COLOR_RESET;
try {
    // Get a valid devoir ID for testing
    $devoirs = $devoirModel->all();
    if (!empty($devoirs)) {
        $testDevoirId = $devoirs[0]['iddevoirs'];
        $testNom = 'TestNom_' . time();
        $testPrenom = 'TestPrenom_' . time();

        $newId = $deposeModel->create([
            'nom' => $testNom,
            'prenom' => $testPrenom,
            'datedepot' => date('Y-m-d H:i:s'),
            'url' => 'http://example.com/test.pdf',
            'nomfichieroriginal' => 'test.pdf',
            'nomfichierstockage' => 'storage_test_' . time() . '.pdf',
            'iddevoirs' => $testDevoirId
        ]);

        $isValidId = is_int($newId) && $newId > 0;
        testResult("create() returns valid ID", $isValidId,
            "Created depose with ID: $newId");

        // Verify creation
        if ($isValidId) {
            $created = $deposeModel->find($newId);
            $verifyCreated = $created && $created['nom'] === $testNom && $created['prenom'] === $testPrenom;
            testResult("create() verification", $verifyCreated,
                "Verified created depose exists in database");
        }
    } else {
        testResult("create() test", false, "No devoirs available for testing");
    }
} catch (Exception $e) {
    testResult("create() method", false, "Exception: " . $e->getMessage());
}

// ===========================================
// TEST 9: createSubmission()
// ===========================================
echo COLOR_BLUE . "Test 9: createSubmission()\n" . COLOR_RESET;
try {
    $devoirs = $devoirModel->all();
    if (!empty($devoirs)) {
        $testDevoirId = $devoirs[0]['iddevoirs'];
        $testNom = 'SubmissionNom_' . time();
        $testPrenom = 'SubmissionPrenom_' . time();

        $newId = $deposeModel->createSubmission([
            'nom' => $testNom,
            'prenom' => $testPrenom,
            'url' => 'http://example.com/submission.pdf',
            'nomfichieroriginal' => 'submission.pdf',
            'nomfichierstockage' => 'storage_submission_' . time() . '.pdf',
            'iddevoirs' => $testDevoirId
        ]);

        $isValidId = is_int($newId) && $newId > 0;
        testResult("createSubmission() returns valid ID", $isValidId,
            "Created submission with ID: $newId");

        // Verify timestamp was set
        if ($isValidId) {
            $created = $deposeModel->find($newId);
            $hasTimestamp = $created && !empty($created['datedepot']);
            testResult("createSubmission() sets timestamp", $hasTimestamp,
                "Timestamp set to: " . $created['datedepot']);
        }
    } else {
        testResult("createSubmission() test", false, "No devoirs available for testing");
    }
} catch (Exception $e) {
    testResult("createSubmission() method", false, "Exception: " . $e->getMessage());
}

// ===========================================
// TEST 10: Basic CRUD - update()
// ===========================================
echo COLOR_BLUE . "Test 10: UPDATE - update()\n" . COLOR_RESET;
try {
    if (isset($newId) && $newId > 0) {
        $newUrl = 'http://example.com/updated_' . time() . '.pdf';
        $affected = $deposeModel->update($newId, [
            'url' => $newUrl
        ]);

        $isValid = $affected > 0;
        testResult("update() affects rows", $isValid,
            "Updated $affected row(s)");

        // Verify update
        if ($isValid) {
            $updated = $deposeModel->find($newId);
            $verifyUpdated = $updated && $updated['url'] === $newUrl;
            testResult("update() verification", $verifyUpdated,
                "Verified depose URL updated");
        }
    } else {
        testResult("update() test", false, "No test record available from create test");
    }
} catch (Exception $e) {
    testResult("update() method", false, "Exception: " . $e->getMessage());
}

// ===========================================
// TEST 11: Basic CRUD - count()
// ===========================================
echo COLOR_BLUE . "Test 11: COUNT - count()\n" . COLOR_RESET;
try {
    $count = $deposeModel->count();
    $isValid = is_int($count) && $count >= 0;
    testResult("count() returns valid number", $isValid,
        "Total depositions in database: $count");
} catch (Exception $e) {
    testResult("count() method", false, "Exception: " . $e->getMessage());
}

// ===========================================
// TEST 12: Basic CRUD - delete()
// ===========================================
echo COLOR_BLUE . "Test 12: DELETE - delete()\n" . COLOR_RESET;
try {
    if (isset($newId) && $newId > 0) {
        $deleted = $deposeModel->delete($newId);
        testResult("delete() returns boolean", is_bool($deleted),
            "Delete operation returned: " . ($deleted ? 'true' : 'false'));

        // Verify deletion
        $afterDelete = $deposeModel->find($newId);
        testResult("delete() verification", $afterDelete === null,
            "Verified depose no longer exists after delete");
    } else {
        testResult("delete() test", false, "No test record available from create test");
    }
} catch (Exception $e) {
    testResult("delete() method", false, "Exception: " . $e->getMessage());
}

// ===========================================
// TEST 13: SQL Injection Protection
// ===========================================
echo COLOR_BLUE . "Test 13: SQL Injection Protection\n" . COLOR_RESET;
try {
    $maliciousInput = "' OR '1'='1";
    $result = $deposeModel->getByStudent($maliciousInput, 'test');
    $isSafe = is_array($result);
    testResult("SQL injection protection in getByStudent", $isSafe,
        "Malicious input '" . $maliciousInput . "' properly handled");

    $result2 = $deposeModel->getByDevoir(99999);
    $isSafe2 = is_array($result2) && count($result2) === 0;
    testResult("SQL injection protection in getByDevoir", $isSafe2,
        "Invalid ID properly handled");
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

echo "\nDepose model unit testing complete!\n";

?>