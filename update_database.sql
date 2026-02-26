-- Run this in MySQL Workbench to update your database

USE priorityiq;

-- Add new columns to users table
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS phone VARCHAR(15) AFTER email,
ADD COLUMN IF NOT EXISTS role VARCHAR(50) AFTER phone,
ADD COLUMN IF NOT EXISTS age INT AFTER role,
ADD COLUMN IF NOT EXISTS gender VARCHAR(10) AFTER age;

-- Add unique constraint on phone
ALTER TABLE users ADD UNIQUE KEY unique_phone (phone);

-- Show updated structure
DESCRIBE users;
