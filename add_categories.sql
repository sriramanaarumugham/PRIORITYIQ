-- Add category/tags support to tasks

USE priorityiq;

-- Add category column
ALTER TABLE tasks ADD COLUMN category VARCHAR(50) AFTER priority_level;

-- Show updated structure
DESCRIBE tasks;
