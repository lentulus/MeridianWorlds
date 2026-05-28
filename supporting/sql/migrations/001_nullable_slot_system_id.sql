-- Migration 001: make ship_system_slots.system_id nullable
--
-- SQLite does not support ALTER COLUMN, so the table is recreated.
-- The only change from the original DDL is removing NOT NULL from system_id.
-- Row data is preserved exactly; row count must be identical before and after.
--
-- Apply with:
--   sqlite3 /Users/lentulus/databases/world.db < 001_nullable_slot_system_id.sql

PRAGMA foreign_keys = OFF;

CREATE TABLE ship_system_slots_new (
    slot_id          INTEGER PRIMARY KEY,
    ship_id          INTEGER NOT NULL REFERENCES ships(ship_id),
    hull_section     TEXT    NOT NULL CHECK(hull_section IN ('front','central','rear')),
    slot_number      INTEGER,
    slot_to          INTEGER,
    is_core          INTEGER NOT NULL DEFAULT 0,
    is_high_energy   INTEGER NOT NULL DEFAULT 0,
    system_id        INTEGER REFERENCES ship_system_catalog(system_id),  -- nullable
    detail           TEXT
);

INSERT INTO ship_system_slots_new
    SELECT slot_id, ship_id, hull_section, slot_number, slot_to,
           is_core, is_high_energy, system_id, detail
    FROM ship_system_slots;

DROP TABLE ship_system_slots;
ALTER TABLE ship_system_slots_new RENAME TO ship_system_slots;

PRAGMA foreign_keys = ON;
