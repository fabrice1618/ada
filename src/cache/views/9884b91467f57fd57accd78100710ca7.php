<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title><?= htmlspecialchars($title ?? '404 Not Found') ?></title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }

        .error-container {
            background: white;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            max-width: 600px;
            width: 100%;
            padding: 60px 40px;
            text-align: center;
        }

        .error-code {
            font-size: 120px;
            font-weight: 700;
            color: #667eea;
            line-height: 1;
            margin-bottom: 20px;
        }

        .error-heading {
            font-size: 32px;
            color: #2d3748;
            margin-bottom: 15px;
        }

        .error-message {
            font-size: 18px;
            color: #718096;
            margin-bottom: 30px;
        }

        .error-details {
            background: #f7fafc;
            border-left: 4px solid #667eea;
            padding: 15px;
            margin-bottom: 30px;
            text-align: left;
            border-radius: 4px;
            font-size: 14px;
            color: #4a5568;
        }

        .error-suggestion {
            font-size: 16px;
            color: #4a5568;
            margin-bottom: 30px;
        }

        .home-button {
            display: inline-block;
            padding: 12px 30px;
            background: #667eea;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            font-weight: 600;
            transition: background 0.3s;
        }

        .home-button:hover {
            background: #5a67d8;
        }

        .icon {
            font-size: 80px;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <div class="error-container">
        <div class="icon">🔍</div>
        <div class="error-code"><?= htmlspecialchars($code ?? '404') ?></div>
        <h1 class="error-heading"><?= htmlspecialchars($heading ?? 'Page Not Found') ?></h1>
        <p class="error-message"><?= htmlspecialchars($message ?? 'The page you are looking for could not be found.') ?></p>

        <?php if (!empty($details)): ?>
            <div class="error-details">
                <?= htmlspecialchars($details) ?>
            </div>
        <?php endif; ?>

        <p class="error-suggestion"><?= htmlspecialchars($suggestion ?? 'Please check the URL or return to the homepage.') ?></p>

        <a href="/" class="home-button">Go to Homepage</a>
    </div>
</body>
</html>
