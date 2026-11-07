-- =========================================================
-- DIE INSEL BAR & RESTAURANT
-- BUSINESS ANALYTICS PLATFORM
-- Database Initialization
-- =========================================================

CREATE DATABASE IF NOT EXISTS die_insel_analytics
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE die_insel_analytics;

SELECT
    DATABASE() AS active_database,
    VERSION() AS mysql_version;

SHOW TABLES;