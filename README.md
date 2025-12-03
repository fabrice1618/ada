# PHP Micro Framework

A lightweight, fast, and secure MVC framework for PHP with **zero external dependencies**.

## Philosophy

- **Simple**: Minimal learning curve, intuitive API
- **Fast**: Low overhead, efficient routing and rendering
- **Secure**: Built-in protection against XSS, CSRF, and SQL injection
- **Pure PHP**: No third-party libraries required

## Features

### Core Components

- **Router**: Single entry point (index.php) with dynamic route matching and parameters
- **MVC Architecture**: Full Model-View-Controller pattern
- **Middleware Pipeline**: Chain of responsibility for request filtering
- **Template Engine**: Simple syntax with layouts, sections, and automatic XSS escaping
- **Database Layer**: PDO-based with query builder and prepared statements
- **Validation System**: Fluent validation with 15+ built-in rules
- **Error Handling**: Dedicated error controller for 404, 500, 403, etc.

### Security Features

- **CSRF Protection**: Token-based protection for all state-changing requests
- **XSS Prevention**: Automatic output escaping in templates
- **SQL Injection Protection**: Prepared statements exclusively
- **Secure Sessions**: HttpOnly, Secure, SameSite cookie flags
- **Input Sanitization**: Built-in validation and sanitization utilities
- **Security Headers**: X-Frame-Options, X-Content-Type-Options, CSP support

### Request/Response

- **Request Object**: Clean access to GET, POST, FILES with security helpers
- **Response Object**: View rendering, redirects, JSON responses
- **Flash Messages**: One-time session messages for user feedback
- **File Uploads**: Secure file handling with validation

## Directory Structure

```
framework_PHP/
├── .htaccess                 # Apache rewrite rules
├── index.php                 # Front controller (router)
├── app/
│   ├── Controllers/          # Application controllers
│   ├── Models/               # Database models
│   └── Views/                # Template files
│       ├── layouts/          # Master layouts
│       ├── partials/         # Reusable components
│       └── errors/           # Error pages (404, 500)
├── config/
│   ├── app.php              # Application settings
│   ├── database.php         # Database credentials
│   ├── routes.php           # Route definitions
│   └── security.php         # Security configuration
├── core/                    # Framework core classes
│   ├── Router.php
│   ├── Controller.php
│   ├── Model.php
│   ├── View.php
│   ├── Request.php
│   ├── Response.php
│   ├── Session.php
│   ├── Validator.php
│   ├── Database.php
│   ├── Middleware.php
│   └── Security.php
├── middleware/              # Custom middleware
└── public/                  # Public assets (css, js, images)
```

## Quick Start

### 1. Define Routes

**config/routes.php:**
```php
return [
    ['GET', '/', 'HomeController@index'],
    ['GET', '/about', 'HomeController@about'],
    ['GET', '/users/{id}', 'UserController@show'],
    ['POST', '/users', 'UserController@store', ['csrf']],
];
```

### 2. Create Controller

**app/Controllers/HomeController.php:**
```php
class HomeController extends Controller
{
    public function index()
    {
        return $this->view('home/index', [
            'title' => 'Welcome'
        ]);
    }
}
```

### 3. Create Model

**app/Models/User.php:**
```php
class User extends Model
{
    protected $table = 'users';
    protected $fillable = ['name', 'email'];

    public function findByEmail($email)
    {
        return $this->findBy('email', $email);
    }
}
```

### 4. Create View

**app/Views/home/index.php:**
```php
@extends('layouts/main')

@section('content')
    <h1>{{ $title }}</h1>
    <p>Welcome to the micro framework!</p>
@endsection
```

## Template Syntax

```php
{{ $variable }}              // Escaped output (XSS safe)
{!! $html !!}                // Raw output (unescaped)
@extends('layout')           // Inherit from layout
@section('name')             // Define content section
@yield('name')               // Output section content
@include('partial')          // Include partial
@if / @foreach / @for        // Control structures
```

## Database Operations

```php
// SELECT
$users = $model->all();
$user = $model->find($id);
$user = $model->findBy('email', 'user@example.com');
$users = $model->where('status', 'active')->get();

// INSERT
$id = $model->create([
    'name' => 'John Doe',
    'email' => 'john@example.com'
]);

// UPDATE
$affected = $model->update($id, ['name' => 'Jane Doe']);

// DELETE
$success = $model->delete($id);
```

## Validation

