<?php
// Start output buffering for layout
ob_start();
?>

<div class="card">
    <h1><?php echo View::escape($title); ?></h1>
    <p>Manage and view all assignments in the system.</p>
</div>

<?php if (empty($devoirs)): ?>
    <div class="card">
        <p>No assignments found in the database.</p>
        <p><em>Add some sample data to see assignments listed here.</em></p>
    </div>
<?php else: ?>
    <div class="card">
        <h2>Assignments List</h2>
        <table style="width: 100%; border-collapse: collapse; margin-top: 1rem;">
            <thead>
                <tr style="background-color: #f8f9fa; text-align: left;">
                    <th style="padding: 12px; border-bottom: 2px solid #dee2e6;">ID</th>
                    <th style="padding: 12px; border-bottom: 2px solid #dee2e6;">Shortcode</th>
                    <th style="padding: 12px; border-bottom: 2px solid #dee2e6;">Due Date</th>
                    <th style="padding: 12px; border-bottom: 2px solid #dee2e6;">Submissions</th>
                    <th style="padding: 12px; border-bottom: 2px solid #dee2e6;">Status</th>
                </tr>
            </thead>
            <tbody>
                <?php foreach ($devoirs as $devoir): ?>
                    <?php
                        $isPast = strtotime($devoir['datelimite']) < strtotime(date('Y-m-d'));
                        $statusColor = $isPast ? '#e74c3c' : '#27ae60';
                        $statusText = $isPast ? 'Closed' : 'Open';
                    ?>
                    <tr style="border-bottom: 1px solid #dee2e6;">
                        <td style="padding: 12px;"><?php echo View::escape($devoir['iddevoirs']); ?></td>
                        <td style="padding: 12px; font-weight: bold;">
                            <?php echo View::escape($devoir['shortcode']); ?>
                        </td>
                        <td style="padding: 12px;"><?php echo View::escape($devoir['datelimite']); ?></td>
                        <td style="padding: 12px;"><?php echo View::escape($devoir['submission_count']); ?></td>
                        <td style="padding: 12px;">
                            <span style="color: <?php echo $statusColor; ?>; font-weight: bold;">
                                <?php echo $statusText; ?>
                            </span>
                        </td>
                    </tr>
                <?php endforeach; ?>
            </tbody>
        </table>
    </div>
<?php endif; ?>

<div class="card">
    <h2>Database Operations Demo</h2>
    <p>This page demonstrates the following Model operations:</p>
    <ul class="feature-list">
        <li><code>all()</code> - Fetch all records</li>
        <li><code>count()</code> - Count records</li>
        <li>Custom query methods for business logic</li>
    </ul>
</div>

<?php
// Get content and include in layout
$content = ob_get_clean();
include __DIR__ . '/../../app/Views/layouts/main.php';
?>
