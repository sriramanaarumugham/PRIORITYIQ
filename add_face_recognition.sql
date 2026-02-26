-- Add face recognition data to users table

USE priorityiq;

-- Add column for storing face descriptor
ALTER TABLE users ADD COLUMN face_data TEXT AFTER gender;

-- Show updated structure
DESCRIBE users;
