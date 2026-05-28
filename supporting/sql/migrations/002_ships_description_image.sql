-- Migration 002: add description and image_path columns to ships
--
-- SQLite supports ADD COLUMN for nullable columns with no default,
-- so no table recreation is needed. Existing rows get NULL in both columns.
--
-- Apply with:
--   sqlite3 /Users/lentulus/databases/world.db < 002_ships_description_image.sql

ALTER TABLE ships ADD COLUMN description TEXT;
ALTER TABLE ships ADD COLUMN image_path  TEXT;
