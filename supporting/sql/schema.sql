-- WORLDS_DB schema
-- SQLite DDL extracted from /Users/lentulus/databases/world.db
-- Keep this in sync with any migrations applied to the live database.

CREATE TABLE hull_sizes (
    sm INTEGER PRIMARY KEY,
    mass_tons INTEGER NOT NULL,
    length_yards INTEGER NOT NULL,
    dst_hp INTEGER NOT NULL,
    handling INTEGER NOT NULL,
    stability_rating INTEGER NOT NULL
);

CREATE TABLE design_bureaus (
    bureau_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    short_code TEXT,
    notes TEXT
);

CREATE TABLE ship_types (
    type_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    military INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE ship_fates (
    fate_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    notes TEXT
);

CREATE TABLE design_features (
    feature_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    feature_type TEXT NOT NULL CHECK(feature_type IN ('feature','switch')),
    tl_min INTEGER,
    is_superscience INTEGER NOT NULL DEFAULT 0,
    description TEXT
);

CREATE TABLE ships (
    ship_id INTEGER PRIMARY KEY,
    hull_number TEXT,
    name TEXT,
    class_name TEXT,
    type_id INTEGER REFERENCES ship_types(type_id),
    bureau_id INTEGER REFERENCES design_bureaus(bureau_id),
    parent_ship_id INTEGER REFERENCES ships(ship_id),
    tl INTEGER NOT NULL,
    is_superscience INTEGER NOT NULL DEFAULT 0,
    sm INTEGER NOT NULL REFERENCES hull_sizes(sm),
    is_streamlined INTEGER NOT NULL DEFAULT 0,
    dst_hp INTEGER,
    handling INTEGER,
    stability_rating INTEGER,
    ht INTEGER,
    move_accel_g REAL,
    move_delta_v_mps REAL,
    move_is_ftl INTEGER NOT NULL DEFAULT 0,
    move_atm_only INTEGER NOT NULL DEFAULT 0,
    lwt_tons REAL,
    load_tons REAL,
    occ_crew INTEGER,
    occ_passengers INTEGER,
    occ_has_artificial_grav INTEGER NOT NULL DEFAULT 0,
    occ_is_short_voyage INTEGER NOT NULL DEFAULT 0,
    ddr_front INTEGER,
    ddr_central INTEGER,
    ddr_rear INTEGER,
    range_ftl TEXT,
    cost_dollars REAL,
    date_laid_down INTEGER,
    date_commissioned INTEGER,
    date_removed INTEGER,
    fate_id INTEGER REFERENCES ship_fates(fate_id),
    notes TEXT,
    description TEXT,
    image_path TEXT
);

CREATE TABLE ship_design_features (
    id INTEGER PRIMARY KEY,
    ship_id INTEGER NOT NULL REFERENCES ships(ship_id),
    feature_id INTEGER NOT NULL REFERENCES design_features(feature_id),
    notes TEXT
);

CREATE TABLE ship_system_catalog (
    system_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    tl_min INTEGER,
    is_superscience INTEGER NOT NULL DEFAULT 0,
    location TEXT NOT NULL DEFAULT 'ANY',
    is_high_energy INTEGER NOT NULL DEFAULT 0,
    repair_skill TEXT,
    notes TEXT
);

CREATE TABLE ship_system_slots (
    slot_id INTEGER PRIMARY KEY,
    ship_id INTEGER NOT NULL REFERENCES ships(ship_id),
    hull_section TEXT NOT NULL CHECK(hull_section IN ('front','central','rear')),
    slot_number INTEGER,
    slot_to INTEGER,
    is_core INTEGER NOT NULL DEFAULT 0,
    is_high_energy INTEGER NOT NULL DEFAULT 0,
    system_id INTEGER REFERENCES ship_system_catalog(system_id),
    detail TEXT
);

CREATE TABLE system_sm_stats (
    stat_id INTEGER PRIMARY KEY,
    system_id INTEGER NOT NULL REFERENCES ship_system_catalog(system_id),
    sm INTEGER NOT NULL,
    workspaces INTEGER,
    cost_dollars REAL,
    capacity_tons REAL,
    launch_rate_tons REAL,
    fuel_tons REAL,
    seats INTEGER,
    cabins INTEGER,
    areas INTEGER,
    control_stations INTEGER,
    computer_complexity INTEGER,
    comm_sensor_level_offset INTEGER,
    power_points INTEGER,
    acceleration_g REAL,
    delta_v_mps_per_tank REAL,
    output_per_hour_dollars REAL,
    output_per_hour_lbs REAL,
    mining_tons_per_hour REAL,
    refinery_tons_per_hour REAL,
    max_tonnage REAL,
    force_screen_ddr INTEGER,
    cost_variant TEXT,
    stat_notes TEXT,
    UNIQUE(system_id, sm, cost_variant)
);

CREATE TABLE armor_sm_stats (
    stat_id INTEGER PRIMARY KEY,
    system_id INTEGER NOT NULL REFERENCES ship_system_catalog(system_id),
    sm INTEGER NOT NULL,
    ddr_us INTEGER,
    ddr_sl INTEGER,
    cost_dollars REAL,
    UNIQUE(system_id, sm)
);
