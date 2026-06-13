-- System Performance Analyser - Database Setup
-- Run this in MySQL Workbench or mysql CLI if auto-setup fails

CREATE DATABASE IF NOT EXISTS system_performance
CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE system_performance;

CREATE TABLE IF NOT EXISTS performance_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    log_time DATETIME NOT NULL,
    cpu_usage FLOAT NOT NULL,
    ram_usage FLOAT NOT NULL,
    disk_usage FLOAT NOT NULL,
    battery FLOAT DEFAULT NULL,
    bytes_sent BIGINT DEFAULT 0,
    bytes_received BIGINT DEFAULT 0
);

-- Sample query to view all logs
-- SELECT * FROM performance_logs ORDER BY log_time DESC;
