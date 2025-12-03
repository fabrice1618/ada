<?php

/**
 * View Class
 *
 * Advanced template engine for rendering views with data.
 * Supports layouts, sections, includes, and control structures.
 *
 * @package ADA Framework
 * @version 1.0 (Phase 5)
 */
class View
{
    /**
     * @var array Sections content
     */
    protected static array $sections = [];

    /**
     * @var array Section stack
     */
    protected static array $sectionStack = [];

    /**
     * @var string|null Parent layout
     */
    protected static ?string $extends = null;

    /**
     * @var string Cache directory
     */
    protected static string $cacheDir = '';
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
        // Reset state for each render
        self::$sections = [];
        self::$sectionStack = [];
        self::$extends = null;

        // Get compiled template path
        $compiledPath = self::compile($template);

        // Extract data array to variables
        extract($data);

        // Start output buffering
        ob_start();

        // Include the compiled template
        include $compiledPath;

        // Get buffer content
        $content = ob_get_clean();

        // If template extends a layout, render the layout
        if (self::$extends !== null) {
            $layoutPath = self::compile(self::$extends);

            ob_start();
            include $layoutPath;
            $content = ob_get_clean();
        }

        return $content;
    }

    /**
     * Process template syntax for auto-escaping
     *
     * Converts {{ $var }} to escaped output and {!! $var !!} to raw output
     * Note: This is available but requires templates to use the syntax
     * For Phase 3, we use View::escape() directly in templates
     *
     * @param string $content Template content
     * @return string Processed content
     */
    private static function processTemplateSyntax(string $content): string
    {
        // Replace {!! $var !!} with raw output (unescaped)
        // This must be done first to avoid double-processing
        $content = preg_replace_callback('/\{!!\s*(.+?)\s*!!\}/', function ($matches) {
            return '<?php echo ' . $matches[1] . '; ?>';
        }, $content);

        // Replace {{ $var }} with escaped output
        $content = preg_replace_callback('/\{\{\s*(.+?)\s*\}\}/', function ($matches) {
            return '<?php echo htmlspecialchars(' . $matches[1] . ', ENT_QUOTES, \'UTF-8\'); ?>';
        }, $content);

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

    // ==================== TEMPLATE ENGINE METHODS ====================

    /**
     * Compile template with directives
     *
     * @param string $template Template path
     * @return string Compiled template path
     * @throws Exception If template not found
     */
    protected static function compile(string $template): string
    {
        $templatePath = __DIR__ . '/../app/Views/' . $template . '.php';

        if (!file_exists($templatePath)) {
            throw new Exception("Template not found: {$template}");
        }

        // Initialize cache directory
        if (empty(self::$cacheDir)) {
            self::$cacheDir = __DIR__ . '/../cache/views';
            if (!is_dir(self::$cacheDir)) {
                @mkdir(self::$cacheDir, 0755, true);
            }
        }

        // Generate cache path
        $cacheKey = md5($template);
        $cachePath = self::$cacheDir . '/' . $cacheKey . '.php';

        // Check if cache is fresh
        if (file_exists($cachePath) && filemtime($cachePath) >= filemtime($templatePath)) {
            return $cachePath;
        }

        // Read template content
        $content = file_get_contents($templatePath);

        // Compile directives
        $content = self::compileDirectives($content);

        // Write to cache
        file_put_contents($cachePath, $content);

        return $cachePath;
    }

    /**
     * Compile all template directives
     *
     * @param string $content Template content
     * @return string Compiled content
     */
    protected static function compileDirectives(string $content): string
    {
        // Compile in specific order
        $content = self::compileExtends($content);
        $content = self::compileSection($content);
        $content = self::compileYield($content);
        $content = self::compileInclude($content);
        $content = self::compileIf($content);
        $content = self::compileForeach($content);
        $content = self::compileFor($content);
        $content = self::processTemplateSyntax($content);

        return $content;
    }

    /**
     * Compile @extends directive
     *
     * @param string $content Template content
     * @return string Compiled content
     */
    protected static function compileExtends(string $content): string
    {
        return preg_replace('/@extends\([\'\"](.+?)[\'\"]\)/', '<?php self::$extends = \'$1\'; ?>', $content);
    }

    /**
     * Compile @section and @endsection directives
     *
     * @param string $content Template content
     * @return string Compiled content
     */
    protected static function compileSection(string $content): string
    {
        // @section('name')
        $content = preg_replace('/@section\([\'\"](.+?)[\'\"]\)/', '<?php self::startSection(\'$1\'); ?>', $content);

        // @endsection
        $content = preg_replace('/@endsection/', '<?php self::endSection(); ?>', $content);

        return $content;
    }

    /**
     * Compile @yield directive
     *
     * @param string $content Template content
     * @return string Compiled content
     */
    protected static function compileYield(string $content): string
    {
        return preg_replace('/@yield\([\'\"](.+?)[\'\"]\)/', '<?php echo self::yieldSection(\'$1\'); ?>', $content);
    }

    /**
     * Compile @include directive
     *
     * @param string $content Template content
     * @return string Compiled content
     */
    protected static function compileInclude(string $content): string
    {
        return preg_replace('/@include\([\'\"](.+?)[\'\"]\)/', '<?php echo self::render(\'$1\', get_defined_vars()); ?>', $content);
    }

    /**
     * Compile @if, @elseif, @else, @endif directives
     *
     * @param string $content Template content
     * @return string Compiled content
     */
    protected static function compileIf(string $content): string
    {
        // @if($condition)
        $content = preg_replace('/@if\((.+?)\)/', '<?php if($1): ?>', $content);

        // @elseif($condition)
        $content = preg_replace('/@elseif\((.+?)\)/', '<?php elseif($1): ?>', $content);

        // @else
        $content = preg_replace('/@else/', '<?php else: ?>', $content);

        // @endif
        $content = preg_replace('/@endif/', '<?php endif; ?>', $content);

        return $content;
    }

    /**
     * Compile @foreach and @endforeach directives
     *
     * @param string $content Template content
     * @return string Compiled content
     */
    protected static function compileForeach(string $content): string
    {
        // @foreach($array as $item)
        $content = preg_replace('/@foreach\((.+?)\)/', '<?php foreach($1): ?>', $content);

        // @endforeach
        $content = preg_replace('/@endforeach/', '<?php endforeach; ?>', $content);

        return $content;
    }

    /**
     * Compile @for and @endfor directives
     *
     * @param string $content Template content
     * @return string Compiled content
     */
    protected static function compileFor(string $content): string
    {
        // @for($i = 0; $i < 10; $i++)
        $content = preg_replace('/@for\((.+?)\)/', '<?php for($1): ?>', $content);

        // @endfor
        $content = preg_replace('/@endfor/', '<?php endfor; ?>', $content);

        return $content;
    }

    // ==================== SECTION MANAGEMENT ====================

    /**
     * Start a new section
     *
     * @param string $name Section name
     * @return void
     */
    public static function startSection(string $name): void
    {
        self::$sectionStack[] = $name;
        ob_start();
    }

    /**
     * End current section
     *
     * @return void
     */
    public static function endSection(): void
    {
        if (empty(self::$sectionStack)) {
            throw new Exception('Cannot end section without starting one.');
        }

        $name = array_pop(self::$sectionStack);
        self::$sections[$name] = ob_get_clean();
    }

    /**
     * Yield a section's content
     *
     * @param string $name Section name
     * @return string Section content
     */
    public static function yieldSection(string $name): string
    {
        return self::$sections[$name] ?? '';
    }
}
