<!DOCTYPE html>
<html lang="fr">

<head>
    <meta charset="UTF-8">
    <title><?= htmlspecialchars($title ?? 'Succès') ?></title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
</head>

<body class="p-5">

    <div class="container">
        <h1 class="mb-4">DM déposé avec succès !</h1>

        <div class="alert alert-success">
            <h4 class="alert-heading">Merci <?= htmlspecialchars($prenom ?? '') ?> <?= htmlspecialchars($nom ?? '') ?> !</h4>
            <p>Votre devoir <strong><?= htmlspecialchars($shortcode ?? '') ?></strong> a bien été enregistré.</p>
            <?php if (isset($devoir)): ?>
                <hr>
                <p class="mb-0">Date limite : <?= date('d/m/Y', strtotime($devoir['datelimite'])) ?></p>
            <?php endif; ?>
        </div>

        <a href="/devoir/<?= htmlspecialchars($shortcode ?? '') ?>" class="btn btn-primary">Déposer un autre fichier</a>
        <a href="/devoirs" class="btn btn-secondary">Retour aux devoirs</a>
        <a href="/" class="btn btn-secondary">Retour à l'accueil</a>
    </div>

</body>

</html>
