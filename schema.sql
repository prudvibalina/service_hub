-- ============================================================
--  Service Hub  –  MySQL Database Setup
--  Run once:  mysql -u root -p < schema.sql
-- ============================================================

CREATE DATABASE IF NOT EXISTS service_hub
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE service_hub;

-- ── Users (customers) ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    name       VARCHAR(100)  NOT NULL,
    username   VARCHAR(50)   NOT NULL UNIQUE,
    password   VARCHAR(64)   NOT NULL,        -- SHA-256 hex
    location   VARCHAR(100)  NOT NULL,
    mobile     VARCHAR(15)   NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ── Workers (service providers) ──────────────────────────────
CREATE TABLE IF NOT EXISTS workers (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    name       VARCHAR(100)  NOT NULL,
    profession ENUM('Electrician','Plumber','Carpenter','Mechanic') NOT NULL,
    experience TINYINT UNSIGNED NOT NULL DEFAULT 0,
    location   VARCHAR(100)  NOT NULL,
    mobile     VARCHAR(15)   NOT NULL,
    rating     DECIMAL(2,1)  NOT NULL DEFAULT 4.5,
    available  TINYINT(1)    NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ── Bookings ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS bookings (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT          NOT NULL,
    worker_id   INT          NOT NULL,
    service     VARCHAR(100) NOT NULL,
    description TEXT,
    status      ENUM('pending','confirmed','completed','cancelled')
                             NOT NULL DEFAULT 'pending',
    booked_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id)   REFERENCES users(id)   ON DELETE CASCADE,
    FOREIGN KEY (worker_id) REFERENCES workers(id) ON DELETE CASCADE
);

-- ── Sample data ───────────────────────────────────────────────
-- Password for all demo users: password123
-- SHA-256('password123') = ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f

INSERT IGNORE INTO users (name, username, password, location, mobile) VALUES
  ('Alice Johnson',  'alice',   'alice123', 'Mumbai',    '9876543210'),
  ('Bob Smith',      'bob',     'bob456', 'Delhi',     '9876543211'),
  ('Carol Williams', 'carol',   'carol789', 'Bangalore', '9876543212');

INSERT IGNORE INTO workers (name, profession, experience, location, mobile, rating) VALUES
  ('Ravi Kumar',    'Electrician', 8,  'Mumbai',    '9911001101', 4.8),
  ('Suresh Patil',  'Electrician', 5,  'Pune',      '9911001102', 4.6),
  ('Mohan Das',     'Plumber',     10, 'Mumbai',    '9911001103', 4.9),
  ('Ajay Singh',    'Plumber',     3,  'Delhi',     '9911001104', 4.3),
  ('Vikram Rao',    'Carpenter',   7,  'Bangalore', '9911001105', 4.7),
  ('Deepak Sharma', 'Carpenter',   4,  'Chennai',   '9911001106', 4.5),
  ('Arun Mehta',    'Mechanic',    6,  'Hyderabad', '9911001107', 4.6),
  ('Sanjay Tiwari', 'Mechanic',    9,  'Mumbai',    '9911001108', 4.8);
