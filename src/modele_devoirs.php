<?php
include "database.php";

/**
 * CRUD sécurisé pour les devoirs
 */
function manageDevoir($conn, $action, $data = []) {
    switch ($action) {
        case "create":
            if (empty($data['shortcode']) || empty($data['datelimite'])) return false;

            $stmt = $conn->prepare("INSERT INTO devoirs (shortcode, datelimite) VALUES (?, ?)");
            $stmt->bind_param("ss", $data['shortcode'], $data['datelimite']);
            return $stmt->execute();

        case "update":
            if (empty($data['id']) || empty($data['shortcode']) || empty($data['datelimite'])) return false;

            $stmt = $conn->prepare("UPDATE devoirs SET shortcode=?, datelimite=? WHERE id=?");
            $stmt->bind_param("ssi", $data['shortcode'], $data['datelimite'], $data['id']);
            return $stmt->execute();

        case "delete":
            if (empty($data['id'])) return false;

            $stmt = $conn->prepare("DELETE FROM devoirs WHERE id=?");
            $stmt->bind_param("i", $data['id']);
            return $stmt->execute();

        default:
            return false;
    }
}

/**
 * Lecture sécurisée de tous les devoirs
 */
function lireDevoirs($conn) {
    $result = $conn->query("SELECT * FROM devoirs ORDER BY datelimite ASC");
    return $result ? $result->fetch_all(MYSQLI_ASSOC) : [];
}

// --- Exécution ---
$conn = open_database();
$request = array_merge($_GET, $_POST);

if (isset($request['action'])) {
    if (manageDevoir($conn, $request['action'], $request)) {
        echo " Action '{$request['action']}' réussie.<br>";
    } else {
        echo " Erreur : paramètres manquants ou échec SQL.<br>";
    }
}

$devoirs = lireDevoirs($conn);
echo "<h2>Liste des devoirs</h2><ul>";
foreach ($devoirs as $d) {
    echo "<li>[{$d['id']}] {$d['shortcode']} - {$d['datelimite']}</li>";
}
echo "</ul>";

close_database($conn);
