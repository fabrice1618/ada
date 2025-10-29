<!DOCTYPE html>
<html>
<head>
    <title><?php echo htmlspecialchars($title ?? "Test", ENT_QUOTES, 'UTF-8'); ?></title>
</head>
<body>
    <header>Header Content</header>
    <main><?php echo self::yieldSection('content'); ?></main>
    <footer>Footer Content</footer>
</body>
</html>