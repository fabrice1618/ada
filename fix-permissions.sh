#!/bin/bash
#
# Fix Permissions Script
# Ensures proper permissions for cache and logs directories
#

echo "🔧 Fixing ADA Framework permissions..."

# Fix cache directory
docker exec ada_web chown -R www-data:www-data /var/www/html/cache
docker exec ada_web chmod -R 775 /var/www/html/cache
echo "✓ Cache directory permissions fixed"

# Fix logs directory
docker exec ada_web mkdir -p /var/www/html/logs
docker exec ada_web chown -R www-data:www-data /var/www/html/logs
docker exec ada_web chmod -R 775 /var/www/html/logs
echo "✓ Logs directory permissions fixed"

# Fix filestore directory
docker exec ada_web chown -R www-data:www-data /var/www/html/filestore
docker exec ada_web chmod -R 775 /var/www/html/filestore
echo "✓ Filestore directory permissions fixed"

echo "✅ All permissions fixed!"
echo ""
echo "You can now access:"
echo "  • Main app: http://localhost:8080/"
echo "  • Phase 6 tests: http://localhost:8080/test_phase6.php"
