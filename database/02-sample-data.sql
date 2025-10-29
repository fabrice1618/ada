-- Sample data for testing Phase 2 database layer

USE ada;

-- Insert sample devoirs (assignments)
INSERT INTO devoirs (shortcode, datelimite) VALUES
    ('PHP-MVC-2024', '2024-12-31'),
    ('DATABASE-101', '2025-11-15'),
    ('SECURITY-BASICS', '2025-12-01')
ON DUPLICATE KEY UPDATE shortcode = VALUES(shortcode);

-- Insert sample deposes (submissions)
INSERT INTO deposes (nom, prenom, datedepot, url, nomfichieroriginal, nomfichierstockage, iddevoirs) VALUES
    ('Dupont', 'Jean', '2024-10-15 10:30:00', 'https://github.com/jeandupont/php-mvc', 'projet.zip', 'uploads/abc123.zip', 1),
    ('Martin', 'Sophie', '2024-10-20 14:45:00', NULL, 'assignment.pdf', 'uploads/def456.pdf', 1),
    ('Durand', 'Pierre', '2024-10-25 09:15:00', 'https://github.com/pdurand/database', 'database.sql', 'uploads/ghi789.sql', 2)
ON DUPLICATE KEY UPDATE nom = VALUES(nom);
