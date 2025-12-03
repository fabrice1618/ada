@extends('layouts/main')

@section('content')

<div class="card">
    <h1><?php echo View::escape($heading); ?></h1>
    <p style="font-size: 1.2rem; color: #7f8c8d; margin-top: 1rem;">
        <?php echo View::escape($message); ?>
    </p>
</div>

<?php
// Get flash messages
$success = Session::getFlash('success');
$errors = Session::getFlash('_errors', []);
?>

<?php if ($success): ?>
<div class="card" style="background-color: #d4edda; border-color: #c3e6cb; color: #155724;">
    <p style="margin: 0; font-weight: bold;">✓ <?php echo View::escape($success); ?></p>
</div>
<?php endif; ?>

<div class="card">
    <h2>Contact Form</h2>
    <p style="color: #27ae60; margin-bottom: 1rem;">
        <strong>✓ Phase 3 Complete:</strong> This form now includes CSRF protection, input validation, and secure processing!
    </p>

    <form method="POST" action="/contact" style="max-width: 600px;">
        <?php echo csrfField(); ?>

        <div style="margin-bottom: 1rem;">
            <label style="display: block; margin-bottom: 0.5rem; font-weight: bold;">Name</label>
            <input type="text" name="name" value="<?php echo View::escape(old('name')); ?>" style="width: 100%; padding: 0.5rem; border: 1px solid <?php echo isset($errors['name']) ? '#e74c3c' : '#ddd'; ?>; border-radius: 4px;" placeholder="Your name">
            <?php if (isset($errors['name'])): ?>
                <p style="color: #e74c3c; margin: 0.25rem 0 0 0; font-size: 0.875rem;"><?php echo View::escape($errors['name']); ?></p>
            <?php endif; ?>
        </div>

        <div style="margin-bottom: 1rem;">
            <label style="display: block; margin-bottom: 0.5rem; font-weight: bold;">Email</label>
            <input type="email" name="email" value="<?php echo View::escape(old('email')); ?>" style="width: 100%; padding: 0.5rem; border: 1px solid <?php echo isset($errors['email']) ? '#e74c3c' : '#ddd'; ?>; border-radius: 4px;" placeholder="your@email.com">
            <?php if (isset($errors['email'])): ?>
                <p style="color: #e74c3c; margin: 0.25rem 0 0 0; font-size: 0.875rem;"><?php echo View::escape($errors['email']); ?></p>
            <?php endif; ?>
        </div>

        <div style="margin-bottom: 1rem;">
            <label style="display: block; margin-bottom: 0.5rem; font-weight: bold;">Message</label>
            <textarea name="message" rows="5" style="width: 100%; padding: 0.5rem; border: 1px solid <?php echo isset($errors['message']) ? '#e74c3c' : '#ddd'; ?>; border-radius: 4px;" placeholder="Your message..."><?php echo View::escape(old('message')); ?></textarea>
            <?php if (isset($errors['message'])): ?>
                <p style="color: #e74c3c; margin: 0.25rem 0 0 0; font-size: 0.875rem;"><?php echo View::escape($errors['message']); ?></p>
            <?php endif; ?>
        </div>

        <button type="submit" style="background: #3498db; color: white; padding: 0.75rem 2rem; border: none; border-radius: 4px; cursor: pointer; font-size: 1rem;">
            Send Message
        </button>
    </form>
</div>

<div class="card">
    <h2>Security Features Implemented ✓</h2>
    <ul class="feature-list">
        <li><strong>CSRF Protection:</strong> Token-based validation prevents cross-site request forgery attacks</li>
        <li><strong>Input Validation:</strong> Server-side validation with error messages</li>
        <li><strong>Input Sanitization:</strong> All input is sanitized before processing</li>
        <li><strong>XSS Prevention:</strong> Output is automatically escaped to prevent XSS attacks</li>
        <li><strong>Flash Messages:</strong> User feedback persists across redirects</li>
        <li><strong>Old Input:</strong> Form repopulates on validation errors</li>
    </ul>
</div>

@endsection
