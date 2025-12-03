<?php
// Facultatif : définir le fuseau horaire
date_default_timezone_set('Europe/Paris');

/**
 * Établit la connexion à la base de données
 * TO DO parametrer les users les MDPS
 */
function connectToDatabase() {
    try {
        $pdo = new PDO('mysql:host=db;dbname=ada;charset=utf8', 'ada', 'ada', [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
        ]);
        return $pdo;
    } catch (PDOException $e) {
        die("Erreur de connexion à la base de données : " . $e->getMessage());
    }
}

/**
 * Valide et nettoie les données personnelles du formulaire 
 * TO DO gerer XSS faille 
 */
function validatePersonalData() {
    $prenom = trim($_POST['prenom'] ?? '');
    $nom = trim($_POST['nom'] ?? '');
    
    // Validation des champs obligatoires
    if (empty($prenom)) {
        throw new Exception("Le prénom est obligatoire.");
    }
    if (empty($nom)) {
        throw new Exception("Le nom est obligatoire.");
    }
    
    return [
        'prenom' => $prenom,
        'nom' => $nom,
        'date_depot' => date('Y-m-d H:i:s')
    ];
}

/**
 * Traite l'URL fournie dans le formulaire
 */
function processUrl() {
    if (!empty($_POST['url'])) {
        $url_valide = filter_var($_POST['url'], FILTER_VALIDATE_URL);
        if ($url_valide) {
            return $url_valide;
        } else {
            throw new Exception("URL non valide.");
        }
    }
    return null;
}

/**
 * Traite le fichier uploadé
 */
function processUploadedFile() {
    if (!empty($_FILES['fichier']) && $_FILES['fichier']['error'] === UPLOAD_ERR_OK) {
        
        // Informations du fichier
        $nomfichier_original = $_FILES['fichier']['name'];
        $taille_fichier = $_FILES['fichier']['size'];
        $type_fichier = $_FILES['fichier']['type'];
        
        // Validation de la taille (ex: 10MB max)
        $taille_max = 10 * 1024 * 1024; // 10MB
        if ($taille_fichier > $taille_max) {
            throw new Exception("Le fichier est trop volumineux. Taille maximum: 10MB.");
        }
        
        // Validation du type de fichier (exemple)
        $types_autorises = ['image/jpeg', 'image/png', 'application/pdf', 'text/plain'];
        if (!in_array($type_fichier, $types_autorises)) {
            throw new Exception("Type de fichier non autorisé.");
        }
        
        // Générer un nom unique pour le stockage
        $extension = pathinfo($nomfichier_original, PATHINFO_EXTENSION);
        $nomfichier_stockage = uniqid('file_') . '.' . $extension;
        
        // Créer le dossier d'upload s'il n'existe pas
        $dossier_uploads = __DIR__ . '/uploads/';
        if (!is_dir($dossier_uploads)) {
            mkdir($dossier_uploads, 0755, true);
        }
        
        // Déplacer le fichier uploadé
        if (move_uploaded_file($_FILES['fichier']['tmp_name'], $dossier_uploads . $nomfichier_stockage)) {
            return [
                'nomfichier_original' => $nomfichier_original,
                'nomfichier_stockage' => $nomfichier_stockage,
                'taille_fichier' => $taille_fichier,
                'type_fichier' => $type_fichier
            ];
        } else {
            throw new Exception("Erreur lors de l'enregistrement du fichier sur le serveur.");
        }
    }
    
    return [
        'nomfichier_original' => null,
        'nomfichier_stockage' => null,
        'taille_fichier' => null,
        'type_fichier' => null
    ];
}

/**
 * Sauvegarde toutes les données dans la base de données
 */
function saveToDatabase($pdo, $data) {
    $stmt = $pdo->prepare("INSERT INTO deposes 
                          (prenom, nom, datedepot, url, nomfichieroriginal, nomfichierstockage, iddevoirs)
                          VALUES 
                          (:prenom, :nom, :datedepot, :url, :nomfichieroriginal, :nomfichierstockage, :iddevoirs)");
    
    $stmt->execute([
        ':prenom' => $data['prenom'],
        ':nom' => $data['nom'],
        ':datedepot' => $data['date_depot'],
        ':url' => $data['url'],
        ':nomfichieroriginal' => $data['nomfichier_original'],
        ':nomfichierstockage' => $data['nomfichier_stockage'],
        ':iddevoirs' => $data['iddevoirs']
    ]);
    
    return $pdo->lastInsertId(); // Retourne l'ID du nouveau dépôt
}

/**
 * Procédure principale de traitement du formulaire
 */
function processFormSubmission() {
    try {
        // ÉTAPE 1: Valider les données personnelles
        $personalData = validatePersonalData();
        
        // ÉTAPE 2: Traiter l'URL (optionnelle)
        $url = processUrl();
        
        // ÉTAPE 3: Traiter le fichier (optionnel)
        $fileData = processUploadedFile();
        
        // ÉTAPE 4: Vérifier qu'au moins URL ou Fichier est fourni
        if ($url === null && $fileData['nomfichier_original'] === null) {
            throw new Exception("Veuillez fournir soit une URL valide, soit un fichier à uploader.");
        }
        
        // ÉTAPE 5: Fusionner toutes les données
        $completeData = array_merge($personalData, [
            'url' => $url,
            'nomfichier_original' => $fileData['nomfichier_original'],
            'nomfichier_stockage' => $fileData['nomfichier_stockage'],
            'iddevoirs' => 1
        ]);
        
        // ÉTAPE 6: Connexion à la base de données et sauvegarde
        $pdo = connectToDatabase();
        $newId = saveToDatabase($pdo, $completeData);
        
        // ÉTAPE 7: Confirmation de succès
        header('Location: /maquette/resultat?success=1&id=' . $newId);
        exit();
        
    } catch (Exception $e) {
        echo " Erreur : " . $e->getMessage();
        exit;
    }
}

// POINT D'ENTRÉE PRINCIPAL
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    processFormSubmission();
} else {
    echo " Cette page attend une soumission de formulaire en méthode POST.";
}
?>