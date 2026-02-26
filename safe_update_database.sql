-- Safe database update script for PriorityIQ
-- Run this in MySQL Workbench

USE priorityiq;

-- Check current structure
DESCRIBE users;

-- Add columns only if they don't exist
-- Note: MySQL doesn't have IF NOT EXISTS for ALTER TABLE ADD COLUMN in older versions
-- So we'll use a procedure

DELIMITER $$

CREATE PROCEDURE AddColumnsIfNotExists()
BEGIN
    -- Check and add phone column
    IF NOT EXISTS (
        SELECT * FROM information_schema.COLUMNS 
        WHERE TABLE_SCHEMA = 'priorityiq' 
        AND TABLE_NAME = 'users' 
        AND COLUMN_NAME = 'phone'
    ) THEN
        ALTER TABLE users ADD COLUMN phone VARCHAR(15) AFTER email;
    END IF;

    -- Check and add role column
    IF NOT EXISTS (
        SELECT * FROM information_schema.COLUMNS 
        WHERE TABLE_SCHEMA = 'priorityiq' 
        AND TABLE_NAME = 'users' 
        AND COLUMN_NAME = 'role'
    ) THEN
        ALTER TABLE users ADD COLUMN role VARCHAR(50) AFTER phone;
    END IF;

    -- Check and add age column
    IF NOT EXISTS (
        SELECT * FROM information_schema.COLUMNS 
        WHERE TABLE_SCHEMA = 'priorityiq' 
        AND TABLE_NAME = 'users' 
        AND COLUMN_NAME = 'age'
    ) THEN
        ALTER TABLE users ADD COLUMN age INT AFTER role;
    END IF;

    -- Check and add gender column
    IF NOT EXISTS (
        SELECT * FROM information_schema.COLUMNS 
        WHERE TABLE_SCHEMA = 'priorityiq' 
        AND TABLE_NAME = 'users' 
        AND COLUMN_NAME = 'gender'
    ) THEN
        ALTER TABLE users ADD COLUMN gender VARCHAR(10) AFTER age;
    END IF;
END$$

DELIMITER ;

-- Execute the procedure
CALL AddColumnsIfNotExists();

-- Drop the procedure
DROP PROCEDURE AddColumnsIfNotExists;

-- Show final structure
DESCRIBE users;

-- Optional: View existing users
SELECT * FROM users;
