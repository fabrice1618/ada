<?php
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ADA Application</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .section { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
        .section h2 { margin-top: 0; color: #333; }
        pre { background: #f5f5f5; padding: 10px; border-radius: 3px; overflow-x: auto; }
    </style>
</head>
<body>
    <h1>ADA Application - Debug Information</h1>

    <div class="section">
        <h2>$_SERVER</h2>
        <pre><?php print_r($_SERVER); ?></pre>
    </div>

    <div class="section">
        <h2>$_COOKIE</h2>
        <pre><?php print_r($_COOKIE); ?></pre>
    </div>

    <div class="section">
        <h2>$_GET</h2>
        <pre><?php print_r($_GET); ?></pre>
    </div>

    <div class="section">
        <h2>$_POST</h2>
        <pre><?php print_r($_POST); ?></pre>
    </div>
</body>
</html>