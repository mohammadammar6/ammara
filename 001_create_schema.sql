-- Initialize database and schema. Runs only if data dir is empty.
-- Do NOT set passwords here; Kubernetes env vars will provide them.

-- Create application database (name can be customized via MYSQL_DATABASE env var too).
CREATE DATABASE IF NOT EXISTS marriage_app CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE marriage_app;

-- Example tables — replace with your real schema
CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(255) NOT NULL UNIQUE,
  email VARCHAR(255) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS invites (
  id INT AUTO_INCREMENT PRIMARY KEY,
  -- Human-friendly invite fields used by the application
  person_name VARCHAR(120) NOT NULL,
  village_name VARCHAR(120) NOT NULL,
  total_people INT NOT NULL DEFAULT 1,
  -- Optional code and metadata
  code VARCHAR(64) DEFAULT NULL UNIQUE,
  created_by INT DEFAULT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (created_by) REFERENCES users(id)
) ENGINE=InnoDB;
