# AGENTS.md - ADA Assignment Submission System

## Build/Lint/Test Commands
- **Build**: `docker-compose build`
- **Run**: `docker-compose up -d`
- **Stop**: `docker-compose down`
- **Rebuild**: `docker-compose up --build`
- **Database reset**: `docker-compose down -v && docker-compose up -d`
- **Single test**: No automated tests configured - manual testing via browser at http://localhost:8080

## Code Style Guidelines

### PHP
- **Imports**: Use `require_once` or direct class instantiation (no autoloader configured)
- **Formatting**: 4-space indentation, consistent with existing codebase
- **Types**: Use type hints where possible (PHP 8.2 features available)
- **Naming**: camelCase for variables/functions, PascalCase for classes, snake_case for database columns
- **Error handling**: Use try/catch with PDO exceptions, throw custom Exception messages
- **Database**: Use PDO with prepared statements, validate all inputs
- **File uploads**: Validate size (10MB max), type restrictions, generate unique filenames
- **Security**: Filter inputs with `filter_var`, escape outputs, validate URLs/emails

### HTML/CSS
- **Framework**: Bootstrap 5.3+ for responsive design
- **Structure**: Semantic HTML with proper form validation
- **JavaScript**: Vanilla JS for simple interactions, no frameworks

### Database
- **Schema**: InnoDB engine, foreign keys with CASCADE constraints
- **Naming**: French field names (prenom, nom, datedepot), English table names
- **Migrations**: SQL files in `/database` directory executed on container startup

### Docker
- **Web**: PHP 8.2-Apache with MySQL extensions
- **Database**: MySQL 8.0 with persistent volumes
- **Ports**: Web on 8080, DB on 3307</content>
<parameter name="filePath">/home/ada/AGENTS.md