<?php
// database.php
$DB_HOST = "localhost";
$DB_USER = "ada";
$DB_PASS = "ada";
$DB_NAME = "ADA";

/**
 * Ouvre une connexion sécuisée à la base de données
 * @return mysqlir
 */
function open_database() {
    global $DB_HOST, $DB_USER, $DB_PASS, $DB_NAME;

    $conn = new mysqli($DB_HOST, $DB_USER, $DB_PASS, $DB_NAME);
    if ($conn->connect_error) {
        die("Erreur de connexion : " . $conn->connect_error);
    }

    $conn->set_charset("utf8mb4");
    return $conn;
}

/**
 * Ferme proprement la connexion à la base de données
 */
function close_database($conn) {
    if ($conn instanceof mysqli) {
        $conn->close();
    }
}
