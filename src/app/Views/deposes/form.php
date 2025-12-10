<!DOCTYPE html>
<html lang="fr">

<head>
    <meta charset="UTF-8">
    <title><?= htmlspecialchars($title ?? 'Formulaire DM') ?></title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
</head>

<body class="p-5">

    <div class="container">
        <h1 class="mb-4">Déposer votre DM - <?= htmlspecialchars($shortcode ?? '') ?></h1>

        <?php if (isset($devoir)): ?>
            <div class="alert alert-info">
                <strong>Devoir:</strong> <?= htmlspecialchars($devoir['shortcode']) ?><br>
                <strong>Date limite:</strong> <?= date('d/m/Y', strtotime($devoir['datelimite'])) ?>
            </div>
        <?php endif; ?>

        <?php if (isset($errors) && !empty($errors)): ?>
            <div class="alert alert-danger">
                <ul class="mb-0">
                    <?php foreach ($errors as $field => $fieldErrors): ?>
                        <?php foreach ($fieldErrors as $error): ?>
                            <li><?= htmlspecialchars($error) ?></li>
                        <?php endforeach; ?>
                    <?php endforeach; ?>
                </ul>
            </div>
        <?php endif; ?>

        <form class="mb-3" method="POST" action="/devoir/<?= htmlspecialchars($shortcode ?? '') ?>" enctype="multipart/form-data">
            <!-- Nom + prénom -->
            <div class="input-group mb-3">
                <span class="input-group-text">Nom & Prénom</span>
                <input type="text" name="prenom" aria-label="First name" class="form-control w-25" 
                       placeholder="Prénom" value="<?= htmlspecialchars($old['prenom'] ?? '') ?>" required>
                <input type="text" name="nom" aria-label="Last name" class="form-control w-25" 
                       placeholder="Nom" value="<?= htmlspecialchars($old['nom'] ?? '') ?>" required>
            </div>
                
            <!-- Choix entre fichier ou GitHub -->
            <div class="mb-3">
                <label for="choice" class="form-label">Choisissez le mode de dépôt :</label>
                <select class="form-select" id="choice" name="depot_type" onchange="toggleInput()">
                    <option selected disabled>-- Sélectionnez une option --</option>
                    <option value="file">Déposer un fichier</option>
                    <option value="github">Donner un lien GitHub</option>
                </select>
            </div>

            <!-- Upload fichier -->
            <div class="input-group mb-3 d-none" id="file-field">
                <label class="input-group-text" for="inputGroupFile01">Upload</label>
                <input type="file" name="fichier" class="form-control" id="inputGroupFile01">
            </div>

            <!-- Champ GitHub -->
            <div class="mb-3 d-none" id="github-field">
                <label for="github-url" class="form-label">Lien du dépôt GitHub</label>
                <input type="url" name="github_url" class="form-control" id="github-url" 
                       placeholder="https://github.com/moncompte/monrepo"
                       value="<?= htmlspecialchars($old['github_url'] ?? '') ?>">
            </div>

            <!-- Bouton -->
            <button type="submit" class="btn btn-primary">Envoyer</button>
            <a href="/devoirs" class="btn btn-secondary">Retour aux devoirs</a>

        </form>

    </div>



    <script>
        function toggleInput() {
            const choice = document.getElementById("choice").value;
            document.getElementById("file-field").classList.toggle("d-none", choice !== "file");
            document.getElementById("github-field").classList.toggle("d-none", choice !== "github");
        }
    </script>

</body>

</html>
