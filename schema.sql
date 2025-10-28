-- Product Recommendation System schema
-- Import this file into phpMyAdmin (XAMPP) to provision the required database objects.

CREATE DATABASE IF NOT EXISTS `product_recommendation_system` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `product_recommendation_system`;

CREATE TABLE IF NOT EXISTS `users` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `username` VARCHAR(100) NOT NULL,
    `email` VARCHAR(150) NOT NULL,
    `password_hash` VARCHAR(255) NOT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `ux_users_username` (`username`),
    UNIQUE KEY `ux_users_email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
