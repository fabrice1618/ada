<?php
include "database.php";

/**
 * CRUD sécurisé pour les dépôts
 */
function manageDepose($conn, $action, $data = []) {
    switch ($action) {
        case "create":
            if (empty($data['nom']) || empty($data['prenom']) || empty($data['date_depot']) ||
                empty($data['url']) || empty($data['nomfichier_original']) || 
                empty($data['nomfichier_stockage']) || empty($data['id_1'])) {
                return false;
            }

            $stmt = $conn->prepare("
                INSERT INTO deposes (nom, prenom, date_depot, url, nomfichier_original, nomfichier_stockage, id_1)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ");
            $stmt->bind_param(
                "ssssssi",
                $data['nom'],
                $data['prenom'],
                $data['date_depot'],
                $data['url'],
                $data['nomfichier_original'],
                $data['nomfichier_stockage'],
                $data['id_1']
            );
            return $stmt->execute();

        case "update":
            if (empty($data['id']) || empty($data['nom']) || empty($data['prenom']) || empty($data['date_depot']) ||
                empty($data['url']) || empty($data['nomfichier_original']) || 
                empty($data['nomfichier_stockage']) || empty($data['id_1'])) {
                return false;
            }

            $stmt = $conn->prepare("
                UPDATE deposes
                SET nom=?, prenom=?, date_depot=?, url=?, nomfichier_original=?, nomfichier_stockage=?, id_1=?
                WHERE id=?
            ");
            $stmt->bind_param(
                "ssssssii",
                $data['nom'],
                $data['prenom'],
                $data['date_depot'],
                $data['url'],
                $data['nomfichier_original'],
                $data['nomfichier_stockage'],
                $data['id_1'],
                $data['id']
            );
            return $stmt->execute();

        case "delete":
            if (empty($data['id'])) return false;
            $stmt = $conn->prepare("DELETE FROM deposes WHERE id=?");
            $stmt->bind_param("i", $data['id']);
            return $stmt->execute();

        default:
            return false;
    }
}

/**
 * Lecture sécurisée de tous les dépôts
 */
function lireDeposes($conn) {
    $sql = "
        SELECT d.*, dv.shortcode AS devoir_shortcode
        FROM deposes d
        JOIN devoirs dv ON d.id_1 = dv.id
        ORDER BY d.date_depot DESC
    ";
    $result = $conn->query($sql);
    return $result ? $result->fetch_all(MYSQLI_ASSOC) : [];
}

// --- Exécution ---
$conn = open_database();
$request = array_merge($_GET, $_POST);

if (isset($request['action'])) {
    if (manageDepose($conn, $request['action'], $request)) {
        echo " Action '{$request['action']}' réussie.<br>";
    } else {
        echo " Erreur : paramètres manquants ou échec SQL.<br>";
    }
}

$deposes = lireDeposes($conn);
echo "<h2>Liste des dépôts</h2><ul>";
foreach ($deposes as $d) {
    echo "<li>[{$d['id']}] {$d['nom']} {$d['prenom']} - {$d['date_depot']} - Devoir: {$d['devoir_shortcode']} - Fichier: {$d['nomfichier_original']}</li>";
}
echo "</ul>";

close_database($conn);
