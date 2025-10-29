<?php
// Start output buffering for layout
ob_start();
?>

<div class="card">
    <h1><?php echo View::escape($heading); ?></h1>
    <p style="font-size: 1.2rem; color: #7f8c8d; margin-top: 1rem;">
        <?php echo View::escape($message); ?>
    </p>
</div>

<div class="card">
    <h2>Contact Form (Demo)</h2>
    <p style="color: #e74c3c; margin-bottom: 1rem;">
        <strong>Note:</strong> Form processing will be implemented in Phase 3 with CSRF protection.
    </p>

    <form style="max-width: 600px;">
        <div style="margin-bottom: 1rem;">
            <label style="display: block; margin-bottom: 0.5rem; font-weight: bold;">Name</label>
            <input type="text" name="name" style="width: 100%; padding: 0.5rem; border: 1px solid #ddd; border-radius: 4px;" placeholder="Your name" disabled>
        </div>

        <div style="margin-bottom: 1rem;">
            <label style="display: block; margin-bottom: 0.5rem; font-weight: bold;">Email</label>
            <input type="email" name="email" style="width: 100%; padding: 0.5rem; border: 1px solid #ddd; border-radius: 4px;" placeholder="your@email.com" disabled>
        </div>

        <div style="margin-bottom: 1rem;">
            <label style="display: block; margin-bottom: 0.5rem; font-weight: bold;">Message</label>
            <textarea name="message" rows="5" style="width: 100%; padding: 0.5rem; border: 1px solid #ddd; border-radius: 4px;" placeholder="Your message..." disabled></textarea>
        </div>

        <button type="submit" style="background: #95a5a6; color: white; padding: 0.75rem 2rem; border: none; border-radius: 4px; cursor: not-allowed;" disabled>
            Submit (Coming Soon)
        </button>
    </form>
</div>

<div class="card">
    <h2>What's Next?</h2>
    <p>In upcoming phases, this contact form will include:</p>
    <ul class="feature-list">
        <li>CSRF token protection</li>
        <li>Input validation with error messages</li>
        <li>Secure form processing</li>
        <li>Flash messages for user feedback</li>
        <li>Email sending capability</li>
    </ul>
</div>

<?php
// Get content and include in layout
$content = ob_get_clean();
include __DIR__ . '/../layouts/main.php';
?>
