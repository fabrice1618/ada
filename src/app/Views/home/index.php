@extends('layouts/main')

@section('content')

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
    <h2>Database Statistics</h2>
    <p>Live data from the database:</p>
    <ul class="feature-list">
        <li><strong>Users:</strong> <?php echo View::escape($stats['users']); ?></li>
        <li><strong>Total Assignments:</strong> <?php echo View::escape($stats['devoirs']); ?></li>
        <li><strong>Upcoming Assignments:</strong> <?php echo View::escape($stats['upcoming']); ?></li>
    </ul>
    <p style="margin-top: 1rem;">
        <a href="/devoirs" style="color: #3498db; text-decoration: none; font-weight: bold;">View All Assignments →</a>
    </p>
</div>

<div class="card">
    <h2>Phase 2 Complete!</h2>
    <p>The following database features are now working:</p>
    <ul class="feature-list">
        <li>Database connection with singleton pattern</li>
        <li>Base Model class with CRUD operations</li>
        <li>Prepared statements for SQL injection protection</li>
        <li>Model inheritance (User, Devoir, Depose models)</li>
        <li>Mass assignment protection with fillable fields</li>
        <li>Query execution with error handling</li>
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

@endsection
