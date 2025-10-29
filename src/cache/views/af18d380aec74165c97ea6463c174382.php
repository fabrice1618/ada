<?php self::$extends = 'test_phase5/layout'; ?>

<?php self::startSection('content'); ?>
<h1><?php echo htmlspecialchars($heading, ENT_QUOTES, 'UTF-8'); ?></h1>
<p><?php echo htmlspecialchars($message, ENT_QUOTES, 'UTF-8'); ?></p>
<?php self::endSection(); ?>