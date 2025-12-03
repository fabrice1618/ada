# ADA Project - Agent Guidelines

## Build/Run Commands
- **Start development environment**: `docker-compose up --build`
- **Stop environment**: `docker-compose down`
- **Rebuild containers**: `docker-compose up --build --force-recreate`
- **Access web app**: http://localhost:8080
- **Access database**: mysql -h localhost -P 3307 -u ada -p ada

## Code Style Guidelines

### PHP
- Use PDO for database connections with prepared statements
- Enable PDO error mode: `PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION`
- Validate and sanitize all user inputs (filter_var, trim)
- Use exceptions for error handling instead of die()
- Function names: camelCase (e.g., `validatePersonalData`)
- Variable names: snake_case for database columns, camelCase for variables
- Use meaningful English names (avoid French unless domain-specific)
- Add PHPDoc comments for functions with @param and @return
- Exit script after header redirects with `exit()`

### Database
- Table names: plural nouns (e.g., `deposes`, `devoirs`)
- Column names: snake_case (e.g., `date_depot`, `nom_fichier`)
- Use foreign keys with CASCADE constraints
- Use AUTO_INCREMENT for primary keys
- Use appropriate data types (VARCHAR with limits, DATETIME for timestamps)

### Security
- Implement CSRF protection for forms
- Sanitize file uploads (type, size validation)
- Use prepared statements to prevent SQL injection
- Validate URLs with FILTER_VALIDATE_URL
- Store uploaded files outside web root

### HTML/CSS
- Use Bootstrap 5.3+ for consistent styling
- Include proper meta charset and viewport tags
- Use semantic HTML elements
- Keep inline styles minimal, prefer external CSS