# ADA PHP Framework - Agent Guidelines

## Build/Lint/Test Commands

### Development Environment
- **Start containers**: `docker-compose up -d`
- **Stop containers**: `docker-compose down`
- **Access app**: http://localhost:8080

### Testing
- **Manual tests**: Run individual test files via browser:
  - CRUD operations: `http://localhost:8080/test_crud.php`
  - Middleware: `http://localhost:8080/test_phase4.php`
  - Validation: `http://localhost:8080/test_phase5.php`
  - Security: `http://localhost:8080/test_security.php`
  - Phase 6 features: `http://localhost:8080/test_phase6.php`

### Code Quality
- No automated linting tools configured
- Manual code review required for style consistency

## Code Style Guidelines

### PHP Version & Syntax
- **PHP Version**: 8.2 minimum
- **Type declarations**: Required for properties and return types
- **File structure**: Opening `<?php` tag only, no closing tag

### Naming Conventions
- **Classes**: PascalCase (e.g., `HomeController`, `UserModel`)
- **Methods**: camelCase (e.g., `findByEmail()`, `getUpcoming()`)
- **Properties**: camelCase (e.g., `$fillable`, `$timestamps`)
- **Constants**: UPPER_SNAKE_CASE
- **Files**: Match class name (e.g., `HomeController.php`)

### Code Structure
- **Includes**: `require_once __DIR__ . '/path/to/file.php'`
- **Visibility**: `protected`/`private` for properties, `public` for methods
- **DocBlocks**: PHPDoc format for all classes and public methods
- **Indentation**: 4 spaces (no tabs)

### Error Handling
- Use framework's `ErrorHandler` class
- Return appropriate HTTP status codes
- Log errors appropriately
- Validate all user input

### Security
- **CSRF**: Use `csrfField()` in forms, validate tokens
- **XSS**: All output automatically escaped via `{{ }}` syntax
- **SQL Injection**: Use prepared statements exclusively
- **Input**: Sanitize with `Security::sanitize()`</content>
<parameter name="filePath">/home/toto/ada/AGENTS.md
