# ADA PHP Micro Framework - Developer Documentation

**Version**: 1.0.0
**PHP Version**: 8.0+
**Status**: Production Ready
**Last Updated**: 2025-10-29

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Installation & Setup](#2-installation--setup)
3. [Core Concepts](#3-core-concepts)
4. [Routing](#4-routing)
5. [Controllers](#5-controllers)
6. [Models & Database](#6-models--database)
7. [Views & Templates](#7-views--templates)
8. [Validation](#8-validation)
9. [Security](#9-security)
10. [Middleware](#10-middleware)
11. [Request & Response](#11-request--response)
12. [Configuration & Environment](#12-configuration--environment)
13. [Logging](#13-logging)
14. [Helper Functions](#14-helper-functions)
15. [Error Handling](#15-error-handling)
16. [Complete Examples](#16-complete-examples)
17. [Deployment](#17-deployment)
18. [API Reference](#18-api-reference)

---

## 1. Introduction

### What is ADA?

**ADA** is a lightweight, production-ready PHP micro framework with **zero external dependencies**. Built with security and performance in mind, ADA provides everything you need for modern web application development:

- ✅ **MVC Architecture** - Clean separation of concerns
- ✅ **RESTful Routing** - Dynamic parameters, named routes, route groups
- ✅ **Database ORM** - Query builder with prepared statements
- ✅ **Template Engine** - Blade-like syntax with layouts and directives
- ✅ **Form Validation** - 15+ validation rules out of the box
- ✅ **Security First** - CSRF, XSS, SQL injection protection built-in
- ✅ **Middleware Pipeline** - Request filtering and authentication
- ✅ **Session Management** - Secure, HTTP-only sessions
- ✅ **File Uploads** - Validation and handling included
- ✅ **Configuration System** - Environment variables and config files
- ✅ **Logging** - PSR-3 compatible with 8 log levels
- ✅ **Error Handling** - Beautiful error pages with detailed debugging

### Key Features

**Zero Dependencies**: No Composer packages required - pure PHP implementation.

**Security Hardened**: CSRF tokens, XSS prevention, SQL injection protection, secure sessions, password hashing.

**Performance Optimized**: Template caching, query builder, lazy loading, OPcache support.

**Developer Friendly**: 30+ helper functions, intuitive API, comprehensive documentation.

### Framework Statistics

- **Total Lines of Code**: ~5,000+
- **Core Classes**: 15
- **Helper Functions**: 30+
- **Validation Rules**: 15+
- **Template Directives**: 10+
- **Built-in Middleware**: 3
- **Log Levels**: 8 (PSR-3)

---

## 2. Installation & Setup

### Requirements

- **PHP**: 8.0 or higher
- **Web Server**: Apache 2.4+ or Nginx 1.18+
- **Database**: MySQL 5.7+ or MariaDB 10.3+
- **PHP Extensions**: pdo, pdo_mysql, mysqli, mbstring, openssl, json, fileinfo

### Quick Start

#### 1. Clone or Download

```bash
git clone https://github.com/yourusername/ada-framework.git
cd ada-framework
```

#### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` file with your configuration:

```ini
APP_NAME="My Application"
APP_ENV=development
APP_DEBUG=true
APP_URL=http://localhost:8080

DB_HOST=localhost
DB_NAME=your_database
DB_USER=your_user
DB_PASS=your_password
```

#### 3. Set Permissions

```bash
chmod -R 775 src/cache
chmod -R 775 src/logs
chmod -R 775 filestore
chmod 600 .env
```

Or use the provided script:

```bash
./fix-permissions.sh
```

#### 4. Configure Web Server

**Apache**: The `.htaccess` file is already configured. Ensure `mod_rewrite` is enabled:

```bash
sudo a2enmod rewrite
sudo systemctl restart apache2
```

**Nginx**: See `DEPLOYMENT.md` for Nginx configuration examples.

#### 5. Database Setup

Import the database schema:

```bash
mysql -u your_user -p your_database < database/01-init.sql
```

#### 6. Test Installation

Visit `http://localhost:8080/` in your browser. You should see the ADA welcome page.

### Directory Structure

```
ada/
├── src/
│   ├── index.php           # Front controller (entry point)
│   ├── .htaccess          # Apache rewrite rules
│   │
│   ├── app/               # Application code
│   │   ├── Controllers/   # Controller classes
│   │   ├── Models/        # Model classes
│   │   └── Views/         # Template files
│   │       ├── layouts/   # Layout templates
│   │       ├── errors/    # Error pages
│   │       └── home/      # Page templates
│   │
│   ├── config/            # Configuration files
│   │   ├── app.php       # Application config
│   │   ├── database.php  # Database config
│   │   └── routes.php    # Route definitions
│   │
│   ├── core/              # Framework core classes
│   │   ├── Router.php    # Routing system
│   │   ├── Controller.php# Base controller
│   │   ├── Model.php     # Base model/ORM
│   │   ├── View.php      # Template engine
│   │   ├── Request.php   # HTTP request
│   │   ├── Response.php  # HTTP response
│   │   ├── Validator.php # Form validation
│   │   ├── Security.php  # Security features
│   │   ├── Session.php   # Session management
│   │   ├── Middleware.php# Middleware base
│   │   ├── Database.php  # Database connection
│   │   ├── ErrorHandler.php # Error handling
│   │   ├── Config.php    # Configuration management
│   │   ├── Env.php       # Environment variables
│   │   ├── Logger.php    # Logging system
│   │   └── helpers.php   # Helper functions
│   │
│   ├── middleware/        # Middleware classes
│   │   ├── AuthMiddleware.php
│   │   ├── CsrfMiddleware.php
│   │   └── SessionMiddleware.php
│   │
│   ├── cache/             # Cache directory
│   │   └── views/        # Compiled templates
│   │
│   ├── logs/              # Log files
│   └── filestore/         # Uploaded files
│
├── database/              # Database migrations
├── .env                   # Environment configuration (not in git)
├── .env.example          # Environment template
├── DOCUMENTATION.md      # This file
├── DEPLOYMENT.md         # Deployment guide
└── README.md             # Project readme
```

---

## 3. Core Concepts

### MVC Architecture

ADA follows the **Model-View-Controller** (MVC) pattern:

**Model**: Handles data and business logic
- Represents database tables
- Performs CRUD operations
- Contains business logic
- Located in `src/app/Models/`

**View**: Presents data to users
- Template files with HTML
- Uses template engine directives
- Receives data from controllers
- Located in `src/app/Views/`

**Controller**: Coordinates between Model and View
- Handles HTTP requests
- Processes user input
- Calls models for data
- Returns views or responses
- Located in `src/app/Controllers/`

### Request Lifecycle

1. **Request arrives** → Web server routes all requests to `index.php`
2. **Front Controller** → `index.php` initializes the framework
3. **Router** → Matches request URI to a route
4. **Middleware** → Runs middleware pipeline (session, CSRF, auth, etc.)
5. **Controller** → Instantiates controller and calls action method
6. **Model** → Controller interacts with models if needed
7. **View** → Controller renders view with data
8. **Response** → Response sent back to browser

### Autoloading

Classes are manually required in `index.php`. The framework loads:
- Core classes from `src/core/`
- Application classes on-demand from `src/app/`
- Middleware from `src/middleware/`

### Naming Conventions

**Classes**: `PascalCase`
```php
class UserController extends Controller { }
class User extends Model { }
```

**Methods**: `camelCase`
```php
public function getUserProfile() { }
public function updatePassword() { }
```

**Database**: `snake_case`
```php
$table = 'user_profiles';
$column = 'created_at';
```

**Files**: `PascalCase.php` for classes
```
UserController.php
PostModel.php
```

---

## 4. Routing

### Basic Routing

Routes are defined in `src/config/routes.php`:

```php
// GET route
$router->get('/', 'HomeController@index');
$router->get('/about', 'HomeController@about');

// POST route
$router->post('/contact', 'ContactController@submit');

// PUT route
$router->put('/users/{id}', 'UserController@update');

// DELETE route
$router->delete('/users/{id}', 'UserController@destroy');

// PATCH route
$router->patch('/users/{id}', 'UserController@patch');

// Respond to any HTTP method
$router->any('/api/webhook', 'WebhookController@handle');
```

### Dynamic Parameters

Capture values from URLs using `{parameter}` syntax:

```php
// Single parameter
$router->get('/user/{id}', 'UserController@show');
// Matches: /user/123, /user/abc

// Multiple parameters
$router->get('/post/{slug}/comment/{id}', 'CommentController@show');
// Matches: /post/hello-world/comment/5

// Controller method receives parameters
public function show(Request $request) {
    $id = $request->routeParam('id');
    $slug = $request->routeParam('slug');
}
```

### Named Routes

Assign names to routes for easy URL generation:

```php
// Define named route
$router->get('/user/{id}', 'UserController@show', [
    'name' => 'user.profile'
]);

$router->post('/user/{id}/update', 'UserController@update', [
    'name' => 'user.update'
]);

// Generate URL from route name
$url = $router->route('user.profile', ['id' => 123]);
// Result: /user/123

// In templates
<a href="<?php echo $router->route('user.profile', ['id' => $userId]); ?>">
    View Profile
</a>

// Or use helper function
$url = route('user.profile', ['id' => 123]);
```

### Route Groups

Group routes with common attributes:

```php
// Admin routes with prefix and middleware
$router->group(['prefix' => '/admin', 'middleware' => ['auth', 'admin']], function($router) {
    $router->get('/dashboard', 'AdminController@dashboard', ['name' => 'admin.dashboard']);
    $router->get('/users', 'AdminController@users', ['name' => 'admin.users']);
    $router->get('/settings', 'AdminController@settings', ['name' => 'admin.settings']);
});
// Routes become: /admin/dashboard, /admin/users, /admin/settings

// API routes with prefix
$router->group(['prefix' => '/api/v1'], function($router) {
    $router->get('/users', 'Api\\UserController@index');
    $router->post('/users', 'Api\\UserController@store');
    $router->get('/users/{id}', 'Api\\UserController@show');
});
// Routes become: /api/v1/users, /api/v1/users/123

// Nested groups
$router->group(['prefix' => '/api'], function($router) {
    $router->group(['prefix' => '/v1', 'middleware' => ['api.auth']], function($router) {
        $router->get('/posts', 'Api\\PostController@index');
    });
});
```

### Route Middleware

Apply middleware to specific routes:

```php
// Single middleware
$router->get('/dashboard', 'DashboardController@index', [
    'middleware' => ['auth']
]);

// Multiple middleware
$router->get('/admin', 'AdminController@index', [
    'middleware' => ['auth', 'admin', 'verified']
]);

// Group middleware
$router->group(['middleware' => ['auth']], function($router) {
    $router->get('/profile', 'ProfileController@show');
    $router->get('/settings', 'SettingsController@index');
});
```

### Global Middleware

Apply middleware to all routes:

```php
// In index.php or routes.php
$router->setGlobalMiddleware([
    'SessionMiddleware',
    'CsrfMiddleware'
]);
```

### Callable Routes

Use closures for simple routes:

```php
$router->get('/hello', function(Request $request) {
    return Response::json(['message' => 'Hello World']);
});

$router->get('/test/{name}', function(Request $request) {
    $name = $request->routeParam('name');
    return new Response("Hello, {$name}!");
});
```

---

## 5. Controllers

### Creating Controllers

Controllers extend the base `Controller` class and are stored in `src/app/Controllers/`:

```php
<?php
// src/app/Controllers/PostController.php

class PostController extends Controller
{
    /**
     * Display list of posts
     */
    public function index(Request $request): Response
    {
        $posts = (new Post())->all();

        return $this->view('posts/index', [
            'posts' => $posts
        ]);
    }

    /**
     * Show single post
     */
    public function show(Request $request): Response
    {
        $id = $request->routeParam('id');
        $post = (new Post())->find($id);

        if (!$post) {
            abort(404, 'Post not found');
        }

        return $this->view('posts/show', [
            'post' => $post
        ]);
    }

    /**
     * Store new post
     */
    public function store(Request $request): Response
    {
        // Validate input
        $data = $this->validate($request->all(), [
            'title' => 'required|min:5|max:200',
            'body' => 'required|min:10',
            'author_id' => 'required|integer|exists:users,id'
        ]);

        // Create post
        $postId = (new Post())->create($data);

        // Redirect with success message
        return $this->redirect('/posts')
            ->with('success', 'Post created successfully!');
    }

    /**
     * Update existing post
     */
    public function update(Request $request): Response
    {
        $id = $request->routeParam('id');

        $data = $this->validate($request->all(), [
            'title' => 'required|min:5|max:200',
            'body' => 'required|min:10'
        ]);

        (new Post())->update($id, $data);

        return $this->redirect("/posts/{$id}")
            ->with('success', 'Post updated!');
    }

    /**
     * Delete post
     */
    public function destroy(Request $request): Response
    {
        $id = $request->routeParam('id');
        (new Post())->delete($id);

        return $this->redirect('/posts')
            ->with('success', 'Post deleted!');
    }
}
```

### Base Controller Methods

The `Controller` base class provides helpful methods:

```php
// Render a view
protected function view(string $template, array $data = []): Response

// Redirect to URL
protected function redirect(string $url): Response

// JSON response
protected function json($data, int $statusCode = 200): Response

// Validate request data
protected function validate(array $data, array $rules, array $messages = []): array
```

### Controller Responses

Controllers can return different response types:

```php
// View response
return $this->view('home/index', ['title' => 'Home']);

// JSON response
return $this->json(['success' => true, 'data' => $users]);

// Redirect response
return $this->redirect('/dashboard');

// Response object (for advanced usage)
return Response::download('/path/to/file.pdf', 'invoice.pdf');
```

### Dependency Injection

Controllers receive the `Request` object as the first parameter:

```php
public function index(Request $request): Response
{
    // Access request data
    $search = $request->input('search');
    $page = $request->input('page', 1);

    // ...
}
```

Route parameters are also available:

```php
// Route: /user/{id}/post/{postId}
public function show(Request $request): Response
{
    $userId = $request->routeParam('id');
    $postId = $request->routeParam('postId');

    // ...
}
```

### Resource Controllers

While not built-in, you can follow RESTful conventions:

```php
class PostController extends Controller
{
    public function index()    // GET    /posts          - List all
    public function create()   // GET    /posts/create   - Show create form
    public function store()    // POST   /posts          - Save new
    public function show()     // GET    /posts/{id}     - Show one
    public function edit()     // GET    /posts/{id}/edit - Show edit form
    public function update()   // PUT    /posts/{id}     - Update
    public function destroy()  // DELETE /posts/{id}     - Delete
}
```

---

## 6. Models & Database

### Creating Models

Models extend the base `Model` class and represent database tables:

```php
<?php
// src/app/Models/User.php

class User extends Model
{
    /**
     * Database table name
     */
    protected string $table = 'users';

    /**
     * Primary key column
     */
    protected string $primaryKey = 'id';

    /**
     * Fields allowed for mass assignment
     */
    protected array $fillable = [
        'name',
        'email',
        'password',
        'role'
    ];

    /**
     * Enable automatic timestamps
     */
    protected bool $timestamps = true;
}
```

### CRUD Operations

**Create** - Insert new records:

```php
$user = new User();

// Create single record
$userId = $user->create([
    'name' => 'John Doe',
    'email' => 'john@example.com',
    'password' => Security::hashPassword('secret'),
    'role' => 'user'
]);

// $userId contains the inserted ID
```

**Read** - Retrieve records:

```php
$user = new User();

// Get all records
$allUsers = $user->all();

// Find by primary key
$user = $user->find(1);

// Find by specific field
$user = $user->findBy('email', 'john@example.com');

// Get first record
$firstUser = $user->first();

// Simple where clause
$activeUsers = $user->where('status', 'active');

// Count records
$total = $user->count();

// Check if exists
$exists = $user->exists(123);
```

**Update** - Modify existing records:

```php
$user = new User();

// Update by ID
$affected = $user->update(1, [
    'name' => 'Jane Doe',
    'email' => 'jane@example.com'
]);

// $affected contains number of rows updated
```

**Delete** - Remove records:

```php
$user = new User();

// Delete by ID
$success = $user->delete(1);

// Returns true if deleted, false otherwise
```

### Query Builder

Chain methods to build complex queries:

```php
$user = new User();

// Select specific columns
$users = $user->select(['id', 'name', 'email'])
              ->get();

// Where conditions
$users = $user->whereCondition('status', '=', 'active')
              ->whereCondition('role', '=', 'admin')
              ->get();

// Order by
$users = $user->orderBy('created_at', 'DESC')
              ->get();

// Limit results
$users = $user->limit(10)
              ->get();

// Offset (for pagination)
$users = $user->offset(20)
              ->get();

// Complete example - pagination
$page = 2;
$perPage = 15;

$users = $user->select(['id', 'name', 'email', 'created_at'])
              ->whereCondition('status', '=', 'active')
              ->orderBy('name', 'ASC')
              ->limit($perPage)
              ->offset(($page - 1) * $perPage)
              ->get();
```

### Raw Queries

For complex queries not supported by the query builder:

```php
class User extends Model
{
    public function findActiveWithPosts()
    {
        $sql = "SELECT users.*, COUNT(posts.id) as post_count
                FROM users
                LEFT JOIN posts ON posts.user_id = users.id
                WHERE users.status = ?
                GROUP BY users.id";

        $stmt = $this->query($sql, ['active']);
        return $stmt ? $stmt->fetchAll() : [];
    }
}
```

### Timestamps

Enable automatic `created_at` and `updated_at` timestamps:

```php
class Post extends Model
{
    protected bool $timestamps = true;  // Enable timestamps

    // Timestamps are automatically set on create() and update()
}

// Your database table should have these columns:
// created_at TIMESTAMP NULL DEFAULT NULL
// updated_at TIMESTAMP NULL DEFAULT NULL
```

### Mass Assignment Protection

Use `$fillable` to whitelist fields that can be mass-assigned:

```php
class User extends Model
{
    protected array $fillable = ['name', 'email', 'role'];

    // This is SAFE - only fillable fields are inserted
    $user->create($_POST);  // Even if $_POST has 'is_admin', it's ignored
}
```

### Database Configuration

Configure database in `src/config/database.php`:

```php
return [
    'driver' => 'mysql',
    'host' => env('DB_HOST', 'localhost'),
    'database' => env('DB_NAME', 'ada'),
    'username' => env('DB_USER', 'root'),
    'password' => env('DB_PASS', ''),
    'charset' => 'utf8mb4',
    'collation' => 'utf8mb4_unicode_ci',
    'options' => [
        PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
        PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
        PDO::ATTR_EMULATE_PREPARES => false,
    ]
];
```

### Direct Database Access

Access PDO directly if needed:

```php
$db = Database::getInstance();
$pdo = $db->getConnection();

// Use PDO directly
$stmt = $pdo->prepare("SELECT * FROM users WHERE id = ?");
$stmt->execute([123]);
$user = $stmt->fetch();
```

---

## 7. Views & Templates

### Template Basics

Views are stored in `src/app/Views/` and use a Blade-like template engine:

```php
// src/app/Views/home/index.php
@extends('layouts/main')

@section('title', 'Home Page')

@section('content')
    <h1>{{ $heading }}</h1>
    <p>{{ $message }}</p>
@endsection
```

### Layout System

**Parent Layout** (`src/app/Views/layouts/main.php`):

```php
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>@yield('title', 'My App')</title>
    <?php echo csrfMeta(); ?>
</head>
<body>
    <nav>
        @include('partials/navigation')
    </nav>

    <main>
        @yield('content')
    </main>

    <footer>
        @yield('footer', '<p>Default footer</p>')
    </footer>
</body>
</html>
```

**Child Template**:

```php
@extends('layouts/main')

@section('title', 'About Us')

@section('content')
    <h1>About Us</h1>
    <p>Company information here...</p>
@endsection

@section('footer')
    <p>Custom footer for about page</p>
@endsection
```

### Template Directives

**@extends** - Extend a parent layout:
```php
@extends('layouts/main')
@extends('layouts/admin')
```

**@section** - Define a section:
```php
@section('content')
    // Section content here
@endsection

// Inline section (single line)
@section('title', 'Page Title')
```

**@yield** - Output a section:
```php
@yield('content')
@yield('sidebar', '<p>Default content</p>')  // With default
```

**@include** - Include a partial:
```php
@include('partials/header')
@include('partials/sidebar')
```

### Output Escaping

**Escaped Output** (safe from XSS):
```php
{{ $variable }}
{{ $user['name'] }}
{{ $post['title'] }}
```

Compiles to:
```php
<?php echo View::escape($variable); ?>
```

**Raw Output** (unescaped):
```php
{!! $htmlContent !!}
{!! $trustedHtml !!}
```

Compiles to:
```php
<?php echo $htmlContent; ?>
```

⚠️ **Never use raw output with user input!**

### Control Structures

**If Statements**:
```php
@if($user['role'] === 'admin')
    <p>Welcome, Admin!</p>
@elseif($user['role'] === 'moderator')
    <p>Welcome, Moderator!</p>
@else
    <p>Welcome, User!</p>
@endif
```

**Foreach Loops**:
```php
@foreach($posts as $post)
    <article>
        <h2>{{ $post['title'] }}</h2>
        <p>{{ $post['body'] }}</p>
    </article>
@endforeach
```

**For Loops**:
```php
@for($i = 0; $i < 10; $i++)
    <p>Number {{ $i }}</p>
@endfor
```

### Passing Data to Views

**From Controller**:
```php
public function index(Request $request): Response
{
    $users = (new User())->all();

    return $this->view('users/index', [
        'users' => $users,
        'title' => 'User List',
        'count' => count($users)
    ]);
}
```

**Access in View**:
```php
<h1>{{ $title }}</h1>
<p>Total users: {{ $count }}</p>

@foreach($users as $user)
    <p>{{ $user['name'] }}</p>
@endforeach
```

### Template Caching

Templates are automatically compiled and cached:

- **Cache Location**: `src/cache/views/`
- **Cache Key**: MD5 hash of template path
- **Cache Invalidation**: Automatic when template file changes
- **Enable/Disable**: Set `VIEW_CACHE` in `.env`

```ini
# .env
VIEW_CACHE=true   # Enable caching (production)
VIEW_CACHE=false  # Disable caching (development)
```

Clear cache manually:
```bash
rm -rf src/cache/views/*
```

### Partials/Components

Create reusable template parts:

**Partial** (`src/app/Views/partials/user-card.php`):
```php
<div class="user-card">
    <h3>{{ $user['name'] }}</h3>
    <p>{{ $user['email'] }}</p>
</div>
```

**Include in Template**:
```php
@foreach($users as $user)
    @include('partials/user-card')
@endforeach
```

### Flash Messages

Display one-time messages:

```php
// In view
@if(flash('success'))
    <div class="alert alert-success">
        {{ flash('success') }}
    </div>
@endif

@if(flash('error'))
    <div class="alert alert-danger">
        {{ flash('error') }}
    </div>
@endif
```

### Old Input

Repopulate form fields after validation errors:

```php
<form method="POST">
    <input type="text"
           name="name"
           value="{{ old('name') }}"
           placeholder="Your name">

    <input type="email"
           name="email"
           value="{{ old('email') }}"
           placeholder="your@email.com">

    <button type="submit">Submit</button>
</form>
```

---

## 8. Validation

### Basic Validation

Use the `Validator` class to validate input:

```php
use Validator;

$data = $request->all();

$validator = Validator::make($data, [
    'name' => 'required|min:3|max:50',
    'email' => 'required|email|unique:users,email',
    'password' => 'required|min:8|confirmed',
    'age' => 'required|integer|min:18|max:120'
]);

if ($validator->validate()) {
    // Validation passed
    $cleanData = $validator->getData();

    // Process data...
} else {
    // Validation failed
    $errors = $validator->errors();

    // Display errors...
}
```

### Controller Validation

Use the controller's `validate()` helper for automatic error handling:

```php
public function store(Request $request): Response
{
    // Automatically redirects back with errors if validation fails
    $data = $this->validate($request->all(), [
        'name' => 'required|min:3',
        'email' => 'required|email',
        'password' => 'required|min:8|confirmed'
    ]);

    // If we reach here, validation passed
    $user = (new User())->create($data);

    return $this->redirect('/users')
        ->with('success', 'User created!');
}
```

### Available Validation Rules

**Required Fields**:
- `required` - Field must be present and not empty

**String Validation**:
- `min:n` - Minimum length (e.g., `min:3`)
- `max:n` - Maximum length (e.g., `max:50`)
- `alpha` - Only alphabetic characters (a-z, A-Z)
- `alphanumeric` - Only letters and numbers
- `email` - Valid email format
- `url` - Valid URL format

**Numeric Validation**:
- `numeric` - Must be numeric (int or float)
- `integer` - Must be an integer
- `min:n` - Minimum value for numbers
- `max:n` - Maximum value for numbers

**Comparison**:
- `match:field` - Must match another field
- `confirmed` - Must have matching `{field}_confirmation` field
- `in:val1,val2,val3` - Must be one of the listed values

**Advanced**:
- `regex:pattern` - Must match regular expression
- `unique:table,column` - Must be unique in database
- `exists:table,column` - Must exist in database

### Validation Rule Examples

```php
$rules = [
    // Required field
    'name' => 'required',

    // Required with length constraints
    'username' => 'required|min:3|max:20|alphanumeric',

    // Email validation
    'email' => 'required|email|unique:users,email',

    // Password with confirmation
    'password' => 'required|min:8|confirmed',
    // Expects 'password_confirmation' field

    // Integer with range
    'age' => 'required|integer|min:18|max:120',

    // Must match another field
    'email_confirm' => 'required|email|match:email',

    // Must be one of specified values
    'role' => 'required|in:admin,user,moderator',

    // Regex validation
    'phone' => 'required|regex:/^[0-9]{10}$/',

    // Database validation
    'category_id' => 'required|exists:categories,id',
    'slug' => 'required|unique:posts,slug'
];
```

### Custom Error Messages

Override default error messages:

```php
$validator = Validator::make($data, [
    'email' => 'required|email',
    'password' => 'required|min:8'
], [
    'email.required' => 'Please provide your email address',
    'email.email' => 'Please provide a valid email address',
    'password.required' => 'Password is required',
    'password.min' => 'Password must be at least 8 characters'
]);
```

### Displaying Validation Errors

**In Controller** (automatic with `validate()` helper):
```php
$data = $this->validate($request->all(), $rules);
// Automatically flashes errors and old input if validation fails
```

**In View**:
```php
<?php $errors = flash('_errors', []); ?>

@if(!empty($errors))
    <div class="alert alert-danger">
        <ul>
            @foreach($errors as $field => $error)
                <li>{{ $error }}</li>
            @endforeach
        </ul>
    </div>
@endif

<form method="POST">
    <?php echo csrfField(); ?>

    <div>
        <input type="text" name="name" value="{{ old('name') }}">
        @if(isset($errors['name']))
            <span class="error">{{ $errors['name'] }}</span>
        @endif
    </div>

    <div>
        <input type="email" name="email" value="{{ old('email') }}">
        @if(isset($errors['email']))
            <span class="error">{{ $errors['email'] }}</span>
        @endif
    </div>

    <button type="submit">Submit</button>
</form>
```

### Validation Methods

```php
// Create validator
$validator = Validator::make($data, $rules, $messages);

// Run validation
$isValid = $validator->validate();

// Check if passed/failed
if ($validator->passes()) { }
if ($validator->fails()) { }

// Get all errors
$errors = $validator->errors();
// Returns: ['field' => 'error message', ...]

// Get error for specific field
$emailError = $validator->error('email');

// Get validated data
$cleanData = $validator->getData();
```

---

## 9. Security

### CSRF Protection

**Cross-Site Request Forgery** protection is built-in and enabled by default.

**In Forms**:
```php
<form method="POST" action="/submit">
    <?php echo csrfField(); ?>
    <!-- Outputs: <input type="hidden" name="_csrf_token" value="..."> -->

    <!-- Form fields -->
    <button type="submit">Submit</button>
</form>
```

**For AJAX Requests**:
```php
<head>
    <?php echo csrfMeta(); ?>
    <!-- Outputs: <meta name="csrf-token" content="..."> -->
</head>

<script>
// JavaScript
const token = document.querySelector('meta[name="csrf-token"]').content;

fetch('/api/endpoint', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token': token
    },
    body: JSON.stringify(data)
});
</script>
```

**Manual Token Validation**:
```php
$token = $request->input('_csrf_token');

if (Security::validateCsrfToken($token)) {
    // Token is valid
} else {
    // Token is invalid
    abort(403, 'CSRF token validation failed');
}
```

**How It Works**:
- Token generated on session start
- Token stored in session
- Form submissions require valid token
- CSRF middleware validates automatically
- Token regenerated after validation

### XSS Prevention

**Cross-Site Scripting** prevention through automatic output escaping:

**Escaped Output** (Default - Safe):
```php
// In templates
{{ $userInput }}
{{ $post['title'] }}
```

**Helper Functions**:
```php
// HTML escaping
echo e($userInput);
echo escape($userInput);

// JavaScript context
<script>
var name = <?php echo escapeJs($userName); ?>;
</script>

// URL encoding
<a href="?redirect=<?php echo escapeUrl($url); ?>">Link</a>
```

**Security Rules**:
- ✅ ALWAYS escape user input in templates
- ✅ Use `{{ }}` for variables
- ❌ NEVER use `{!! !!}` with user input
- ✅ Validate and sanitize input before storage

### SQL Injection Prevention

**Prepared Statements** are used automatically:

```php
// Model operations are SAFE (use prepared statements)
$user = (new User())->find($id);
$users = (new User())->where('status', $_POST['status']);

// Query builder is SAFE
$users = (new User())
    ->whereCondition('email', '=', $userEmail)
    ->get();

// Custom queries - use parameter binding
$sql = "SELECT * FROM users WHERE email = ? AND status = ?";
$stmt = $this->query($sql, [$email, $status]);

// ❌ NEVER concatenate user input into SQL
$sql = "SELECT * FROM users WHERE id = " . $_GET['id'];  // UNSAFE!

// ✅ ALWAYS use parameter binding
$sql = "SELECT * FROM users WHERE id = ?";
$stmt = $this->query($sql, [$_GET['id']]);  // SAFE
```

### Password Hashing

**Bcrypt** password hashing with configurable cost:

```php
// Hash a password
$password = 'user-password-123';
$hash = Security::hashPassword($password, [
    'algorithm' => PASSWORD_BCRYPT,
    'cost' => 12  // Higher = more secure but slower
]);

// Store $hash in database (NOT the plain password)

// Verify password during login
$inputPassword = $_POST['password'];
$storedHash = $user['password'];  // From database

if (Security::verifyPassword($inputPassword, $storedHash)) {
    // Password is correct - log user in
    Session::set('user_id', $user['id']);

    // Check if hash needs upgrade
    if (Security::needsRehash($storedHash)) {
        $newHash = Security::hashPassword($inputPassword);
        // Update database with $newHash
    }
} else {
    // Password is incorrect
    return back()->with('error', 'Invalid credentials');
}
```

**Best Practices**:
- ✅ NEVER store plain text passwords
- ✅ Use bcrypt (default in ADA)
- ✅ Use cost of 12 or higher
- ✅ Rehash passwords when algorithm improves
- ❌ NEVER decrypt passwords (they're hashed, not encrypted)

### Secure Token Generation

Generate cryptographically secure tokens:

```php
// Generate token (32 bytes = 64 hex characters)
$resetToken = Security::generateToken(32);
// Use for password reset, API keys, etc.

// Generate random string (alphanumeric)
$string = Security::randomString(16);
// Use for verification codes, etc.
```

### Session Security

Sessions are configured securely by default:

```php
// In src/config/app.php
'session' => [
    'lifetime' => 7200,           // 2 hours
    'cookie_httponly' => true,    // No JavaScript access
    'cookie_secure' => true,      // HTTPS only (production)
    'cookie_samesite' => 'Lax',  // CSRF protection
]
```

**Session Methods**:
```php
// Start session (done automatically)
Session::start();

// Set session data
Session::set('user_id', 123);
Session::set('role', 'admin');

// Get session data
$userId = Session::get('user_id');
$role = Session::get('role', 'guest');

// Check if exists
if (Session::has('user_id')) {
    // User is logged in
}

// Flash messages (one-time)
Session::flash('success', 'Action completed!');

// Remove session data
Session::remove('user_id');

// Destroy entire session (logout)
Session::destroy();

// Regenerate session ID (after login)
Session::regenerate();
```

### Input Sanitization

Clean user input before processing:

```php
// Sanitize string
$clean = Security::sanitize($userInput);
// Removes: null bytes, excessive whitespace

// Sanitize array
$cleanData = Security::sanitizeArray($_POST);

// Sanitize with tag stripping
$clean = Security::sanitize($input, stripTags: true);

// Or use helper
$clean = sanitize($userInput);
```

### File Upload Security

Validate uploaded files:

```php
if ($request->hasFile('avatar')) {
    // Validate file
    $validation = $request->validateFile('avatar',
        maxSize: 5 * 1024 * 1024,  // 5MB
        allowedTypes: ['image/jpeg', 'image/png', 'image/gif'],
        allowedExtensions: ['jpg', 'jpeg', 'png', 'gif']
    );

    if ($validation['valid']) {
        // Move file
        $result = $request->moveFile('avatar', __DIR__ . '/uploads');

        if ($result['success']) {
            $filePath = $result['path'];
            // Save path to database
        }
    } else {
        // Validation failed
        $error = $validation['error'];
        return back()->with('error', $error);
    }
}
```

**File Upload Best Practices**:
- ✅ Validate file size
- ✅ Validate MIME type (using fileinfo, not $_FILES['type'])
- ✅ Validate file extension
- ✅ Generate unique filenames
- ✅ Store outside web root if possible
- ❌ NEVER trust user-provided filename
- ❌ NEVER execute uploaded files

### Security Headers

Security headers are configured in `.htaccess`:

```apache
# Already configured in .htaccess
Header always set X-Frame-Options "SAMEORIGIN"
Header always set X-Content-Type-Options "nosniff"
Header always set X-XSS-Protection "1; mode=block"
Header always set Referrer-Policy "strict-origin-when-cross-origin"

# For HTTPS sites
Header always set Strict-Transport-Security "max-age=31536000"
```

### Security Checklist

Before deploying to production:

- ✅ Set `APP_ENV=production` in `.env`
- ✅ Set `APP_DEBUG=false` in `.env`
- ✅ Enable HTTPS
- ✅ Set `SESSION_SECURE=true` for HTTPS
- ✅ Use strong database passwords
- ✅ Restrict file permissions (755/644)
- ✅ Keep `.env` out of version control
- ✅ Enable security headers
- ✅ Validate ALL user input
- ✅ Escape ALL output
- ✅ Use prepared statements
- ✅ Hash passwords with bcrypt
- ✅ Implement rate limiting (if needed)
- ✅ Regular security updates
- ✅ Monitor error logs

---

## 10. Middleware

### What is Middleware?

Middleware provides a mechanism to filter HTTP requests entering your application. Think of it as layers that wrap around your application.

### Built-in Middleware

**1. SessionMiddleware** - Starts secure sessions
**2. CsrfMiddleware** - Validates CSRF tokens
**3. AuthMiddleware** - Checks user authentication

### Creating Middleware

Create a middleware class in `src/middleware/`:

```php
<?php
// src/middleware/AuthMiddleware.php

class AuthMiddleware extends Middleware
{
    /**
     * Handle the request
     *
     * @param Request $request
     * @param callable $next
     * @return Response
     */
    public function handle(Request $request, callable $next): Response
    {
        // Check if user is logged in
        if (!Session::has('user_id')) {
            // User not authenticated - redirect to login
            return Response::redirect('/login')
                ->with('error', 'Please log in to continue');
        }

        // User is authenticated - continue to next middleware/controller
        return $next($request);
    }
}
```

### Middleware Examples

**Admin Middleware**:
```php
class AdminMiddleware extends Middleware
{
    public function handle(Request $request, callable $next): Response
    {
        $userId = Session::get('user_id');

        if (!$userId) {
            return Response::redirect('/login');
        }

        // Get user role
        $user = (new User())->find($userId);

        if (!$user || $user['role'] !== 'admin') {
            abort(403, 'Unauthorized - Admin access required');
        }

        return $next($request);
    }
}
```

**Rate Limiting Middleware**:
```php
class RateLimitMiddleware extends Middleware
{
    public function handle(Request $request, callable $next): Response
    {
        $ip = $request->ip();
        $key = "rate_limit_{$ip}";

        $attempts = (int) Session::get($key, 0);

        if ($attempts >= 100) {
            abort(429, 'Too Many Requests');
        }

        Session::set($key, $attempts + 1);

        return $next($request);
    }
}
```

**Logging Middleware**:
```php
class LoggingMiddleware extends Middleware
{
    public function handle(Request $request, callable $next): Response
    {
        // Log request
        Logger::info("Request: {$request->method()} {$request->uri()}", [
            'ip' => $request->ip(),
            'user_agent' => $request->userAgent()
        ]);

        // Continue processing
        $response = $next($request);

        // Log response
        Logger::info("Response: {$response->getStatus()}");

        return $response;
    }
}
```

### Applying Middleware

**Global Middleware** (applies to ALL routes):
```php
// In index.php or routes.php
$router->setGlobalMiddleware([
    'SessionMiddleware',
    'CsrfMiddleware'
]);
```

**Route-Specific Middleware**:
```php
// Single middleware
$router->get('/dashboard', 'DashboardController@index', [
    'middleware' => ['auth']
]);

// Multiple middleware (executed in order)
$router->get('/admin', 'AdminController@index', [
    'middleware' => ['auth', 'admin', 'verified']
]);
```

**Group Middleware**:
```php
// Apply to all routes in group
$router->group(['middleware' => ['auth']], function($router) {
    $router->get('/profile', 'ProfileController@show');
    $router->get('/settings', 'SettingsController@index');
    $router->post('/logout', 'AuthController@logout');
});

// Combine with prefix
$router->group([
    'prefix' => '/admin',
    'middleware' => ['auth', 'admin']
], function($router) {
    $router->get('/dashboard', 'AdminController@dashboard');
    $router->get('/users', 'AdminController@users');
});
```

### Middleware Execution Order

Middleware executes in the order specified:

```php
// Execution flow:
// 1. SessionMiddleware runs first
// 2. CsrfMiddleware runs second
// 3. AuthMiddleware runs third
// 4. Controller action executes
// 5. Response returns through middleware (in reverse)

$router->get('/dashboard', 'DashboardController@index', [
    'middleware' => ['session', 'csrf', 'auth']
]);
```

### Middleware Parameters

Pass parameters to middleware:

```php
class RoleMiddleware extends Middleware
{
    protected string $requiredRole;

    public function __construct(string $role = 'user')
    {
        $this->requiredRole = $role;
    }

    public function handle(Request $request, callable $next): Response
    {
        $user = (new User())->find(Session::get('user_id'));

        if ($user['role'] !== $this->requiredRole) {
            abort(403, 'Insufficient permissions');
        }

        return $next($request);
    }
}
```

### Terminating Middleware

Stop request processing in middleware:

```php
class MaintenanceModeMiddleware extends Middleware
{
    public function handle(Request $request, callable $next): Response
    {
        if (Config::get('app.maintenance.enabled')) {
            // Don't call $next() - terminate here
            return Response::view('errors/maintenance', [], 503);
        }

        return $next($request);
    }
}
```

---

## 11. Request & Response

### Request Object

The `Request` object provides access to all HTTP request data:

**Creating Request**:
```php
// Automatically captured in controllers
public function store(Request $request): Response
{
    // $request is automatically provided
}

// Manual creation (rare)
$request = Request::capture();
```

**HTTP Method**:
```php
$method = $request->method();  // GET, POST, PUT, DELETE, etc.

// Check specific method
if ($request->isPost()) { }
if ($request->isGet()) { }
if ($request->isPut()) { }
if ($request->isDelete()) { }
if ($request->isAjax()) { }
```

**Accessing Input**:
```php
// GET parameter
$value = $request->get('key', 'default');

// POST parameter
$value = $request->post('key', 'default');

// GET or POST (POST takes precedence)
$value = $request->input('key', 'default');

// All input (GET + POST merged)
$all = $request->all();
// Returns: ['name' => 'John', 'email' => 'john@example.com', ...]

// Specific fields only
$data = $request->only(['name', 'email', 'phone']);
// Returns: ['name' => '...', 'email' => '...', 'phone' => '...']

// All except specific fields
$data = $request->except(['password', 'token']);

// Check if input exists
if ($request->has('email')) { }
```

**Request Information**:
```php
// URI
$uri = $request->uri();  // /users/123

// Full URL
$url = $request->url();  // http://example.com/users/123

// Client IP
$ip = $request->ip();

// User Agent
$userAgent = $request->userAgent();

// Headers
$contentType = $request->header('Content-Type');
$token = $request->header('Authorization');
```

**Route Parameters**:
```php
// Route: /user/{id}/post/{postId}
$userId = $request->routeParam('id');
$postId = $request->routeParam('postId');

// All route parameters
$params = $request->routeParams();
// Returns: ['id' => '123', 'postId' => '456']
```

**File Uploads**:
```php
// Check if file uploaded
if ($request->hasFile('avatar')) {
    // Get file info
    $file = $request->file('avatar');
    // Returns: ['name' => '...', 'type' => '...', 'size' => ..., ...]

    // Validate file
    $validation = $request->validateFile('avatar',
        maxSize: 5 * 1024 * 1024,  // 5MB in bytes
        allowedTypes: ['image/jpeg', 'image/png'],
        allowedExtensions: ['jpg', 'jpeg', 'png']
    );

    if ($validation['valid']) {
        // Move file
        $result = $request->moveFile('avatar', '/uploads', 'newname.jpg');

        if ($result['success']) {
            $path = $result['path'];  // /uploads/newname.jpg
        } else {
            $error = $result['error'];
        }
    } else {
        $error = $validation['error'];
        // Possible errors: 'No file uploaded', 'File too large',
        // 'Invalid file type', 'Invalid file extension'
    }
}
```

### Response Object

The `Response` object handles HTTP responses:

**Basic Response**:
```php
// Plain text
$response = new Response('Hello World');

// With status code
$response = new Response('Not Found', 404);

// With headers
$response = new Response('OK', 200, [
    'Content-Type' => 'text/plain',
    'X-Custom' => 'value'
]);
```

**View Response**:
```php
// Render view
return Response::view('home/index', [
    'title' => 'Home',
    'posts' => $posts
]);

// With custom status
return Response::view('errors/404', [], 404);
```

**JSON Response**:
```php
// Success response
return Response::json([
    'success' => true,
    'data' => $users,
    'message' => 'Users retrieved successfully'
]);

// Error response
return Response::json([
    'success' => false,
    'error' => 'User not found'
], 404);

// With custom status
return Response::json($data, 201);  // Created
```

**Redirect Response**:
```php
// Redirect to URL
return Response::redirect('/dashboard');

// Redirect with status code
return Response::redirect('/login', 301);  // Permanent redirect

// Redirect back to previous page
return Response::back();
```

**File Download**:
```php
// Download file
return Response::download('/path/to/invoice.pdf', 'Invoice-2025.pdf');

// Browser tries to download as 'Invoice-2025.pdf'
```

**File Display**:
```php
// Display file inline (e.g., PDF viewer, image)
return Response::file('/path/to/document.pdf', 'application/pdf');

// Auto-detect MIME type
return Response::file('/path/to/image.jpg');
```

**Special Responses**:
```php
// No Content (204) - successful but no response body
return Response::noContent();

// Created (201) - resource created successfully
return Response::created(['id' => 123], '/api/users/123');
```

**Fluent Methods** (chainable):
```php
// Flash messages
return Response::redirect('/dashboard')
    ->with('success', 'Login successful')
    ->with('username', $user['name']);

// Flash validation errors
return Response::back()
    ->withErrors($validator->errors())
    ->withInput($request->all());

// Set headers
return Response::json($data)
    ->withHeaders([
        'X-API-Version' => '1.0',
        'X-RateLimit-Remaining' => '99'
    ]);

// Set cookie
return Response::redirect('/dashboard')
    ->withCookie('remember_token', $token, time() + 86400);

// Complex example
return Response::redirect('/profile')
    ->with('message', 'Profile updated!')
    ->withCookie('last_update', time(), time() + 3600)
    ->withHeaders(['X-Custom' => 'value']);
```

**Response Methods**:
```php
// Set status code
$response->setStatus(404);

// Set header
$response->setHeader('Content-Type', 'application/json');

// Set content
$response->setContent('Response body');

// Get values
$status = $response->getStatus();
$header = $response->getHeader('Content-Type');
$content = $response->getContent();

// Send response (done automatically)
$response->send();
```

---

## 12. Configuration & Environment

### Environment Variables

Environment variables are stored in the `.env` file (root directory):

**Loading .env File**:
```php
// Done automatically in index.php
Env::load(__DIR__ . '/.env');
```

**.env File Format**:
```ini
# Application
APP_NAME="My Application"
APP_ENV=production
APP_DEBUG=false
APP_URL=https://example.com

# Database
DB_HOST=localhost
DB_NAME=myapp
DB_USER=myapp_user
DB_PASS=secure_password

# Session
SESSION_SECURE=true
SESSION_LIFETIME=7200

# Logging
LOG_LEVEL=error

# Features
FEATURE_REGISTRATION=true
FEATURE_COMMENTS=false
```

**Accessing Environment Variables**:
```php
// Using Env class
$appEnv = Env::get('APP_ENV', 'production');
$dbHost = Env::get('DB_HOST', 'localhost');

// Check if exists
if (Env::has('FEATURE_REGISTRATION')) {
    // Feature flag exists
}

// Set at runtime (rare)
Env::set('CUSTOM_VAR', 'value');

// Using helper function
$appName = env('APP_NAME', 'ADA Framework');
$debugMode = env('APP_DEBUG', false);
```

**Type Conversion**:
```ini
# .env
APP_DEBUG=true
FEATURE_ENABLED=false
API_TIMEOUT=30
```

```php
// Automatically converted
$debug = env('APP_DEBUG');  // true (boolean, not string)
$enabled = env('FEATURE_ENABLED');  // false (boolean)
$timeout = env('API_TIMEOUT');  // "30" (string - convert manually if needed)
```

### Configuration Files

Configuration files are stored in `src/config/`:

**Application Config** (`src/config/app.php`):
```php
return [
    'name' => env('APP_NAME', 'ADA Framework'),
    'env' => env('APP_ENV', 'development'),
    'debug' => env('APP_DEBUG', true),
    'url' => env('APP_URL', 'http://localhost'),
    'timezone' => env('APP_TIMEZONE', 'UTC'),

    'log' => [
        'path' => __DIR__ . '/../logs/app.log',
        'level' => env('LOG_LEVEL', 'info'),
    ],

    'session' => [
        'lifetime' => 7200,
        'cookie_httponly' => true,
        'cookie_secure' => env('SESSION_SECURE', false),
    ],
];
```

**Database Config** (`src/config/database.php`):
```php
return [
    'driver' => 'mysql',
    'host' => env('DB_HOST', 'localhost'),
    'database' => env('DB_NAME', 'ada'),
    'username' => env('DB_USER', 'root'),
    'password' => env('DB_PASS', ''),
    'charset' => 'utf8mb4',
    'collation' => 'utf8mb4_unicode_ci',
];
```

**Accessing Configuration**:
```php
// Load config file
Config::load('app');

// Get value with dot notation
$appName = Config::get('app.name');
$dbHost = Config::get('database.host', 'localhost');
$logLevel = Config::get('app.log.level', 'info');

// Check if exists
if (Config::has('app.debug')) {
    // Config key exists
}

// Get all from file
$allAppConfig = Config::all('app');

// Set at runtime
Config::set('app.custom.setting', 'value');

// Using helper function
$appName = config('app.name');
$debugMode = config('app.debug', false);
```

**Nested Configuration Access**:
```php
// Config file structure:
// app.php returns:
// [
//     'log' => [
//         'path' => '/logs/app.log',
//         'level' => 'info',
//         'max_files' => 30
//     ]
// ]

// Access nested values
$logPath = config('app.log.path');
$logLevel = config('app.log.level');
$maxFiles = config('app.log.max_files');
```

### Custom Configuration Files

Create custom configuration files:

**Create File** (`src/config/services.php`):
```php
<?php

return [
    'stripe' => [
        'key' => env('STRIPE_KEY'),
        'secret' => env('STRIPE_SECRET'),
    ],

    'mail' => [
        'driver' => env('MAIL_DRIVER', 'smtp'),
        'host' => env('MAIL_HOST', 'smtp.mailtrap.io'),
        'port' => env('MAIL_PORT', 2525),
        'from' => [
            'address' => env('MAIL_FROM_ADDRESS', 'noreply@example.com'),
            'name' => env('MAIL_FROM_NAME', 'ADA App'),
        ],
    ],
];
```

**Access Configuration**:
```php
// Load (done once)
Config::load('services');

// Access
$stripeKey = config('services.stripe.key');
$mailHost = config('services.mail.host');
$fromAddress = config('services.mail.from.address');
```

### Configuration Best Practices

**Security**:
- ✅ Never commit `.env` to version control
- ✅ Use `.env.example` as template
- ✅ Set restrictive permissions: `chmod 600 .env`
- ✅ Keep secrets in `.env`, not in config files
- ❌ Never expose `.env` through web server

**Organization**:
- Group related settings in config files
- Use environment variables for secrets and environment-specific settings
- Use config files for application structure and defaults
- Document all config options

**Example .gitignore**:
```
.env
/logs/*.log
/cache/*
!/cache/.gitkeep
```

---

## 13. Logging

### PSR-3 Compatible Logging

ADA includes a PSR-3 compatible logging system with 8 severity levels:

**Log Levels** (from most to least severe):
1. `emergency` - System is unusable
2. `alert` - Action must be taken immediately
3. `critical` - Critical conditions
4. `error` - Runtime errors
5. `warning` - Exceptional occurrences that are not errors
6. `notice` - Normal but significant events
7. `info` - Interesting events
8. `debug` - Detailed debug information

### Initializing Logger

```php
// In index.php or bootstrap file
Logger::init('/path/to/logs/app.log', Logger::INFO);

// Or use config
$logPath = config('app.log.path');
$logLevel = config('app.log.level');
Logger::init($logPath, $logLevel);
```

### Logging Messages

**Basic Logging**:
```php
// Emergency - system unusable
Logger::emergency("Database server is down");

// Alert - immediate action required
Logger::alert("Website is down - no response from server");

// Critical - critical conditions
Logger::critical("Application component unavailable");

// Error - runtime errors
Logger::error("Failed to process payment");

// Warning - exceptional but not error
Logger::warning("Disk space running low");

// Notice - normal but significant
Logger::notice("User account created");

// Info - informational messages
Logger::info("User logged in successfully");

// Debug - detailed debug information
Logger::debug("Processing request data", ['request_id' => 123]);
```

**Generic Log Method**:
```php
Logger::log('info', $message, $context);
Logger::log('error', $message, $context);
```

### Context Data

Add additional data to log entries:

```php
// Simple context
Logger::info("User logged in", [
    'user_id' => 123,
    'ip' => '192.168.1.1',
    'user_agent' => 'Mozilla/5.0...'
]);

// Complex context
Logger::error("Payment failed", [
    'user_id' => 456,
    'amount' => 99.99,
    'currency' => 'USD',
    'error_code' => 'CARD_DECLINED',
    'transaction_id' => 'txn_abc123'
]);

// Exception logging
try {
    // Code that might fail
} catch (Exception $e) {
    Logger::error("Database query failed", [
        'exception' => $e,  // Full exception with stack trace
        'query' => $sql,
        'params' => $params
    ]);
}
```

### Message Interpolation

Use placeholders in messages:

```php
// Placeholders replaced with context values
Logger::info("User {username} logged in from {ip}", [
    'username' => 'john_doe',
    'ip' => '192.168.1.1'
]);

// Output: "User john_doe logged in from 192.168.1.1"

Logger::warning("Failed login attempt for {email} from {ip}", [
    'email' => 'admin@example.com',
    'ip' => '203.0.113.1'
]);
```

### Log File Format

Logs are written in a standardized format:

```
[2025-10-29 14:30:45] INFO: User logged in {"user_id":123,"ip":"192.168.1.1"}
[2025-10-29 14:31:10] ERROR: Payment failed {"amount":99.99,"error":"CARD_DECLINED"}
[2025-10-29 14:32:00] WARNING: Disk space low {"available":"2GB","threshold":"5GB"}
```

### Daily Log Rotation

Logs automatically rotate daily:

```
logs/
├── app-2025-10-27.log
├── app-2025-10-28.log
├── app-2025-10-29.log  (today)
└── app-2025-10-30.log
```

**Cleanup Old Logs**:
```php
// Delete logs older than 30 days
$deleted = Logger::cleanOldLogs(30);
Logger::info("Cleaned up {$deleted} old log files");
```

### Log Levels and Filtering

Only messages at or above the configured level are logged:

```php
// Set log level to WARNING
Logger::init($path, Logger::WARNING);

// These will be logged:
Logger::emergency("...");  // ✓ Logged
Logger::alert("...");      // ✓ Logged
Logger::critical("...");   // ✓ Logged
Logger::error("...");      // ✓ Logged
Logger::warning("...");    // ✓ Logged

// These will be ignored:
Logger::notice("...");     // ✗ Not logged
Logger::info("...");       // ✗ Not logged
Logger::debug("...");      // ✗ Not logged
```

**Recommended Levels**:
- **Production**: `error` or `warning`
- **Staging**: `info`
- **Development**: `debug`

### Using Logger Helper

```php
// Helper function for quick logging
logger('info', 'User logged in', ['user_id' => 123]);
logger('error', 'Something went wrong', ['error' => $e->getMessage()]);
```

### Integration Points

Logger is automatically integrated into:

**Error Handler**:
```php
// All errors and exceptions are logged
Logger::error("Uncaught exception: {$e->getMessage()}", [
    'exception' => $e
]);
```

**Database**:
```php
// Database connection failures
Logger::critical("Database connection failed", [
    'host' => $config['host'],
    'exception' => $e
]);
```

**Custom Integration**:
```php
// In your application code
public function createUser($data)
{
    try {
        $userId = (new User())->create($data);
        Logger::info("User created", ['user_id' => $userId]);
        return $userId;
    } catch (Exception $e) {
        Logger::error("Failed to create user", [
            'exception' => $e,
            'data' => $data
        ]);
        throw $e;
    }
}
```

### Best Practices

**What to Log**:
- ✅ Authentication events (login, logout, failed attempts)
- ✅ Authorization failures (access denied)
- ✅ Application errors and exceptions
- ✅ Critical business operations
- ✅ External API calls
- ✅ Database connection issues
- ✅ Performance bottlenecks

**What NOT to Log**:
- ❌ Passwords (plain or hashed)
- ❌ Credit card numbers
- ❌ Social security numbers
- ❌ API keys or secrets
- ❌ Personal identifiable information (in production)

**Log Message Tips**:
- Be descriptive and actionable
- Include relevant context
- Use consistent terminology
- Don't log in loops (causes huge files)
- Use appropriate log levels

---

## 14. Helper Functions

ADA includes 30+ global helper functions for common tasks:

### View & Response Helpers

**view()** - Render a view:
```php
return view('home/index', ['title' => 'Home']);
```

**json()** - JSON response:
```php
return json(['success' => true, 'data' => $users]);
return json(['error' => 'Not found'], 404);
```

**abort()** - Abort with HTTP error:
```php
abort(404);
abort(403, 'Unauthorized access');
abort(500, 'Internal server error');
```

### Escaping Helpers

**e() / escape()** - Escape HTML:
```php
echo e($userInput);
echo e('<script>alert("xss")</script>');
// Output: &lt;script&gt;alert(&quot;xss&quot;)&lt;/script&gt;
```

**escapeJs()** - Escape for JavaScript:
```php
<script>
var name = <?php echo escapeJs($userName); ?>;
</script>
```

**escapeUrl()** - URL encoding:
```php
$url = 'redirect=' . escapeUrl($returnUrl);
```

### CSRF Helpers

**csrfField()** - Hidden input field:
```php
<form method="POST">
    <?php echo csrfField(); ?>
    <!-- Outputs: <input type="hidden" name="_csrf_token" value="..."> -->
</form>
```

**csrfToken()** - Get token value:
```php
$token = csrfToken();
```

**csrfMeta()** - Meta tag for AJAX:
```php
<head>
    <?php echo csrfMeta(); ?>
    <!-- Outputs: <meta name="csrf-token" content="..."> -->
</head>
```

### Form Helpers

**old()** - Old input value:
```php
<input type="text"
       name="email"
       value="<?php echo old('email'); ?>">
```

### URL Helpers

**url()** - Generate URL:
```php
$profileUrl = url('/user/profile');
// Output: http://example.com/user/profile

$homeUrl = url('/');
// Output: http://example.com/
```

**asset()** - Asset URL:
```php
<img src="<?php echo asset('images/logo.png'); ?>">
// Output: <img src="http://example.com/images/logo.png">

<link rel="stylesheet" href="<?php echo asset('css/style.css'); ?>">
```

**route()** - Named route URL:
```php
$url = route('user.profile', ['id' => 123]);
// Output: /user/123

<a href="<?php echo route('posts.show', ['id' => $post['id']]); ?>">
    Read More
</a>
```

### Redirect Helpers

**redirect()** - Redirect to URL:
```php
redirect('/dashboard');
redirect('/login', 301);  // Permanent redirect
```

**back()** - Redirect back:
```php
back();  // Goes to previous page
```

### Configuration Helpers

**config()** - Get config value:
```php
$appName = config('app.name');
$dbHost = config('database.host', 'localhost');
$logLevel = config('app.log.level');
```

**env()** - Get environment variable:
```php
$appEnv = env('APP_ENV', 'production');
$dbPassword = env('DB_PASS');
$debugMode = env('APP_DEBUG', false);
```

### Session Helpers

**session()** - Get session value:
```php
$userId = session('user_id');
$role = session('role', 'guest');

// Get all session data
$allSession = session();
```

**flash()** - Get flash message:
```php
$successMessage = flash('success');
$errorMessage = flash('error');

// In templates
@if(flash('success'))
    <div class="alert">{{ flash('success') }}</div>
@endif
```

### Logging Helper

**logger()** - Log message:
```php
logger('info', 'User logged in', ['user_id' => 123]);
logger('error', 'Payment failed', ['amount' => 99.99]);
logger('debug', 'Processing data', ['step' => 3]);
```

### Request Helpers

**isPost()** - Check if POST request:
```php
if (isPost()) {
    // Handle form submission
}
```

**isGet()** - Check if GET request:
```php
if (isGet()) {
    // Display form
}
```

**isAjax()** - Check if AJAX request:
```php
if (isAjax()) {
    return json(['data' => $data]);
} else {
    return view('page', ['data' => $data]);
}
```

**getClientIp()** - Get client IP:
```php
$ip = getClientIp();
Logger::info("Request from {$ip}");
```

### Security Helper

**sanitize()** - Sanitize string:
```php
$clean = sanitize($userInput);
// Removes null bytes, trims whitespace
```

### Debug Helper

**dd()** - Dump and die:
```php
dd($variable);
dd($user, $posts, $comments);  // Multiple variables

// Outputs formatted var_dump and stops execution
```

### Helper Usage Examples

**Complete Form Example**:
```php
<form method="POST" action="<?php echo url('/contact'); ?>">
    <?php echo csrfField(); ?>

    <input type="text"
           name="name"
           value="<?php echo old('name'); ?>"
           placeholder="Your name">

    <input type="email"
           name="email"
           value="<?php echo old('email'); ?>"
           placeholder="your@email.com">

    <button type="submit">Submit</button>
</form>

<?php if (flash('success')): ?>
    <div class="alert alert-success">
        <?php echo e(flash('success')); ?>
    </div>
<?php endif; ?>
```

**Controller with Helpers**:
```php
public function store(Request $request): Response
{
    $data = $this->validate($request->all(), $rules);

    $userId = (new User())->create([
        'name' => sanitize($data['name']),
        'email' => sanitize($data['email']),
        'password' => Security::hashPassword($data['password'])
    ]);

    logger('info', 'User registered', ['user_id' => $userId]);

    return redirect(route('user.profile', ['id' => $userId]))
        ->with('success', 'Registration successful!');
}
```

---

## 15. Error Handling

### Global Error Handler

ADA includes a comprehensive error handling system that catches all errors and exceptions:

**Features**:
- Catches all PHP errors (warnings, notices, fatal errors)
- Catches uncaught exceptions
- Handles fatal errors via shutdown handler
- Logs all errors automatically
- Beautiful error pages
- Different behavior for development vs production

### Error Pages

**404 Not Found** (`src/app/Views/errors/404.php`):
- Displayed when route doesn't exist
- Customizable template

**500 Internal Server Error** (`src/app/Views/errors/500.php`):
- Displayed for uncaught exceptions
- Shows stack trace in development mode
- User-friendly message in production

**403 Forbidden** (`src/app/Views/errors/403.php`):
- Displayed for authorization failures
- Customizable message

### Development vs Production

**Development Mode** (`APP_DEBUG=true`):
```php
// .env
APP_ENV=development
APP_DEBUG=true
```

Shows:
- Full error messages
- Stack traces
- File paths and line numbers
- Variable dumps
- Helpful debugging information

**Production Mode** (`APP_DEBUG=false`):
```php
// .env
APP_ENV=production
APP_DEBUG=false
```

Shows:
- Generic error messages
- No stack traces
- No file paths
- User-friendly error pages
- Errors logged, not displayed

### Error Controller

The `ErrorController` handles error pages:

```php
class ErrorController extends Controller
{
    /**
     * 404 Not Found
     */
    public function error404(Request $request): Response
    {
        return $this->view('errors/404', [
            'uri' => $request->uri()
        ])->setStatus(404);
    }

    /**
     * 500 Internal Server Error
     */
    public function error500(Request $request, Throwable $exception): Response
    {
        $showDetails = config('app.debug', false);

        return $this->view('errors/500', [
            'exception' => $exception,
            'showDetails' => $showDetails
        ])->setStatus(500);
    }

    /**
     * 403 Forbidden
     */
    public function error403(Request $request, string $reason = ''): Response
    {
        return $this->view('errors/403', [
            'reason' => $reason
        ])->setStatus(403);
    }
}
```

### Custom Error Pages

Create custom error pages in `src/app/Views/errors/`:

**404.php Example**:
```php
@extends('layouts/main')

@section('title', '404 - Page Not Found')

@section('content')
    <div class="error-page">
        <h1>404</h1>
        <h2>Page Not Found</h2>
        <p>The page "<?php echo e($uri); ?>" could not be found.</p>
        <a href="<?php echo url('/'); ?>" class="btn">Go Home</a>
    </div>
@endsection
```

**500.php Example**:
```php
@extends('layouts/main')

@section('title', '500 - Internal Server Error')

@section('content')
    <div class="error-page">
        <h1>500</h1>
        <h2>Internal Server Error</h2>

        @if($showDetails)
            <div class="error-details">
                <h3><?php echo e(get_class($exception)); ?></h3>
                <p><?php echo e($exception->getMessage()); ?></p>
                <p>File: <?php echo e($exception->getFile()); ?>:<?php echo $exception->getLine(); ?></p>
                <pre><?php echo e($exception->getTraceAsString()); ?></pre>
            </div>
        @else
            <p>Something went wrong. Please try again later.</p>
        @endif
    </div>
@endsection
```

### Throwing Errors

**HTTP Errors**:
```php
// 404 Not Found
abort(404);
abort(404, 'Page not found');

// 403 Forbidden
abort(403);
abort(403, 'You do not have permission to access this resource');

// 500 Internal Server Error
abort(500);
abort(500, 'Database connection failed');
```

**Custom Exceptions**:
```php
// Throw exception
throw new Exception("Something went wrong");

// With code
throw new Exception("User not found", 404);

// ValidationException (automatically handled)
throw new ValidationException($validator->errors(), $request);
```

### Error Logging

All errors are automatically logged:

```php
// In src/logs/error.log or src/logs/app.log

[2025-10-29 14:30:45] [ERROR] Database connection failed in /path/to/file.php:123
Stack trace:
#0 /path/to/file.php(123): Database->connect()
#1 /path/to/file.php(456): Model->__construct()
...
```

**Manual Error Logging**:
```php
try {
    // Risky code
    $result = performOperation();
} catch (Exception $e) {
    // Log error
    Logger::error("Operation failed: {$e->getMessage()}", [
        'exception' => $e,
        'user_id' => Session::get('user_id')
    ]);

    // Show user-friendly message
    return back()->with('error', 'Operation failed. Please try again.');
}
```

### Handling Specific Exceptions

**Validation Exceptions**:
```php
// Automatically caught by error handler
// Redirects back with errors and old input
throw new ValidationException($errors, $request);
```

**Database Exceptions**:
```php
try {
    $user = (new User())->find($id);
} catch (PDOException $e) {
    Logger::error("Database error", ['exception' => $e]);
    abort(500, 'Database error occurred');
}
```

**Custom Exception Handling**:
```php
class PaymentException extends Exception {}

try {
    processPayment($amount);
} catch (PaymentException $e) {
    Logger::error("Payment failed", [
        'exception' => $e,
        'amount' => $amount
    ]);

    return back()
        ->with('error', 'Payment failed: ' . $e->getMessage())
        ->withInput();
}
```

### Error Handler Configuration

Configure error handling in `src/core/ErrorHandler.php`:

```php
// Initialize error handler
ErrorHandler::register(
    developmentMode: config('app.debug', false),
    logFile: config('app.log.path', __DIR__ . '/../logs/error.log')
);
```

### Best Practices

**Error Handling**:
- ✅ Always use try-catch for risky operations
- ✅ Log all errors with context
- ✅ Show user-friendly messages to users
- ✅ Show detailed errors only in development
- ❌ Never expose sensitive information in errors
- ❌ Don't catch exceptions without handling them

**Error Messages**:
- ✅ Be descriptive for developers (in logs)
- ✅ Be friendly for users (in UI)
- ✅ Include context (user ID, operation, etc.)
- ❌ Don't expose stack traces to users in production
- ❌ Don't include passwords or secrets in logs

---

## 16. Complete Examples

### Example 1: Blog Application

Complete CRUD application for a blog with posts and comments.

**Database Schema**:
```sql
CREATE TABLE posts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    slug VARCHAR(200) NOT NULL UNIQUE,
    body TEXT NOT NULL,
    author_id INT NOT NULL,
    status ENUM('draft', 'published') DEFAULT 'draft',
    created_at TIMESTAMP NULL,
    updated_at TIMESTAMP NULL
);

CREATE TABLE comments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    post_id INT NOT NULL,
    author_name VARCHAR(100) NOT NULL,
    author_email VARCHAR(100) NOT NULL,
    body TEXT NOT NULL,
    created_at TIMESTAMP NULL,
    FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE
);
```

**Post Model** (`src/app/Models/Post.php`):
```php
<?php

class Post extends Model
{
    protected string $table = 'posts';
    protected array $fillable = ['title', 'slug', 'body', 'author_id', 'status'];
    protected bool $timestamps = true;

    /**
     * Get published posts
     */
    public function getPublished()
    {
        return $this->whereCondition('status', '=', 'published')
                    ->orderBy('created_at', 'DESC')
                    ->get();
    }

    /**
     * Get post by slug
     */
    public function findBySlug(string $slug)
    {
        return $this->findBy('slug', $slug);
    }
}
```

**Comment Model** (`src/app/Models/Comment.php`):
```php
<?php

class Comment extends Model
{
    protected string $table = 'comments';
    protected array $fillable = ['post_id', 'author_name', 'author_email', 'body'];
    protected bool $timestamps = true;

    /**
     * Get comments for a post
     */
    public function getByPost(int $postId)
    {
        return $this->whereCondition('post_id', '=', $postId)
                    ->orderBy('created_at', 'ASC')
                    ->get();
    }
}
```

**Post Controller** (`src/app/Controllers/PostController.php`):
```php
<?php

class PostController extends Controller
{
    /**
     * Display list of posts
     */
    public function index(Request $request): Response
    {
        $post = new Post();
        $posts = $post->getPublished();

        return $this->view('posts/index', [
            'posts' => $posts
        ]);
    }

    /**
     * Show single post
     */
    public function show(Request $request): Response
    {
        $slug = $request->routeParam('slug');

        $post = (new Post())->findBySlug($slug);

        if (!$post || $post['status'] !== 'published') {
            abort(404, 'Post not found');
        }

        $comments = (new Comment())->getByPost($post['id']);

        return $this->view('posts/show', [
            'post' => $post,
            'comments' => $comments
        ]);
    }

    /**
     * Show create form
     */
    public function create(Request $request): Response
    {
        return $this->view('posts/create');
    }

    /**
     * Store new post
     */
    public function store(Request $request): Response
    {
        $data = $this->validate($request->all(), [
            'title' => 'required|min:5|max:200',
            'slug' => 'required|alphanumeric|unique:posts,slug',
            'body' => 'required|min:50',
            'status' => 'required|in:draft,published'
        ]);

        $data['author_id'] = Session::get('user_id');

        $postId = (new Post())->create($data);

        Logger::info("Post created", ['post_id' => $postId, 'title' => $data['title']]);

        return $this->redirect('/posts')
            ->with('success', 'Post created successfully!');
    }

    /**
     * Add comment to post
     */
    public function addComment(Request $request): Response
    {
        $postId = $request->routeParam('id');

        $data = $this->validate($request->all(), [
            'author_name' => 'required|min:2|max:100',
            'author_email' => 'required|email',
            'body' => 'required|min:10|max:1000'
        ]);

        $data['post_id'] = $postId;

        (new Comment())->create($data);

        return $this->redirect("/posts/{$postId}")
            ->with('success', 'Comment added!');
    }
}
```

**Routes** (`src/config/routes.php`):
```php
// Blog routes
$router->get('/posts', 'PostController@index', ['name' => 'posts.index']);
$router->get('/posts/create', 'PostController@create', [
    'name' => 'posts.create',
    'middleware' => ['auth']
]);
$router->post('/posts', 'PostController@store', [
    'name' => 'posts.store',
    'middleware' => ['auth', 'csrf']
]);
$router->get('/posts/{slug}', 'PostController@show', ['name' => 'posts.show']);
$router->post('/posts/{id}/comments', 'PostController@addComment', [
    'name' => 'posts.comments',
    'middleware' => ['csrf']
]);
```

**Post Index View** (`src/app/Views/posts/index.php`):
```php
@extends('layouts/main')

@section('title', 'Blog Posts')

@section('content')
    <h1>Blog Posts</h1>

    @if(Session::has('user_id'))
        <p>
            <a href="<?php echo route('posts.create'); ?>" class="btn">
                Create New Post
            </a>
        </p>
    @endif

    @if(flash('success'))
        <div class="alert alert-success">{{ flash('success') }}</div>
    @endif

    @if(empty($posts))
        <p>No posts yet.</p>
    @else
        @foreach($posts as $post)
            <article class="post">
                <h2>
                    <a href="<?php echo route('posts.show', ['slug' => $post['slug']]); ?>">
                        {{ $post['title'] }}
                    </a>
                </h2>
                <p class="meta">
                    Published on {{ date('F j, Y', strtotime($post['created_at'])) }}
                </p>
                <p>{{ substr($post['body'], 0, 200) }}...</p>
                <a href="<?php echo route('posts.show', ['slug' => $post['slug']]); ?>">
                    Read more →
                </a>
            </article>
        @endforeach
    @endif
@endsection
```

**Post Show View** (`src/app/Views/posts/show.php`):
```php
@extends('layouts/main')

@section('title', $post['title'])

@section('content')
    <article class="post-full">
        <h1>{{ $post['title'] }}</h1>
        <p class="meta">
            Published on {{ date('F j, Y', strtotime($post['created_at'])) }}
        </p>
        <div class="post-body">
            {!! nl2br(e($post['body'])) !!}
        </div>
    </article>

    <section class="comments">
        <h2>Comments ({{ count($comments) }})</h2>

        @if(flash('success'))
            <div class="alert alert-success">{{ flash('success') }}</div>
        @endif

        @foreach($comments as $comment)
            <div class="comment">
                <p class="author">{{ $comment['author_name'] }}</p>
                <p class="date">{{ date('F j, Y g:ia', strtotime($comment['created_at'])) }}</p>
                <p>{{ $comment['body'] }}</p>
            </div>
        @endforeach

        <h3>Add a Comment</h3>
        <form method="POST" action="<?php echo route('posts.comments', ['id' => $post['id']]); ?>">
            <?php echo csrfField(); ?>

            <div class="form-group">
                <label>Name</label>
                <input type="text" name="author_name" value="{{ old('author_name') }}" required>
                <?php if ($errors = flash('_errors')): ?>
                    <?php if (isset($errors['author_name'])): ?>
                        <span class="error">{{ $errors['author_name'] }}</span>
                    <?php endif; ?>
                <?php endif; ?>
            </div>

            <div class="form-group">
                <label>Email</label>
                <input type="email" name="author_email" value="{{ old('author_email') }}" required>
                <?php if ($errors = flash('_errors')): ?>
                    <?php if (isset($errors['author_email'])): ?>
                        <span class="error">{{ $errors['author_email'] }}</span>
                    <?php endif; ?>
                <?php endif; ?>
            </div>

            <div class="form-group">
                <label>Comment</label>
                <textarea name="body" rows="5" required>{{ old('body') }}</textarea>
                <?php if ($errors = flash('_errors')): ?>
                    <?php if (isset($errors['body'])): ?>
                        <span class="error">{{ $errors['body'] }}</span>
                    <?php endif; ?>
                <?php endif; ?>
            </div>

            <button type="submit" class="btn">Post Comment</button>
        </form>
    </section>
@endsection
```

### Example 2: User Authentication System

Complete authentication system with registration, login, and logout.

**User Model** (`src/app/Models/User.php`):
```php
<?php

class User extends Model
{
    protected string $table = 'users';
    protected array $fillable = ['name', 'email', 'password', 'role'];
    protected bool $timestamps = true;

    /**
     * Create user with hashed password
     */
    public function createUser(array $data): int
    {
        $data['password'] = Security::hashPassword($data['password']);
        return $this->create($data);
    }

    /**
     * Find user by email
     */
    public function findByEmail(string $email): ?array
    {
        return $this->findBy('email', $email);
    }

    /**
     * Verify user credentials
     */
    public function verifyCredentials(string $email, string $password): ?array
    {
        $user = $this->findByEmail($email);

        if (!$user) {
            return null;
        }

        if (!Security::verifyPassword($password, $user['password'])) {
            return null;
        }

        // Check if password needs rehashing
        if (Security::needsRehash($user['password'])) {
            $newHash = Security::hashPassword($password);
            $this->update($user['id'], ['password' => $newHash]);
        }

        return $user;
    }
}
```

**Auth Controller** (`src/app/Controllers/AuthController.php`):
```php
<?php

class AuthController extends Controller
{
    /**
     * Show registration form
     */
    public function showRegister(Request $request): Response
    {
        return $this->view('auth/register');
    }

    /**
     * Handle registration
     */
    public function register(Request $request): Response
    {
        $data = $this->validate($request->all(), [
            'name' => 'required|min:2|max:100',
            'email' => 'required|email|unique:users,email',
            'password' => 'required|min:8|confirmed',
            'password_confirmation' => 'required'
        ], [
            'password.confirmed' => 'Passwords do not match'
        ]);

        $user = new User();
        $userId = $user->createUser([
            'name' => $data['name'],
            'email' => $data['email'],
            'password' => $data['password'],
            'role' => 'user'
        ]);

        Logger::info("User registered", ['user_id' => $userId, 'email' => $data['email']]);

        // Log user in
        Session::set('user_id', $userId);
        Session::regenerate();

        return $this->redirect('/dashboard')
            ->with('success', 'Registration successful! Welcome!');
    }

    /**
     * Show login form
     */
    public function showLogin(Request $request): Response
    {
        return $this->view('auth/login');
    }

    /**
     * Handle login
     */
    public function login(Request $request): Response
    {
        $data = $this->validate($request->all(), [
            'email' => 'required|email',
            'password' => 'required'
        ]);

        $user = new User();
        $authenticatedUser = $user->verifyCredentials($data['email'], $data['password']);

        if (!$authenticatedUser) {
            Logger::warning("Failed login attempt", ['email' => $data['email'], 'ip' => $request->ip()]);

            return $this->redirect('/login')
                ->with('error', 'Invalid email or password')
                ->withInput($request->only(['email']));
        }

        // Login successful
        Session::set('user_id', $authenticatedUser['id']);
        Session::set('user_name', $authenticatedUser['name']);
        Session::set('user_role', $authenticatedUser['role']);
        Session::regenerate();

        Logger::info("User logged in", [
            'user_id' => $authenticatedUser['id'],
            'email' => $authenticatedUser['email']
        ]);

        return $this->redirect('/dashboard')
            ->with('success', "Welcome back, {$authenticatedUser['name']}!");
    }

    /**
     * Handle logout
     */
    public function logout(Request $request): Response
    {
        $userId = Session::get('user_id');

        Logger::info("User logged out", ['user_id' => $userId]);

        Session::destroy();

        return $this->redirect('/')
            ->with('success', 'You have been logged out');
    }
}
```

**Auth Middleware** (`src/middleware/AuthMiddleware.php`):
```php
<?php

class AuthMiddleware extends Middleware
{
    public function handle(Request $request, callable $next): Response
    {
        if (!Session::has('user_id')) {
            return Response::redirect('/login')
                ->with('error', 'Please log in to continue');
        }

        return $next($request);
    }
}
```

**Routes**:
```php
// Authentication routes
$router->get('/register', 'AuthController@showRegister', ['name' => 'register']);
$router->post('/register', 'AuthController@register', ['middleware' => ['csrf']]);

$router->get('/login', 'AuthController@showLogin', ['name' => 'login']);
$router->post('/login', 'AuthController@login', ['middleware' => ['csrf']]);

$router->post('/logout', 'AuthController@logout', [
    'name' => 'logout',
    'middleware' => ['auth', 'csrf']
]);

// Protected routes
$router->group(['middleware' => ['auth']], function($router) {
    $router->get('/dashboard', 'DashboardController@index', ['name' => 'dashboard']);
    $router->get('/profile', 'ProfileController@show', ['name' => 'profile']);
});
```

**Login View** (`src/app/Views/auth/login.php`):
```php
@extends('layouts/main')

@section('title', 'Login')

@section('content')
    <div class="auth-form">
        <h1>Login</h1>

        @if(flash('error'))
            <div class="alert alert-danger">{{ flash('error') }}</div>
        @endif

        @if(flash('success'))
            <div class="alert alert-success">{{ flash('success') }}</div>
        @endif

        <form method="POST" action="<?php echo route('login'); ?>">
            <?php echo csrfField(); ?>

            <div class="form-group">
                <label for="email">Email</label>
                <input type="email"
                       id="email"
                       name="email"
                       value="{{ old('email') }}"
                       required
                       autofocus>
            </div>

            <div class="form-group">
                <label for="password">Password</label>
                <input type="password"
                       id="password"
                       name="password"
                       required>
            </div>

            <button type="submit" class="btn btn-primary">Login</button>
        </form>

        <p class="auth-link">
            Don't have an account?
            <a href="<?php echo route('register'); ?>">Register here</a>
        </p>
    </div>
@endsection
```

---

## 17. Deployment

For comprehensive deployment instructions, see **DEPLOYMENT.md**.

### Quick Deployment Checklist

**Before Deploying**:
- [ ] Set `APP_ENV=production` in `.env`
- [ ] Set `APP_DEBUG=false` in `.env`
- [ ] Configure database credentials
- [ ] Generate secure `APP_KEY` if needed
- [ ] Set `SESSION_SECURE=true` for HTTPS
- [ ] Review and update `.env` file
- [ ] Test application thoroughly
- [ ] Create database backups

**Server Setup**:
- [ ] PHP 8.0+ installed
- [ ] Required PHP extensions enabled
- [ ] Web server configured (Apache/Nginx)
- [ ] HTTPS certificate installed (Let's Encrypt)
- [ ] File permissions set correctly (755/644)
- [ ] Writable directories: `cache/`, `logs/`, `filestore/`

**Security**:
- [ ] Security headers enabled
- [ ] `.env` file not web-accessible
- [ ] Error display disabled
- [ ] Database user has minimal privileges
- [ ] Firewall configured
- [ ] Regular security updates scheduled

**Performance**:
- [ ] OPcache enabled
- [ ] View caching enabled
- [ ] Gzip compression enabled
- [ ] Browser caching configured
- [ ] Database queries optimized

**Monitoring**:
- [ ] Error logging enabled
- [ ] Log rotation configured
- [ ] Monitoring tools set up
- [ ] Backup strategy implemented

### Server Requirements

**Minimum**:
- PHP 8.0+
- MySQL 5.7+ / MariaDB 10.3+
- 128MB RAM per process
- Apache 2.4+ or Nginx 1.18+

**Recommended**:
- PHP 8.1+
- MySQL 8.0+ / MariaDB 10.6+
- 256MB RAM per process
- SSD storage

**PHP Extensions**:
```bash
# Check installed extensions
php -m | grep -E 'pdo|mysqli|mbstring|openssl|json|fileinfo'
```

Required: `pdo`, `pdo_mysql`, `mysqli`, `mbstring`, `openssl`, `json`, `fileinfo`

### Performance Tips

**OPcache Configuration** (`php.ini`):
```ini
opcache.enable=1
opcache.memory_consumption=128
opcache.max_accelerated_files=10000
opcache.revalidate_freq=2
```

**View Caching** (`.env`):
```ini
VIEW_CACHE=true
```

**Database Optimization**:
- Use indexes on frequently queried columns
- Limit `SELECT` columns (avoid `SELECT *`)
- Use query builder for complex queries
- Implement application-level caching

For complete deployment guide, see **DEPLOYMENT.md**.

---

## 18. API Reference

### Quick Reference

**Core Classes**:
- `Router` - Route management and dispatching
- `Controller` - Base controller for app controllers
- `Model` - Base model for database operations
- `View` - Template rendering engine
- `Request` - HTTP request handling
- `Response` - HTTP response generation
- `Validator` - Input validation
- `Security` - Security features (CSRF, XSS, passwords)
- `Session` - Session management
- `Middleware` - Request filtering base class
- `Database` - Database connection manager
- `ErrorHandler` - Global error and exception handling
- `Config` - Configuration management
- `Env` - Environment variable loader
- `Logger` - PSR-3 logging system

**Helper Functions**: `e()`, `escape()`, `csrfField()`, `csrfToken()`, `old()`, `url()`, `asset()`, `route()`, `redirect()`, `back()`, `config()`, `env()`, `session()`, `flash()`, `logger()`, `view()`, `json()`, `abort()`, `sanitize()`, `dd()`, and more.

### Links

- **Official Documentation**: This file
- **Deployment Guide**: DEPLOYMENT.md
- **Project README**: README.md
- **Development Guide**: CLAUDE.md
- **Phase Reports**: PHASE*_COMPLETED.md

### Getting Help

**Resources**:
- Read this documentation
- Check DEPLOYMENT.md for production setup
- Review code examples in this file
- Examine test files (`test_phase*.php`)
- Check phase completion reports

**Troubleshooting**:
- Enable debug mode temporarily (`APP_DEBUG=true`)
- Check error logs in `src/logs/`
- Review Apache/Nginx error logs
- Verify file permissions (755/644)
- Clear cache if needed: `rm -rf src/cache/views/*`

---

## Conclusion

You now have a comprehensive guide to the **ADA PHP Micro Framework**. This framework provides everything needed for building modern, secure web applications with zero external dependencies.

**Key Strengths**:
- ✅ Zero dependencies - pure PHP
- ✅ Security built-in by default
- ✅ Clean, intuitive API
- ✅ Production-ready
- ✅ Well-documented
- ✅ Easy to learn and use

**Next Steps**:
1. Follow the Installation & Setup guide
2. Build your first application
3. Explore the complete examples
4. Refer to specific sections as needed

Happy coding with ADA! 🚀

---

**Framework Version**: 1.0.0
**Documentation Version**: 1.0
**Last Updated**: 2025-10-29
