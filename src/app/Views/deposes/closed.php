<!DOCTYPE html>
<html lang="fr">

<head>
    <meta charset="UTF-8">
    <title><?= htmlspecialchars($title ?? 'Devoir fermé') ?></title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
</head>

<body class="p-5">

    <div class="container">
        <h1 class="mb-4"><?= htmlspecialchars($title ?? 'Devoir fermé') ?></h1>

        <div class="alert alert-warning">
            <h4 class="alert-heading">Impossible de déposer</h4>
            <p><?= htmlspecialchars($message ?? 'Ce devoir n\'est pas accessible.') ?></p>
            
            <?php if (isset($devoir)): ?>
                <hr>
                <p class="mb-0">
                    <strong>Devoir:</strong> <?= htmlspecialchars($devoir['shortcode']) ?><br>
                    <strong>Date limite:</strong> <?= date('d/m/Y', strtotime($devoir['datelimite'])) ?>
                </p>
            <?php endif; ?>
        </div>

        <a href="/devoirs" class="btn btn-primary">Voir tous les devoirs</a>
        <a href="/" class="btn btn-secondary">Retour à l'accueil</a>
    </div>

</body>

</html>
