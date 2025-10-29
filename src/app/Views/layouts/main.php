<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title><?php echo View::escape($title ?? 'ADA Framework'); ?></title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px;
        }

        /* Header */
        header {
            background: #2c3e50;
            color: white;
            padding: 1rem 0;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }

        header .container {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .logo {
            font-size: 1.5rem;
            font-weight: bold;
        }

        nav ul {
            list-style: none;
            display: flex;
            gap: 2rem;
        }

        nav a {
            color: white;
            text-decoration: none;
            transition: color 0.3s;
        }

        nav a:hover {
            color: #3498db;
        }

        /* Main Content */
        main {
            background: white;
            min-height: calc(100vh - 200px);
            padding: 2rem 0;
        }

        /* Footer */
        footer {
            background: #34495e;
            color: white;
            text-align: center;
            padding: 2rem 0;
            margin-top: 2rem;
        }

        /* Page heading */
        h1 {
            color: #2c3e50;
            margin-bottom: 1.5rem;
            font-size: 2.5rem;
        }

        h2 {
            color: #34495e;
            margin: 1.5rem 0 1rem;
        }

        /* Cards */
        .card {
            background: white;
            border-radius: 8px;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }

        /* Lists */
        ul.feature-list {
            list-style: none;
            padding: 0;
        }

        ul.feature-list li {
            padding: 0.5rem 0;
            padding-left: 1.5rem;
            position: relative;
        }

        ul.feature-list li:before {
            content: "✓";
            position: absolute;
            left: 0;
            color: #27ae60;
            font-weight: bold;
        }

        /* Definition list */
        dl {
            margin: 1rem 0;
        }

        dt {
            font-weight: bold;
            color: #2c3e50;
            margin-top: 1rem;
        }

        dd {
            margin-left: 1.5rem;
            margin-top: 0.5rem;
        }

        /* Utility */
        .text-muted {
            color: #7f8c8d;
        }

        .badge {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            background: #3498db;
            color: white;
            border-radius: 12px;
            font-size: 0.875rem;
        }
    </style>
</head>
<body>
    <header>
        <div class="container">
            <div class="logo">ADA Framework</div>
            <nav>
                <ul>
                    <li><a href="/">Home</a></li>
                    <li><a href="/about">About</a></li>
                    <li><a href="/contact">Contact</a></li>
                </ul>
            </nav>
        </div>
    </header>

    <main>
        <div class="container">
            <?php echo $content ?? ''; ?>
        </div>
    </main>

    <footer>
        <div class="container">
            <p>&copy; <?php echo date('Y'); ?> ADA Framework. Built with PHP, security, and simplicity in mind.</p>
            <p class="text-muted">Phase 1: Basic Routing & Views</p>
        </div>
    </footer>
</body>
</html>
