<?php

/**
 * View Class
 *
 * Simple template engine for rendering views with data.
 * Supports basic template loading, data extraction, and error handling.
 *
 * @package ADA Framework
 * @version 1.0 (Phase 1)
 */
class View
{
    /**
     * Render a view template with data
     *
     * @param string $template Template path (e.g., 'home/index')
     * @param array $data Data to pass to the template
     * @return string Rendered HTML
     * @throws Exception If template file not found
     */
    public static function render($template, $data = [])
    {
        // Construct template file path
        $templatePath = __DIR__ . '/../app/Views/' . $template . '.php';

        // Check if template exists
        if (!file_exists($templatePath)) {
            throw new Exception("Template not found: {$template}");
        }

        // Extract data array to variables
        // This allows $data['title'] to be accessed as $title in the template
        extract($data);

        // Start output buffering
        ob_start();

        // Include the template file
        // The template has access to all extracted variables
        include $templatePath;

        // Get buffer content and clean buffer
        $content = ob_get_clean();

        return $content;
    }

    /**
     * Escape HTML output to prevent XSS
     *
     * @param string $value Value to escape
     * @return string Escaped value
     */
    public static function escape($value)
    {
        return htmlspecialchars($value, ENT_QUOTES, 'UTF-8');
    }
}
