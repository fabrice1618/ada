# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**ADA** is a PHP micro framework project implementing a lightweight MVC architecture with zero external dependencies. The project has completed Phase 1 implementation with a fully functional MVC foundation.

### Current Status
- ✅ **Phase 1 Complete**: MVC architecture with routing, controllers, and views
- Working application at http://localhost:8080 (/, /about, /contact)
- Database schema defined (devoirs and deposes tables) - ready for Phase 2
- Docker-based development environment
- Comprehensive implementation report in `ai_prompt/phase1_report.md`

## Development Environment

### Running the Application

Start the Docker environment:
```bash
docker-compose up -d
```

Stop the environment:
```bash
docker-compose down
```

Access the application:
- **Web**: http://localhost:8080
- **MySQL**: localhost:3306

### Environment Configuration

Copy `.env_dist` to `.env` and configure database credentials:
```bash
cp .env_dist .env
```

Required environment variables:
- `DB_NAME`: Database name
- `DB_USER`: Database user
- `DB_PASS`: Database password
- `DB_ROOT_PASS`: MySQL root password

### Database Access

The database is automatically initialized with the schema from `database/01-init.sql` when the container first starts.

Connect to MySQL:
```bash
docker exec -it ada_db mysql -u root -p
```

## Architecture

### Current Structure

```
ada/
├── src/                    # Application source code
│   ├── index.php          # Front controller (basic routing)
│   ├── post.php           # Form processing
│   └── parts/             # HTML partials
├── database/              # Database initialization scripts
│   └── 01-init.sql       # Schema and sample data
├── build_docker/         # Docker configuration
│   ├── Dockerfile        # PHP 8.2 + Apache + MySQL extensions
│   └── 000-default.conf  # Apache configuration
├── filestore/            # File uploads storage
└── ai_prompt/            # Framework specifications
    ├── spec.md          # Complete framework specification
    └── plan.md          # 6-phase implementation plan (80 tasks)
```

### Database Schema

**devoirs** (assignments):
- `iddevoirs`: Primary key
- `shortcode`: Unique identifier for assignment
- `datelimite`: Due date

**deposes** (submissions):
- `iddeposes`: Primary key
- `nom`, `prenom`: Student name
- `datedepot`: Submission timestamp
- `url`: Optional URL submission
- `nomfichieroriginal`, `nomfichierstockage`: File upload tracking
- `iddevoirs`: Foreign key to devoirs

### Target Architecture

The project aims to implement a complete MVC framework as detailed in `ai_prompt/spec.md`:

**Core Components** (to be implemented):
- **Router**: Dynamic route matching with parameters
- **Controllers**: Base controller class with MVC support
- **Models**: PDO-based ORM with query builder
- **Views**: Template engine with layouts and escaping
- **Middleware**: Request filtering pipeline
- **Security**: CSRF protection, XSS prevention, SQL injection protection
- **Validation**: Fluent validation system with 15+ rules

## Implementation Plan

The framework is designed to be built in **6 progressive phases** (see `ai_prompt/plan.md`):

1. **Phase 1** (2-3h): MVP - Basic routing and views
2. **Phase 2** (3-4h): Database layer and models
3. **Phase 3** (3-4h): Security foundation (CSRF, XSS, sessions)
4. **Phase 4** (2-3h): Middleware system
5. **Phase 5** (4-5h): Validation, error handling, template engine
6. **Phase 6** (3-4h): Configuration, optimization, documentation

**Total Estimated Time**: 17-23 hours

When implementing features, reference the detailed task breakdown in `ai_prompt/plan.md` for step-by-step guidance.

## Security Considerations

### Built-in Security Features (Planned)

- **CSRF Protection**: Token-based validation for all POST/PUT/DELETE requests
- **XSS Prevention**: Automatic output escaping in templates
- **SQL Injection Protection**: Prepared statements exclusively
- **Secure Sessions**: HttpOnly, Secure, SameSite cookie flags
- **Input Validation**: 15+ validation rules with custom error messages
- **Security Headers**: X-Frame-Options, X-Content-Type-Options, CSP

### Current Security Status

The prototype code in `src/index.php` is a basic proof-of-concept and does NOT implement security features yet. When developing:
- All user input must be validated and sanitized
- Use prepared statements for database queries
- Escape all output
- Implement CSRF tokens for forms

## Performance Targets

As specified in the framework design:
- Page load: < 200ms (without external resources)
- Memory usage: < 10MB per request
- Database queries: < 10 per page
- Template rendering: < 50ms

## Technology Stack

- **PHP**: 8.2 (via Docker)
- **Web Server**: Apache 2.4 with mod_rewrite
- **Database**: MySQL 8.0
- **Extensions**: mysqli, pdo, pdo_mysql

## Key Design Principles

1. **Zero Dependencies**: Pure PHP implementation, no third-party libraries
2. **Security First**: All security features built-in by default
3. **MVC Architecture**: Clear separation of concerns
4. **RESTful Routing**: Standard HTTP methods and URL patterns
5. **Performance**: Lazy loading, minimal overhead
6. **Developer Experience**: Intuitive API, clear conventions

## Documentation

For detailed information, refer to:
- `ai_prompt/spec.md`: Complete 1,000+ line framework specification
- `ai_prompt/plan.md`: Detailed 80-task implementation roadmap
- `README.md`: User-facing documentation and quick start guide
