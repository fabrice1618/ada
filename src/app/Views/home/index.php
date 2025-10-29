<?php
// Start output buffering for layout
ob_start();
?>

<div class="card">
    <h1><?php echo View::escape($heading); ?></h1>
    <p style="font-size: 1.2rem; color: #7f8c8d;">
        <?php echo View::escape($message); ?>
    </p>
    <p>
        <span class="badge">Version: <?php echo View::escape($version); ?></span>
    </p>
</div>

<div class="card">
    <h2>Features</h2>
    <ul class="feature-list">
        <?php foreach ($features as $feature): ?>
            <li><?php echo View::escape($feature); ?></li>
        <?php endforeach; ?>
    </ul>
</div>

<div class="card">
    <h2>Quick Start</h2>
    <p>This is Phase 1 of the ADA Framework implementation. The following features are now working:</p>
    <ul class="feature-list">
        <li>Front Controller routing (index.php)</li>
        <li>Base Controller class with view rendering</li>
        <li>Simple View engine with template loading</li>
        <li>Route configuration system</li>
        <li>Apache URL rewriting (.htaccess)</li>
        <li>Basic error handling (404, 500)</li>
    </ul>
</div>

<div class="card">
    <h2>Coming Soon</h2>
    <p>Future phases will add:</p>
    <ul class="feature-list">
        <li><strong>Phase 2:</strong> Database layer with PDO and Models</li>
        <li><strong>Phase 3:</strong> CSRF protection, XSS prevention, secure sessions</li>
        <li><strong>Phase 4:</strong> Middleware system for request filtering</li>
        <li><strong>Phase 5:</strong> Validation system and advanced template features</li>
        <li><strong>Phase 6:</strong> Production optimization and configuration management</li>
    </ul>
</div>

<?php
// Get content and include in layout
$content = ob_get_clean();
include __DIR__ . '/../layouts/main.php';
?>
