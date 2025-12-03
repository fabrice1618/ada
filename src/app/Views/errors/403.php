<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title><?= htmlspecialchars($title ?? '403 Forbidden') ?></title>
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
            background: linear-gradient(135deg, #fbc2eb 0%, #a6c1ee 100%);
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
            color: #a6c1ee;
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
            background: #ebf8ff;
            border-left: 4px solid #4299e1;
            padding: 15px;
            margin-bottom: 30px;
            text-align: left;
            border-radius: 4px;
            font-size: 14px;
            color: #2c5282;
        }

        .error-suggestion {
            font-size: 16px;
            color: #4a5568;
            margin-bottom: 30px;
        }

        .home-button {
            display: inline-block;
            padding: 12px 30px;
            background: #4299e1;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            font-weight: 600;
            transition: background 0.3s;
            margin-right: 10px;
        }

        .home-button:hover {
            background: #3182ce;
        }

        .back-button {
            display: inline-block;
            padding: 12px 30px;
            background: #4a5568;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            font-weight: 600;
            transition: background 0.3s;
        }

        .back-button:hover {
            background: #2d3748;
        }

        .icon {
            font-size: 80px;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <div class="error-container">
        <div class="icon">🚫</div>
        <div class="error-code"><?= htmlspecialchars($code ?? '403') ?></div>
        <h1 class="error-heading"><?= htmlspecialchars($heading ?? 'Access Denied') ?></h1>
        <p class="error-message"><?= htmlspecialchars($message ?? 'You do not have permission to access this resource.') ?></p>

        <?php if (!empty($details)): ?>
            <div class="error-details">
                <strong>Reason:</strong> <?= htmlspecialchars($details) ?>
            </div>
        <?php endif; ?>

        <p class="error-suggestion"><?= htmlspecialchars($suggestion ?? 'Please log in or contact an administrator.') ?></p>

        <a href="/" class="home-button">Go to Homepage</a>
        <a href="javascript:history.back()" class="back-button">Go Back</a>
    </div>
</body>
</html>
