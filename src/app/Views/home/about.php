<?php
// Start output buffering for layout
ob_start();
?>

<div class="card">
    <h1><?php echo View::escape($heading); ?></h1>
    <p style="font-size: 1.2rem; color: #7f8c8d; margin-top: 1rem;">
        <?php echo View::escape($description); ?>
    </p>
</div>

<div class="card">
    <h2>Core Principles</h2>
    <dl>
        <?php foreach ($principles as $name => $description): ?>
            <dt><?php echo View::escape($name); ?></dt>
            <dd><?php echo View::escape($description); ?></dd>
        <?php endforeach; ?>
    </dl>
</div>

<div class="card">
    <h2>Architecture</h2>
    <p>ADA follows the Model-View-Controller (MVC) pattern:</p>
    <ul class="feature-list">
        <li><strong>Models:</strong> Handle data access and business logic</li>
        <li><strong>Views:</strong> Present data to users with templates</li>
        <li><strong>Controllers:</strong> Coordinate between models and views</li>
    </ul>
</div>

<div class="card">
    <h2>Development Status</h2>
    <p>ADA is currently in <strong>Phase 1</strong> of a 6-phase implementation plan:</p>
    <ul class="feature-list">
        <li>✓ Basic routing system</li>
        <li>✓ MVC architecture foundation</li>
        <li>✓ Template engine</li>
        <li>Database layer (Phase 2)</li>
        <li>Security features (Phase 3)</li>
        <li>Middleware system (Phase 4)</li>
        <li>Validation system (Phase 5)</li>
        <li>Production optimization (Phase 6)</li>
    </ul>
</div>

<?php
// Get content and include in layout
$content = ob_get_clean();
include __DIR__ . '/../layouts/main.php';
?>
