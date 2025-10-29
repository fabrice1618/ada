<?php if($show): ?>
<p>Condition is true</p>
<?php else: ?>
<p>Condition is false</p>
<?php endif; ?>

<?php foreach($items as $item): ?>
<li><?php echo htmlspecialchars($item, ENT_QUOTES, 'UTF-8'); ?></li>
<?php endforeach; ?>