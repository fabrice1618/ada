# ADA Framework - Deployment Guide

This guide provides comprehensive instructions for deploying the ADA PHP Micro Framework to production environments.

---

## Table of Contents

1. [Server Requirements](#server-requirements)
2. [Pre-Deployment Checklist](#pre-deployment-checklist)
3. [Environment Configuration](#environment-configuration)
4. [File Permissions](#file-permissions)
5. [Web Server Configuration](#web-server-configuration)
6. [Database Setup](#database-setup)
7. [Security Hardening](#security-hardening)
8. [Performance Optimization](#performance-optimization)
9. [Monitoring and Logging](#monitoring-and-logging)
10. [Troubleshooting](#troubleshooting)

---

## Server Requirements

### Minimum Requirements

- **PHP**: 8.0 or higher
- **Web Server**: Apache 2.4+ or Nginx 1.18+
- **Database**: MySQL 5.7+ or MariaDB 10.3+
- **Memory**: 128MB per process (recommended 256MB)
- **Disk Space**: 100MB minimum

### Required PHP Extensions

```bash
php -m | grep -E 'pdo|pdo_mysql|mysqli|mbstring|openssl|json|fileinfo'
```

Required extensions:
- `pdo`
- `pdo_mysql`
- `mysqli`
- `mbstring`
- `openssl`
- `json`
- `fileinfo`
- `session`

### Recommended PHP Extensions

- `opcache` - For improved performance
- `apcu` - For caching
- `curl` - For external HTTP requests

---

## Pre-Deployment Checklist

### Code Preparation

- [ ] All code is committed to version control
- [ ] Application has been tested in staging environment
- [ ] Database migrations are ready
- [ ] Configuration files are prepared
- [ ] Third-party dependencies are documented

### Security Review

- [ ] All user inputs are validated
- [ ] SQL injection protection verified
- [ ] XSS protection enabled
- [ ] CSRF tokens implemented on all forms
- [ ] Password hashing uses bcrypt
- [ ] Security headers configured
- [ ] Error reporting disabled in production
- [ ] Debug mode disabled

### Performance Review

- [ ] Database queries optimized
- [ ] Indexes added to database tables
- [ ] View caching enabled
- [ ] OPcache configured
- [ ] Static assets minified
- [ ] Gzip compression enabled

---

## Environment Configuration

### 1. Create .env File

Copy `.env.example` to `.env` and configure for production:

```bash
cp .env.example .env
chmod 600 .env  # Restrict permissions
```

### 2. Production Environment Variables

```ini
# Application
APP_NAME="Your Application"
APP_ENV=production
APP_DEBUG=false
APP_URL=https://yourdomain.com
APP_TIMEZONE=UTC

# Database
DB_HOST=localhost
DB_NAME=your_database
DB_USER=your_user
DB_PASS=your_secure_password
DB_CHARSET=utf8mb4

# Session
SESSION_SECURE=true  # HTTPS only
SESSION_LIFETIME=7200

# Logging
LOG_LEVEL=error  # Only log errors in production

# Cache
VIEW_CACHE=true

# Maintenance
MAINTENANCE_MODE=false
```

### 3. Security Considerations

**IMPORTANT**: Never commit `.env` to version control!

Add to `.gitignore`:
```
.env
/logs/*.log
/cache/*
```

---

## File Permissions

### Recommended Permission Structure

```bash
# Application root
chmod 755 /path/to/app

# Core and app directories (read-only for web server)
chmod -R 755 src/core
chmod -R 755 src/app
chmod -R 755 src/config

# Writable directories
chmod -R 775 src/logs
chmod -R 775 src/cache
chmod -R 775 filestore

# Set ownership (www-data for Apache/Nginx)
chown -R www-data:www-data src/logs
chown -R www-data:www-data src/cache
chown -R www-data:www-data filestore

# Secure environment file
chmod 600 .env
chown www-data:www-data .env
```

### Create Required Directories

```bash
mkdir -p src/logs
mkdir -p src/cache/views
mkdir -p filestore
```

---

## Web Server Configuration

### Apache Configuration

#### .htaccess (already included)

Ensure `mod_rewrite` is enabled:

```bash
sudo a2enmod rewrite
sudo systemctl restart apache2
```

#### Virtual Host Configuration

```apache
<VirtualHost *:80>
    ServerName yourdomain.com
    ServerAlias www.yourdomain.com

    DocumentRoot /path/to/app/src

    <Directory /path/to/app/src>
        Options -Indexes +FollowSymLinks
        AllowOverride All
        Require all granted
    </Directory>

    # Error and access logs
    ErrorLog /var/log/apache2/ada_error.log
    CustomLog /var/log/apache2/ada_access.log combined

    # Security headers
    Header always set X-Frame-Options "SAMEORIGIN"
    Header always set X-Content-Type-Options "nosniff"
    Header always set X-XSS-Protection "1; mode=block"
    Header always set Referrer-Policy "strict-origin-when-cross-origin"
</VirtualHost>

# HTTPS Configuration (recommended)
<VirtualHost *:443>
    ServerName yourdomain.com
    ServerAlias www.yourdomain.com

    DocumentRoot /path/to/app/src

    SSLEngine on
    SSLCertificateFile /path/to/ssl/cert.pem
    SSLCertificateKeyFile /path/to/ssl/key.pem

    <Directory /path/to/app/src>
        Options -Indexes +FollowSymLinks
        AllowOverride All
        Require all granted
    </Directory>

    # Security headers
    Header always set Strict-Transport-Security "max-age=31536000; includeSubDomains"
    Header always set X-Frame-Options "SAMEORIGIN"
    Header always set X-Content-Type-Options "nosniff"
    Header always set X-XSS-Protection "1; mode=block"
</VirtualHost>
```

### Nginx Configuration

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    root /path/to/app/src;
    index index.php;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Disable access to hidden files
    location ~ /\. {
        deny all;
    }

    # Route all requests through index.php
    location / {
        try_files $uri $uri/ /index.php?$query_string;
    }

    # PHP handling
    location ~ \.php$ {
        fastcgi_pass unix:/var/run/php/php8.2-fpm.sock;
        fastcgi_index index.php;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        include fastcgi_params;
    }

    # Cache static files
    location ~* \.(jpg|jpeg|png|gif|ico|css|js|svg|woff|woff2|ttf)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Deny access to sensitive files
    location ~ /(\.env|\.git|composer\.(json|lock)|package\.json) {
        deny all;
    }
}

# HTTPS Configuration
server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /path/to/ssl/cert.pem;
    ssl_certificate_key /path/to/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;

    # Include all location blocks from above
    # ...
}
```

---

## Database Setup

### 1. Create Production Database

```sql
CREATE DATABASE ada CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'ada_user'@'localhost' IDENTIFIED BY 'secure_password';
GRANT SELECT, INSERT, UPDATE, DELETE ON ada.* TO 'ada_user'@'localhost';
FLUSH PRIVILEGES;
```

### 2. Import Schema

```bash
mysql -u ada_user -p ada < database/01-init.sql
```

### 3. Database Security

- Use strong, unique passwords
- Limit user privileges (no DROP, CREATE, ALTER in production)
- Use prepared statements (already implemented in framework)
- Enable MySQL slow query log for monitoring

### 4. Database Optimization

```sql
-- Add indexes to frequently queried columns
ALTER TABLE devoirs ADD INDEX idx_shortcode (shortcode);
ALTER TABLE deposes ADD INDEX idx_iddevoirs (iddevoirs);
ALTER TABLE deposes ADD INDEX idx_datedepot (datedepot);
```

---

## Security Hardening

### 1. PHP Configuration (php.ini)

```ini
# Production Settings
display_errors = Off
display_startup_errors = Off
error_reporting = E_ALL
log_errors = On
error_log = /path/to/php_errors.log

# Security
expose_php = Off
allow_url_fopen = Off
allow_url_include = Off
enable_dl = Off

# Session Security
session.cookie_httponly = 1
session.cookie_secure = 1
session.use_strict_mode = 1
session.cookie_samesite = Lax

# Upload limits
upload_max_filesize = 10M
post_max_size = 10M
max_file_uploads = 5

# Resource limits
max_execution_time = 30
max_input_time = 30
memory_limit = 256M
```

### 2. Disable Directory Listing

Already configured in `.htaccess`:
```apache
Options -Indexes
```

### 3. Protect Sensitive Files

Ensure these files are not web-accessible:
- `.env`
- `composer.json`
- `database/` directory
- `logs/` directory

### 4. SSL/TLS Certificate

Use Let's Encrypt for free SSL certificates:

```bash
sudo apt install certbot python3-certbot-apache
sudo certbot --apache -d yourdomain.com -d www.yourdomain.com
```

### 5. Firewall Configuration

```bash
# Ubuntu/Debian with UFW
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

---

## Performance Optimization

### 1. Enable OPcache

In `php.ini`:

```ini
opcache.enable=1
opcache.enable_cli=0
opcache.memory_consumption=128
opcache.interned_strings_buffer=8
opcache.max_accelerated_files=10000
opcache.revalidate_freq=2
opcache.fast_shutdown=1
```

### 2. Enable View Caching

In `.env`:
```ini
VIEW_CACHE=true
```

### 3. Gzip Compression (Apache)

```apache
<IfModule mod_deflate.c>
    AddOutputFilterByType DEFLATE text/html text/plain text/xml text/css text/javascript application/javascript application/json
</IfModule>
```

### 4. Browser Caching

Already configured in `.htaccess` for static assets.

### 5. Database Connection Pooling

Use persistent connections (already implemented via PDO).

---

## Monitoring and Logging

### 1. Application Logs

Location: `src/logs/app-YYYY-MM-DD.log`

Monitor for errors:
```bash
tail -f src/logs/app-$(date +%Y-%m-%d).log
```

### 2. Web Server Logs

```bash
# Apache
tail -f /var/log/apache2/ada_error.log

# Nginx
tail -f /var/log/nginx/error.log
```

### 3. PHP Error Logs

```bash
tail -f /var/log/php8.2-fpm.log
```

### 4. Log Rotation

Create `/etc/logrotate.d/ada`:

```
/path/to/app/src/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
}
```

### 5. Monitoring Tools

Consider implementing:
- **Application**: New Relic, Datadog
- **Server**: Nagios, Zabbix
- **Uptime**: UptimeRobot, Pingdom

---

## Troubleshooting

### Common Issues

#### 1. 500 Internal Server Error

**Cause**: PHP errors, permission issues, or configuration problems

**Solution**:
```bash
# Check Apache error log
tail -n 50 /var/log/apache2/ada_error.log

# Check PHP error log
tail -n 50 /var/log/php_errors.log

# Verify file permissions
ls -la src/logs
ls -la src/cache
```

#### 2. Database Connection Failed

**Cause**: Incorrect credentials or database not accessible

**Solution**:
```bash
# Test database connection
mysql -h localhost -u ada_user -p ada

# Check config/database.php settings
# Verify .env file exists and is readable
```

#### 3. CSRF Token Mismatch

**Cause**: Session not persisting or token regeneration issues

**Solution**:
- Verify session.cookie_secure setting matches HTTPS usage
- Check session directory is writable
- Ensure APP_URL in .env matches actual domain

#### 4. File Upload Fails

**Cause**: Permission issues or PHP upload limits

**Solution**:
```bash
# Check filestore permissions
chmod 775 filestore
chown www-data:www-data filestore

# Check PHP settings
php -i | grep upload_max_filesize
php -i | grep post_max_size
```

### Debug Mode (Temporary)

Only enable for troubleshooting:

```ini
# .env
APP_DEBUG=true
APP_ENV=development
```

**IMPORTANT**: Always disable debug mode after troubleshooting!

---

## Deployment Checklist

Before going live:

- [ ] Environment configured for production
- [ ] Debug mode disabled
- [ ] HTTPS certificate installed
- [ ] Database credentials secure
- [ ] File permissions correct
- [ ] Logs directory writable
- [ ] Cache directory writable
- [ ] Security headers enabled
- [ ] Firewall configured
- [ ] Backups configured
- [ ] Monitoring tools set up
- [ ] SSL certificate auto-renewal configured
- [ ] Application tested in production environment

---

## Backup Strategy

### Database Backups

```bash
#!/bin/bash
# backup-database.sh
DATE=$(date +%Y%m%d_%H%M%S)
mysqldump -u ada_user -p ada > /backups/ada_$DATE.sql
gzip /backups/ada_$DATE.sql

# Keep only last 30 days
find /backups -name "ada_*.sql.gz" -mtime +30 -delete
```

Add to crontab:
```bash
0 2 * * * /path/to/backup-database.sh
```

### File Backups

Include these directories in your backup:
- `src/` (entire application)
- `filestore/` (uploaded files)
- `.env` (configuration)
- Database dumps

---

## Support and Resources

- **Documentation**: See README.md
- **GitHub**: [Repository URL]
- **Security Issues**: Report privately to security@yourdomain.com

---

**Last Updated**: 2025-10-29