```php
$validator = Validator::make($request->all(), [
    'name' => 'required|min:3|max:50',
    'email' => 'required|email|unique:users,email',
    'password' => 'required|min:8',
    'password_confirm' => 'required|match:password'
]);

if ($validator->fails()) {
    return redirect()->back()
        ->withErrors($validator->errors())
        ->withInput();
}
```

### Built-in Validation Rules

`required`, `email`, `min:n`, `max:n`, `numeric`, `integer`, `alpha`, `alphanumeric`, `url`, `match:field`, `unique:table,column`, `exists:table,column`, `in:val1,val2`, `regex:pattern`

## Middleware

**middleware/AuthMiddleware.php:**
```php
class AuthMiddleware extends Middleware
{
    public function handle(Request $request, callable $next)
    {
        if (!Session::has('user_id')) {
            return Response::redirect('/login');
        }

        return $next($request);
    }
}
```

Apply to routes:
```php
['GET', '/dashboard', 'DashboardController@index', ['auth']],
```

## Security

### CSRF Protection

Add to all forms:
```php
<?php echo csrfField(); ?>
```

Automatically validated on POST/PUT/DELETE requests.

### XSS Prevention

All template output is automatically escaped:
```php
{{ $userInput }}  // Safe, escaped
```

### SQL Injection

All queries use prepared statements:
```php
$model->query('SELECT * FROM users WHERE email = ?', [$email]);
```

## Server Requirements

- **PHP**: 7.4+ or 8.0+
- **Apache**: 2.4+ with mod_rewrite enabled
- **Database**: MySQL 5.7+, PostgreSQL 10+, or SQLite 3
- **Memory**: 128MB+ per request recommended

## Installation

1. Clone or download the framework
2. Configure Apache virtual host with `AllowOverride All`
3. Copy `.env.example` to `.env` and configure database
4. Set proper file permissions:
   - Directories: 755
   - PHP files: 644
   - Config files: 600
   - Logs directory: 777 (or 755 with proper owner)
5. Create database and tables
6. Access via web browser

## Apache Configuration

Ensure `.htaccess` is present in root:
```apache
RewriteEngine On
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d
RewriteRule ^(.*)$ index.php [QSA,L]
```

## Performance Targets

- Page load: < 200ms (without external resources)
- Memory usage: < 10MB per request
- Database queries: < 10 per page
- Template rendering: < 50ms

## Development Workflow

1. **Define routes** in `config/routes.php`
2. **Create controller** in `app/Controllers/`
3. **Create model** in `app/Models/` (if database access needed)
4. **Create views** in `app/Views/`
5. **Test** in browser and verify security

## Error Handling

The framework includes a dedicated `ErrorController` for:
- **404**: Route not found
- **500**: Internal server error
- **403**: Forbidden
- **405**: Method not allowed

Custom error pages in `app/Views/errors/`

## Configuration

### Database (config/database.php)
```php
return [
    'driver' => 'mysql',
    'host' => 'localhost',
    'database' => 'your_database',
    'username' => 'your_username',
    'password' => 'your_password',
    'charset' => 'utf8mb4'
];
```

### Application (config/app.php)
```php
return [
    'name' => 'My Application',
    'environment' => 'development', // or 'production'
    'debug' => true,
    'timezone' => 'UTC'
];
```

## Documentation

For complete specifications and architecture details, see:
- **spec.md**: Full framework specification
- **plan.md**: Implementation roadmap (6 phases, 80 tasks)

## Implementation Status

This framework is designed to be implemented in **6 progressive phases**:

1. **Phase 1**: MVP - Basic routing and views
2. **Phase 2**: Database layer and models
3. **Phase 3**: Security foundation (CSRF, XSS, sessions)
4. **Phase 4**: Middleware system
5. **Phase 5**: Advanced features (validation, error handling, templates)
6. **Phase 6**: Production polish and documentation

See `plan.md` for detailed implementation tasks.

## Security Best Practices

- ✅ All user input is validated and sanitized
- ✅ All output is escaped by default
- ✅ All database queries use prepared statements
- ✅ CSRF tokens on all state-changing requests
- ✅ Secure session configuration
- ✅ Security headers enabled
- ✅ Password hashing with `password_hash()`
- ✅ File uploads validated and sanitized

## License

Open source - choose your preferred license.

## Contributing

Contributions welcome! Focus areas:
- Security improvements
- Performance optimizations
- Additional validation rules
- Documentation enhancements

---

**Version**: 1.0
**Status**: Specification Complete, Ready for Implementation
**Estimated Development Time**: 17-23 hours

For questions or issues, refer to the full specification in `ai_prompt/spec.md`.
