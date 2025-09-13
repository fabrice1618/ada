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

-- Grant additional privileges to ada user
GRANT ALL PRIVILEGES ON ada.* TO 'ada'@'%';
FLUSH PRIVILEGES;