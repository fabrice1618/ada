<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title><?= htmlspecialchars($title ?? '500 Internal Server Error') ?></title>
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
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
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
            max-width: 700px;
            width: 100%;
            padding: 60px 40px;
            text-align: center;
        }

        .error-code {
            font-size: 120px;
            font-weight: 700;
            color: #f5576c;
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
            background: #fff5f5;
            border-left: 4px solid #f5576c;
            padding: 15px;
            margin-bottom: 20px;
            text-align: left;
            border-radius: 4px;
            font-size: 14px;
            color: #742a2a;
        }

        .error-trace {
            background: #1a202c;
            color: #e2e8f0;
            padding: 20px;
            border-radius: 4px;
            text-align: left;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            overflow-x: auto;
            margin-bottom: 30px;
            max-height: 300px;
            overflow-y: auto;
        }

        .error-suggestion {
            font-size: 16px;
            color: #4a5568;
            margin-bottom: 30px;
        }

        .home-button {
            display: inline-block;
            padding: 12px 30px;
            background: #f5576c;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            font-weight: 600;
            transition: background 0.3s;
            margin-right: 10px;
        }

        .home-button:hover {
            background: #e53e3e;
        }

        .reload-button {
            display: inline-block;
            padding: 12px 30px;
            background: #4a5568;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            font-weight: 600;
            transition: background 0.3s;
        }

        .reload-button:hover {
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
        <div class="icon">⚠️</div>
        <div class="error-code"><?= htmlspecialchars($code ?? '500') ?></div>
        <h1 class="error-heading"><?= htmlspecialchars($heading ?? 'Internal Server Error') ?></h1>
        <p class="error-message"><?= htmlspecialchars($message ?? 'Something went wrong on our end.') ?></p>

        <?php if (!empty($details)): ?>
            <div class="error-details">
                <strong>Error:</strong> <?= htmlspecialchars($details) ?>
            </div>
        <?php endif; ?>

        <?php if (!empty($trace)): ?>
            <div class="error-trace">
                <strong>Stack Trace:</strong><br>
                <?= htmlspecialchars($trace) ?>
            </div>
        <?php endif; ?>

        <p class="error-suggestion"><?= htmlspecialchars($suggestion ?? 'Please try again later.') ?></p>

        <a href="/" class="home-button">Go to Homepage</a>
        <a href="javascript:location.reload()" class="reload-button">Reload Page</a>
    </div>
</body>
</html>
