-- Update users table to include registration fields

ALTER TABLE users 
ADD COLUMN phone VARCHAR(15) AFTER email,
ADD COLUMN role VARCHAR(50) AFTER phone,
ADD COLUMN age INT AFTER role,
ADD COLUMN gender VARCHAR(10) AFTER age;

-- Make phone unique
ALTER TABLE users ADD UNIQUE KEY unique_phone (phone);
