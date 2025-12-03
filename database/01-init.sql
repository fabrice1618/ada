-- ADA Database Initialization Script
-- This script is automatically executed when the MySQL container starts

USE ada;

-- Create a sample table for demonstration
CREATE TABLE IF NOT EXISTS users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample data
INSERT INTO users (username, email) VALUES
    ('admin', 'admin@ada.local'),
    ('user1', 'user1@ada.local')
ON DUPLICATE KEY UPDATE username = VALUES(username);



CREATE TABLE IF NOT EXISTS devoirs (
    iddevoirs INT AUTO_INCREMENT PRIMARY KEY,
    shortcode VARCHAR(50) NOT NULL,
    datelimite DATE NOT NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS deposes (
    iddeposes INT AUTO_INCREMENT PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    prenom VARCHAR(100) NOT NULL,
    datedepot DATETIME NOT NULL,
    url VARCHAR(255),
    nomfichieroriginal VARCHAR(255),
    nomfichierstockage VARCHAR(255),
    iddevoirs INT NOT NULL,
    CONSTRAINT fk_devoir
        FOREIGN KEY (iddevoirs) REFERENCES devoirs(iddevoirs)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB;

-- Create ada_user and grant privileges
CREATE USER IF NOT EXISTS 'ada_user'@'%' IDENTIFIED BY 'ada_password';
GRANT ALL PRIVILEGES ON ada.* TO 'ada_user'@'%';
FLUSH PRIVILEGES;