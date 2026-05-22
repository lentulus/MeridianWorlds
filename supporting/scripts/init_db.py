#!/usr/bin/env python3
"""Create world.db schema and seed GURPS Spaceships 1 data."""

import sqlite3, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config import WORLDS_DB

# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------
SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS hull_sizes (
    sm INTEGER PRIMARY KEY,
    mass_tons INTEGER NOT NULL,
    length_yards INTEGER NOT NULL,
    dst_hp INTEGER NOT NULL,
    handling INTEGER NOT NULL,
    stability_rating INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS design_bureaus (
    bureau_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    short_code TEXT,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS ship_types (
    type_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    military INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS ship_fates (
    fate_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS design_features (
    feature_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    feature_type TEXT NOT NULL CHECK(feature_type IN ('feature','switch')),
    tl_min INTEGER,
    is_superscience INTEGER NOT NULL DEFAULT 0,
    description TEXT
);

CREATE TABLE IF NOT EXISTS ships (
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
    notes TEXT
);

CREATE TABLE IF NOT EXISTS ship_design_features (
    id INTEGER PRIMARY KEY,
    ship_id INTEGER NOT NULL REFERENCES ships(ship_id),
    feature_id INTEGER NOT NULL REFERENCES design_features(feature_id),
    notes TEXT
);

CREATE TABLE IF NOT EXISTS ship_system_catalog (
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

CREATE TABLE IF NOT EXISTS ship_system_slots (
    slot_id INTEGER PRIMARY KEY,
    ship_id INTEGER NOT NULL REFERENCES ships(ship_id),
    hull_section TEXT NOT NULL CHECK(hull_section IN ('front','central','rear')),
    slot_number INTEGER,
    slot_to INTEGER,
    is_core INTEGER NOT NULL DEFAULT 0,
    is_high_energy INTEGER NOT NULL DEFAULT 0,
    system_id INTEGER NOT NULL REFERENCES ship_system_catalog(system_id),
    detail TEXT
);

CREATE TABLE IF NOT EXISTS system_sm_stats (
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

CREATE TABLE IF NOT EXISTS armor_sm_stats (
    stat_id INTEGER PRIMARY KEY,
    system_id INTEGER NOT NULL REFERENCES ship_system_catalog(system_id),
    sm INTEGER NOT NULL,
    ddr_us INTEGER,
    ddr_sl INTEGER,
    cost_dollars REAL,
    UNIQUE(system_id, sm)
);
"""

# ---------------------------------------------------------------------------
# System catalog IDs (named constants for readable slot data)
# ---------------------------------------------------------------------------
ARM_ICE=1; ARM_STONE=2; ARM_STEEL=3; ARM_LIGHT_ALLOY=4; ARM_METALLIC_LAM=5
ARM_ADV_METALLIC=6; ARM_NANOCOMPOSITE=7; ARM_ORGANIC=8; ARM_DIAMONDOID=9
ARM_EXOTIC_LAM=10
CARGO_HOLD=11; PASSENGER_SEATING=12; HABITAT=13; OPEN_SPACE=14; HANGAR_BAY=15
CONTROL_ROOM=16; ENGINE_ROOM=17; ARRAY_ENHANCED=18; ARRAY_SCIENCE=19
ARRAY_TACTICAL=20; ARRAY_MULTIPURPOSE=21; DEFENSIVE_ECM=22; EXT_CLAMP=23
ROBOT_ARM=24; ROBOT_LEG=25; CLOAKING=26
PP_FUEL_CELL=27; PP_MHD_TURBINE=28; PP_FISSION=29; PP_FUSION=30
PP_ANTIMATTER=31; PP_SUPER_FUSION=32; PP_TOTAL_CONV=33
SOLAR_PANEL=34; RAMSCOOP=35
RE_CHEMICAL=36; RE_HEDM=37; RE_ION=38; RE_MASS_DRIVER=39; RE_NTR=40
RE_NUCLEAR_LIGHT_BULB=41; RE_NUCLEAR_SALTWATER=42; RE_ORION=43
RE_FUSION_PULSE=44; RE_ADV_FUSION_PULSE=45; RE_SUPER_FUSION_PULSE=46
RE_FUSION_ROCKET=47; RE_FUSION_TORCH=48; RE_SUPER_FUSION_TORCH=49
RE_AM_THERMAL=50; RE_AM_PLASMA=51; RE_AM_PLASMA_TORCH=52
RE_SUPER_AM_PLASMA_TORCH=53; RE_AM_PION=54; RE_AM_PION_TORCH=55
RE_TOTAL_CONV_TORCH=56; RE_SUPER_CONV_TORCH=57
RLS_ROTARY=58; RLS_STANDARD=59; RLS_HOT=60; RLS_SUPER=61; RLS_SUBWARP=62
FTL_STARDRIVE=63; FTL_SUPER_STARDRIVE=64; FTL_JUMP_GATE=65
WPN_MAJOR=66; WPN_MEDIUM=67; WPN_SECONDARY=68; WPN_TERTIARY=69; WPN_SPINAL=70
IND_FABRICATOR=71; IND_ROBOFAC=72; IND_NANOFACTORY=73; IND_REPLICATOR=74
IND_MINING=75; IND_REFINERY=76
FUEL_TANK=77; JET_ENGINE=78; SOFT_LANDING=79; SAIL_LIGHT=80; SAIL_MAG=81
UPPER_STAGE=82; RECONFIGURABLE=83
SC_CONTRAGRAV=84; SC_FORCE_SCREEN_LIGHT=85; SC_FORCE_SCREEN_HEAVY=86
SC_STASIS_WEB=87


def create_schema(conn):
    conn.executescript(SCHEMA)


def populate_reference(conn):
    conn.executemany("INSERT OR IGNORE INTO hull_sizes VALUES (?,?,?,?,?,?)", [
        (5,  30,       15,  20,  0, 4),
        (6,  100,      20,  30,  0, 4),
        (7,  300,      30,  50, -1, 5),
        (8,  1000,     50,  70, -1, 5),
        (9,  3000,     70, 100, -1, 5),
        (10, 10000,   100, 150, -2, 5),
        (11, 30000,   150, 200, -2, 5),
        (12, 100000,  200, 300, -2, 5),
        (13, 300000,  300, 500, -3, 5),
        (14, 1000000, 500, 700, -3, 5),
        (15, 3000000, 700,1000, -3, 5),
    ])

    conn.execute("INSERT OR IGNORE INTO design_bureaus VALUES (1,'GURPS Spaceships Index','SS-INDEX','Ships from the GURPS Spaceships rulebook series. Date fields set to 0 — pre-date campaign epoch.')")

    conn.executemany("INSERT OR IGNORE INTO ship_types VALUES (?,?,?)", [
        (1,  'Tramp Freighter',    0),
        (2,  'Orbital Shuttle',    0),
        (3,  'Freight Liner',      0),
        (4,  'Passenger Liner',    0),
        (5,  'Sunjammer',          0),
        (6,  'Yacht',              0),
        (7,  'Launch Vehicle',     0),
        (8,  'Shuttle/Lighter',    0),
        (9,  'Courier/Speedster',  0),
        (10, 'Orbital Transfer',   0),
        (11, 'Battleship',         1),
        (12, 'Heavy Cruiser',      1),
        (13, 'Space Cruiser',      1),
        (14, 'Strike Cruiser',     1),
        (15, 'Battle Cruiser',     1),
        (16, 'Frontier Cruiser',   1),
        (17, 'Space Patrol',       1),
        (18, 'Frigate',            1),
        (19, 'Patrol Ship',        1),
        (20, 'Corsair',            1),
        (21, 'Battle Station',     1),
        (22, 'Fighter',            1),
        (23, 'Assault Carrier',    1),
        (24, 'Assault Corvette',   1),
        (25, 'Drop Ship',          1),
        (26, 'Fleet Carrier',      1),
        (27, 'Super Carrier',      1),
        (28, 'Boarding Ship',      1),
        (29, 'Assault Boat',       1),
        (30, 'Grappler Ship',      1),
        (31, 'Light Carrier',      1),
        (32, 'Strike Carrier',     1),
        (33, 'Mecha',              1),
        (34, 'Assault Pod',        1),
        (35, 'Space Probe',        0),
        (36, 'Deep Space Probe',   0),
        (37, 'Exploration Ship',   0),
        (38, 'Armored Scout',      1),
        (39, 'Lander',             0),
        (40, 'Survey Ship',        0),
        (41, 'Colony Ship',        0),
        (42, 'Generation Ship',    0),
        (43, 'Space Station',      0),
        (44, 'Mining Ship',        0),
        (45, 'Tanker',             0),
        (46, 'Tug',                0),
        (47, 'Factory Ship',       0),
    ])

    conn.executemany("INSERT OR IGNORE INTO ship_fates VALUES (?,?,?)", [
        (1, 'Scrapped',         None),
        (2, 'Lost in combat',   None),
        (3, 'Lost — accident',  None),
        (4, 'Converted',        'Role or configuration change'),
        (5, 'Mothballed',       'Held in reserve'),
        (6, 'Captured',         None),
        (7, 'Expended',         'Deliberately destroyed or used as weapon/decoy'),
        (8, 'Unknown',          None),
    ])

    conn.executemany("INSERT OR IGNORE INTO design_features VALUES (?,?,?,?,?,?)", [
        (1, 'Artificial Gravity', 'feature', None, 1,
            'Provides shipboard gravity equivalent to 1G. Crew suffer no zero-G penalties. Denoted ASV in Occ stat.'),
        (2, 'Winged',             'feature', 7,    0,
            'Aerodynamic lifting surfaces. Required for atmospheric gliding and landing. Gives separate air Handling/SR.'),
        (3, 'Sealed',             'switch',  7,    0,
            'Hull is fully airtight with airlocks. Standard for spacecraft.'),
        (4, 'Automation',         'switch',  7,    0,
            'Reduces or eliminates workspace requirements. Cost varies.'),
        (5, 'Exposed Radiators',  'switch',  7,    0,
            'Ship radiates waste heat efficiently but radiators are a combat vulnerability.'),
    ])


def populate_system_catalog(conn):
    rows = [
        # Armor
        (ARM_ICE,           'Armor, Ice',                        'Armor',             0,  0, 'HULL', 0, 'Armoury (Vehicle Armor) −4',  'Semi-ablative. Not for SM+5–7 or streamlined hulls. Cost negligible.'),
        (ARM_STONE,         'Armor, Stone',                      'Armor',             0,  0, 'HULL', 0, 'Masonry',                      'Semi-ablative. Not for SM+5–6 or streamlined hulls. Cost negligible.'),
        (ARM_STEEL,         'Armor, Steel',                      'Armor',             7,  0, 'HULL', 0, 'Armoury (Vehicle Armor)',       None),
        (ARM_LIGHT_ALLOY,   'Armor, Light Alloy',                'Armor',             7,  0, 'HULL', 0, 'Armoury (Vehicle Armor)',       'Aerospace-grade aluminium or titanium alloys.'),
        (ARM_METALLIC_LAM,  'Armor, Metallic Laminate',          'Armor',             8,  0, 'HULL', 0, 'Armoury (Vehicle Armor)',       'Titanium/aluminium/beryllium with carbon or ceramic fibres.'),
        (ARM_ADV_METALLIC,  'Armor, Advanced Metallic Laminate', 'Armor',             9,  0, 'HULL', 0, 'Armoury (Vehicle Armor)',       'Carbon nanotubes or boron nanotubes reinforce the alloy.'),
        (ARM_NANOCOMPOSITE, 'Armor, Nanocomposite',              'Armor',            10,  0, 'HULL', 0, 'Armoury (Vehicle Armor)',       'Ultra-strength carbon/boron nanotube-reinforced polymers.'),
        (ARM_ORGANIC,       'Armor, Organic',                    'Armor',            10,  0, 'HULL', 0, 'Carpentry / Biotechnology',     'Low-cost biotech: space-adapted wood, living tissue, living bioplastic. DR halved vs burning/corrosion.'),
        (ARM_DIAMONDOID,    'Armor, Diamondoid',                 'Armor',            11,  0, 'HULL', 0, 'Armoury (Vehicle Armor)',       'Nano-fabricated diamondoid, fullerites, or cubic boron nitride.'),
        (ARM_EXOTIC_LAM,    'Armor, Exotic Laminate',            'Armor',            12,  0, 'HULL', 0, 'Armoury (Vehicle Armor)',       'Ultra-hard materials with high-density exotic matter laminate.'),
        # Cargo & Payload
        (CARGO_HOLD,        'Cargo Hold',                        'Cargo',             7,  0, 'ANY',  0, 'Mechanic (Vehicle Type)',       'Options: Refrigerated (+$0.5K/ton), Shielded (0.5t shielded per ton sacrificed, +$4K/ton).'),
        (PASSENGER_SEATING, 'Passenger Seating',                 'Cargo',             7,  0, 'ANY',  0, 'Mechanic (Life Support)',       'Airliner seats with 24h limited life support.'),
        (HABITAT,           'Habitat',                           'Cargo',             7,  0, 'ANY',  0, 'Mechanic (Life Support)',       'Long-term quarters. Cabins exchangeable 1:1 for bunkrooms/cells; luxury cabin=2 cabins; 1 cabin=5t steerage cargo.'),
        (OPEN_SPACE,        'Open Space',                        'Cargo',             7,  0, 'ANY',  0, 'Housekeeping / Gardening',      'Pressurised hall: auditorium, farm, pool, garden. 20 areas = 1 acre. Can provide food.'),
        (HANGAR_BAY,        'Hangar Bay',                        'Cargo',             7,  0, 'HULL', 0, 'Mechanic (Vehicle Type)',       'Stores/launches/recovers craft. Can also carry roll-on/roll-off cargo.'),
        # Control & Sensors
        (CONTROL_ROOM,      'Control Room',                      'Control',           7,  0, 'ANY',  0, 'Electronics Repair (Computers)', 'Includes basic comm/sensor array and hardened computer network.'),
        (ENGINE_ROOM,       'Engine Room',                       'Control',           7,  0, 'ANY',  0, 'Mechanic (Vehicle Type)',        'Tools and parts for maintenance. Not required SM+10+. Lowers HT if absent on SM+5–9.'),
        (ARRAY_ENHANCED,    'Comm/Sensor Array, Enhanced',       'Control',           7,  0, 'HULL', 0, 'Electronics Repair (Comm/Sensors)', 'Larger multi-function phased array. Cost 1× base.'),
        (ARRAY_SCIENCE,     'Comm/Sensor Array, Science',        'Control',           7,  0, 'HULL', 0, 'Electronics Repair (Comm/Sensors)', 'Adds astronomical and physics survey instruments. Cost 5× base.'),
        (ARRAY_TACTICAL,    'Comm/Sensor Array, Tactical',       'Control',           7,  0, 'HULL', 0, 'Electronics Repair (Comm/Sensors)', 'Active jamming; can overcome Defensive ECM. Cost 5× base.'),
        (ARRAY_MULTIPURPOSE,'Comm/Sensor Array, Multipurpose',   'Control',           7,  0, 'HULL', 0, 'Electronics Repair (Comm/Sensors)', 'Combines science and tactical functions. Cost 10× base.'),
        (DEFENSIVE_ECM,     'Defensive ECM',                     'Control',           7,  0, 'ANY',  0, 'Electronics Repair (EW)',       '−2 to ranged attacks on vessel. Max 3 installed. Only vs same-or-lower TL attackers.'),
        (EXT_CLAMP,         'External Clamp',                    'Control',           7,  0, 'HULL', 0, 'Mechanic (Vehicle Type)',       'Grapples and attaches to another vessel or object.'),
        (ROBOT_ARM,         'Robot Arm',                         'Control',           8,  0, 'HULL', 0, 'Mechanic (Robotics)',            None),
        (ROBOT_LEG,         'Robot Leg',                         'Control',           9,  0, 'HULL', 1, 'Mechanic (Robotics)',            'High-energy. Allows walking on surfaces.'),
        (CLOAKING,          'Cloaking Device',                   'Control',        None,  1, 'ANY',  1, 'Electronics Repair (EW)',       'Superscience stealth. −10 to detection. Deactivates if weapons fired or reaction drive used.'),
        # Power
        (PP_FUEL_CELL,      'Power Plant, Fuel Cell',            'Power',             7,  0, 'ANY',  0, 'Mechanic (Fuel Cell)',          'Provides 1 PP. Internal fuel: 3h (TL7), 8h (TL8), 12h (TL9), 24h (TL10+).'),
        (PP_MHD_TURBINE,    'Power Plant, MHD Turbine',          'Power',             9,  0, 'ANY',  0, 'Mechanic (MHD Turbine)',        'Provides 2 PP. Internal fuel: 6h (TL9), 12h (TL10+). Double fuel cell cost.'),
        (PP_FISSION,        'Power Plant, Fission Reactor',      'Power',             8,  0, 'ANY',  0, 'Mechanic (Fission)',            'Provides 1 PP. Fuel: 25yr (TL8), 50yr (TL9), 75yr (TL10+).'),
        (PP_FUSION,         'Power Plant, Fusion Reactor',       'Power',             9,  0, 'ANY',  0, 'Mechanic (Fusion)',             'Provides 2 PP. Fuel: 50yr (TL9), 200yr (TL10), 600yr (TL11), 1500yr (TL12). Min SM+10 at TL9.'),
        (PP_ANTIMATTER,     'Power Plant, Antimatter Reactor',   'Power',            10,  0, 'ANY',  0, 'Mechanic (Antimatter)',         'Provides 4 PP. Internal fuel: 2yr (TL10), 20yr (TL11), 200yr (TL12). Explodes if damaged.'),
        (PP_SUPER_FUSION,   'Power Plant, Super Fusion Reactor', 'Power',            11,  0, 'ANY',  0, 'Mechanic (Fusion)',             'Provides 4 PP. Fuel: 400yr (TL11), 1000yr (TL12). Muon-catalysed or black hole catalysed.'),
        (PP_TOTAL_CONV,     'Power Plant, Total Conversion',     'Power',            12,  1, 'ANY',  0, 'Mechanic (Total Conversion)',   'Superscience. Provides 5 PP. Effectively unlimited endurance.'),
        (SOLAR_PANEL,       'Solar Panel Array',                 'Power',             7,  0, 'HULL', 0, 'Mechanic (Electrical)',         'Generates power from sunlight. Performance drops with distance from star.'),
        (RAMSCOOP,          'Ramscoop',                          'Power',            10,  0, 'FRONT',0, 'Mechanic (High-Performance Spacecraft)', 'Scoops interstellar hydrogen as reaction mass. Unlimited delta-V if fast enough.'),
        # Reaction Engines
        (RE_CHEMICAL,       'Reaction Engine, Chemical Rocket',  'Reaction Engine',   7,  0, 'REAR', 0, 'Mechanic (Rocket)',             None),
        (RE_HEDM,           'Reaction Engine, HEDM Rocket',      'Reaction Engine',   9,  0, 'REAR', 0, 'Mechanic (Rocket)',             'High-Energy Dense Matter propellant.'),
        (RE_ION,            'Reaction Engine, Ion Drive',        'Reaction Engine',   8,  0, 'REAR', 1, 'Mechanic (High-Performance Spacecraft)', 'High-energy. Low thrust, very high delta-V.'),
        (RE_MASS_DRIVER,    'Reaction Engine, Mass Driver',      'Reaction Engine',   9,  0, 'REAR', 1, 'Mechanic (High-Performance Spacecraft)', 'High-energy electromagnetic mass driver.'),
        (RE_NTR,            'Reaction Engine, Nuclear Thermal',  'Reaction Engine',   7,  0, 'REAR', 0, 'Mechanic (High-Performance Spacecraft)', None),
        (RE_NUCLEAR_LIGHT_BULB,'Reaction Engine, Nuclear Light Bulb','Reaction Engine',9, 0, 'REAR', 0, 'Mechanic (High-Performance Spacecraft)', None),
        (RE_NUCLEAR_SALTWATER,'Reaction Engine, Nuclear Saltwater','Reaction Engine',  9,  1, 'REAR', 0, 'Mechanic (High-Performance Spacecraft)', 'Superscience variant.'),
        (RE_ORION,          'Reaction Engine, Orion Pulse Drive','Reaction Engine',   7,  0, 'REAR', 0, 'Mechanic (High-Performance Spacecraft)', 'Nuclear pulse detonation. Politically sensitive.'),
        (RE_FUSION_PULSE,   'Reaction Engine, Fusion Pulse Drive','Reaction Engine',  9,  0, 'REAR', 0, 'Mechanic (High-Performance Spacecraft)', None),
        (RE_ADV_FUSION_PULSE,'Reaction Engine, Adv Fusion Pulse','Reaction Engine',   9,  0, 'REAR', 0, 'Mechanic (High-Performance Spacecraft)', None),
        (RE_SUPER_FUSION_PULSE,'Reaction Engine, Super Fusion Pulse','Reaction Engine',11, 1,'REAR', 0, 'Mechanic (High-Performance Spacecraft)', 'Superscience.'),
        (RE_FUSION_ROCKET,  'Reaction Engine, Fusion Rocket',    'Reaction Engine',   9,  0, 'REAR', 0, 'Mechanic (High-Performance Spacecraft)', None),
        (RE_FUSION_TORCH,   'Reaction Engine, Fusion Torch',     'Reaction Engine',  10,  1, 'REAR', 0, 'Mechanic (High-Performance Spacecraft)', 'Superscience. High thrust and delta-V.'),
        (RE_SUPER_FUSION_TORCH,'Reaction Engine, Super Fusion Torch','Reaction Engine',11,1,'REAR', 0, 'Mechanic (High-Performance Spacecraft)', 'Superscience.'),
        (RE_AM_THERMAL,     'Reaction Engine, Antimatter Thermal','Reaction Engine',  9,  0, 'REAR', 0, 'Mechanic (Antimatter)',          None),
        (RE_AM_PLASMA,      'Reaction Engine, Antimatter Plasma','Reaction Engine',  10,  0, 'REAR', 0, 'Mechanic (Antimatter)',          None),
        (RE_AM_PLASMA_TORCH,'Reaction Engine, Antimatter Plasma Torch','Reaction Engine',10,1,'REAR',0,'Mechanic (Antimatter)',          'Superscience.'),
        (RE_SUPER_AM_PLASMA_TORCH,'Reaction Engine, Super AM Plasma Torch','Reaction Engine',11,1,'REAR',0,'Mechanic (Antimatter)', 'Superscience.'),
        (RE_AM_PION,        'Reaction Engine, Antimatter Pion',  'Reaction Engine',  11,  0, 'REAR', 0, 'Mechanic (Antimatter)',          None),
        (RE_AM_PION_TORCH,  'Reaction Engine, Antimatter Pion Torch','Reaction Engine',11, 1,'REAR', 0, 'Mechanic (Antimatter)',          'Superscience.'),
        (RE_TOTAL_CONV_TORCH,'Reaction Engine, Total Conversion Torch','Reaction Engine',12,1,'REAR',0,'Mechanic (Total Conversion)',   'Superscience.'),
        (RE_SUPER_CONV_TORCH,'Reaction Engine, Super Conversion Torch','Reaction Engine',12,1,'REAR',0,'Mechanic (Total Conversion)',  'Superscience.'),
        # Reactionless Engines
        (RLS_ROTARY,        'Reactionless Engine, Rotary',       'Reactionless Engine',7, 1, 'REAR', 1, 'Mechanic (Contragravity)',      'Superscience Dean Drive.'),
        (RLS_STANDARD,      'Reactionless Engine, Standard',     'Reactionless Engine',10,1, 'REAR', 1, 'Mechanic (Contragravity)',      'Superscience. No reaction mass needed.'),
        (RLS_HOT,           'Reactionless Engine, Hot',          'Reactionless Engine',10,1, 'REAR', 1, 'Mechanic (Contragravity)',      'Superscience. Higher thrust variant.'),
        (RLS_SUPER,         'Reactionless Engine, Super',        'Reactionless Engine',11,1, 'REAR', 1, 'Mechanic (Contragravity)',      'Superscience.'),
        (RLS_SUBWARP,       'Reactionless Engine, Subwarp',      'Reactionless Engine',None,1,'REAR',1, 'Mechanic (Contragravity)',      'Superscience.'),
        # FTL
        (FTL_STARDRIVE,     'FTL, Stardrive Engine',             'FTL',            None,  1, 'ANY',  1, 'Mechanic (FTL)',                'Superscience. Hyperdrive, jump, or warp — GM chooses type.'),
        (FTL_SUPER_STARDRIVE,'FTL, Super Stardrive Engine',      'FTL',            None,  1, 'ANY',  1, 'Mechanic (FTL)',                'Superscience. Higher FTL rating.'),
        (FTL_JUMP_GATE,     'FTL, Jump Gate',                    'FTL',            None,  1, 'HULL', 1, 'Electronics Repair (MT)',       'Superscience. Fixed wormhole portal. Multiple in same section combine capacity.'),
        # Weapons
        (WPN_MAJOR,         'Weapon, Major Battery',             'Weapon',            7,  0, 'HULL', 1, None,                            'Turret or fixed mount. Largest shipboard weapons.'),
        (WPN_MEDIUM,        'Weapon, Medium Battery',            'Weapon',            7,  0, 'HULL', 1, None,                            None),
        (WPN_SECONDARY,     'Weapon, Secondary Battery',         'Weapon',            7,  0, 'HULL', 1, None,                            None),
        (WPN_TERTIARY,      'Weapon, Tertiary Battery',          'Weapon',            7,  0, 'HULL', 1, None,                            'Can sacrifice cargo capacity for weapons.'),
        (WPN_SPINAL,        'Weapon, Spinal Battery',            'Weapon',            7,  0, 'SPECIAL',1,None,                           'Runs the length of the ship spine. Special placement rules.'),
        # Industrial
        (IND_FABRICATOR,    'Industrial, Factory: Fabricator',   'Industrial',        8,  0, 'ANY',  1, 'Mechanic (Machine Tools)',      'High-tech machine shop. Needs component parts at 40% of good value.'),
        (IND_ROBOFAC,       'Industrial, Factory: Robofac',      'Industrial',       10,  0, 'ANY',  1, 'Mechanic (Robotics)',           'Self-operating fabricator. Machinist-14 skill. 2× fabricator cost.'),
        (IND_NANOFACTORY,   'Industrial, Factory: Nanofactory',  'Industrial',       11,  0, 'ANY',  1, 'Mechanic (Nanomachines)',       'Raw materials in, finished goods out. 4× fabricator cost.'),
        (IND_REPLICATOR,    'Industrial, Factory: Replicator',   'Industrial',       12,  1, 'ANY',  1, 'Electronics Repair (MT)',       'Superscience. Transmutes elements. 20× fabricator cost.'),
        (IND_MINING,        'Industrial, Mining System',         'Industrial',        7,  0, 'ANY',  1, 'Mechanic (Mining)',             'Extracts ore or converts ice/rock. Needs Mechanic (Mining) supervisor.'),
        (IND_REFINERY,      'Industrial, Chemical Refinery',     'Industrial',        7,  0, 'ANY',  1, 'Mechanic (Refineries)',         'Processes ice into hydrogen/oxygen rocket fuel.'),
        # Utility
        (FUEL_TANK,         'Fuel Tank',                         'Utility',           7,  0, 'ANY',  0, 'Mechanic (Vehicle Type)',       'Reaction mass for reaction drives. Delta-V multiplier for 6+ tanks.'),
        (JET_ENGINE,        'Jet Engine',                        'Utility',           7,  0, 'REAR', 0, 'Mechanic (Jet Engines)',        'Turbojet/scramjet. Atmosphere only (0.1+ atm). 1G per engine. Uses 1 fuel tank/half-hour (TL7) or hour (TL8+).'),
        (SOFT_LANDING,      'Soft-Landing System',               'Utility',           7,  0, 'HULL', 0, 'Mechanic (Vehicle Type)',       'Retrorockets or airbags for gentle planetary landing.'),
        (SAIL_LIGHT,        'Space Sails: Lightsail',            'Utility',           9,  0, 'HULL', 0, 'Mechanic (High-Performance Spacecraft)', 'Photon pressure. Laser-pushed variants reach near-c. Delta-V notation /c.'),
        (SAIL_MAG,          'Space Sails: Magsail',              'Utility',           9,  0, 'HULL', 0, 'Mechanic (High-Performance Spacecraft)', 'Magnetic braking on stellar wind. Useful for deceleration. Delta-V notation /c.'),
        (UPPER_STAGE,       'Upper Stage',                       'Utility',           7,  0, 'SPECIAL',0,'Mechanic (Vehicle Type)',      'A complete spacecraft in the front hull of a multi-stage vehicle.'),
        (RECONFIGURABLE,    'Reconfigurable System',             'Utility',          11,  1, 'SPECIAL',0,'Mechanic (Vehicle Type)',      'Superscience. Can change function between missions.'),
        # Superscience
        (SC_CONTRAGRAV,     'Contragravity Lifter',              'Superscience',   None,  1, 'ANY',  1, 'Mechanic (Contragravity)',      'Nullifies local gravity. Treated as reactionless drive. Can land/take off from any normal planet up to 10G.'),
        (SC_FORCE_SCREEN_LIGHT,'Force Screen, Light',            'Superscience',     11,  1, 'ANY',  1, 'Armoury (Force Shields)',       'Semi-ablative dDR around entire vessel. Regenerates 10% lost dDR/second while powered.'),
        (SC_FORCE_SCREEN_HEAVY,'Force Screen, Heavy',            'Superscience',     12,  1, 'ANY',  1, 'Armoury (Force Shields)',       'Can use 2nd PP to double dDR. Otherwise same as light screen.'),
        (SC_STASIS_WEB,     'Stasis Web',                        'Superscience',     12,  1, 'ANY',  1, None,                            'Superscience. Freezes target in stasis field.'),
    ]
    conn.executemany(
        "INSERT OR IGNORE INTO ship_system_catalog VALUES (?,?,?,?,?,?,?,?,?)",
        rows
    )


def populate_armor_stats(conn):
    # (system_id, sm, ddr_us, ddr_sl, cost_dollars)
    # ddr_sl=None means not available streamlined; cost=0 means negligible
    rows = []

    # Ice — only SM+8 to +15, no streamlined version
    for sm, us in zip(range(8,16), [1,2,3,5,7,10,15,20]):
        rows.append((ARM_ICE, sm, us, None, 0))

    # Stone — only SM+7 to +15, no streamlined version
    for sm, us in zip(range(7,16), [1,2,2,3,5,7,10,15,20]):
        rows.append((ARM_STONE, sm, us, None, 0))

    # Steel
    for sm, us, sl, cost in zip(range(5,16),
        [1,2,3,5,7,10,15,20,30,50,70],
        [None,1,2,3,5,7,10,15,20,30,50],
        [6e3,20e3,60e3,200e3,600e3,2e6,6e6,20e6,60e6,200e6,600e6]):
        rows.append((ARM_STEEL, sm, us, sl, cost))

    # Light Alloy
    for sm, us, sl, cost in zip(range(5,16),
        [2,3,5,7,10,15,20,30,50,70,100],
        [1,2,3,5,7,10,15,20,30,50,70],
        [15e3,50e3,150e3,500e3,1.5e6,5e6,15e6,50e6,150e6,500e6,1.5e9]):
        rows.append((ARM_LIGHT_ALLOY, sm, us, sl, cost))

    # Metallic Laminate
    for sm, us, sl, cost in zip(range(5,16),
        [3,5,7,10,15,20,30,50,70,100,150],
        [2,3,5,7,10,15,20,30,50,70,100],
        [30e3,100e3,300e3,1e6,3e6,10e6,30e6,100e6,300e6,1e9,3e9]):
        rows.append((ARM_METALLIC_LAM, sm, us, sl, cost))

    # Advanced Metallic Laminate
    for sm, us, sl, cost in zip(range(5,16),
        [5,7,10,15,20,30,50,70,100,150,200],
        [3,5,7,10,15,20,30,50,70,100,150],
        [60e3,200e3,600e3,2e6,6e6,20e6,60e6,200e6,600e6,2e9,6e9]):
        rows.append((ARM_ADV_METALLIC, sm, us, sl, cost))

    # Nanocomposite
    for sm, us, sl, cost in zip(range(5,16),
        [7,10,15,20,30,50,70,100,150,200,300],
        [5,7,10,15,20,30,50,70,100,150,200],
        [150e3,500e3,1.5e6,5e6,15e6,50e6,150e6,500e6,1.5e9,5e9,15e9]):
        rows.append((ARM_NANOCOMPOSITE, sm, us, sl, cost))

    # Organic
    for sm, us, sl, cost in zip(range(5,16),
        [2,3,5,7,10,15,20,30,50,70,100],
        [1,2,3,5,7,10,15,20,30,50,70],
        [10e3,30e3,100e3,300e3,1e6,3e6,10e6,30e6,100e6,300e6,1e9]):
        rows.append((ARM_ORGANIC, sm, us, sl, cost))

    # Diamondoid
    for sm, us, sl, cost in zip(range(5,16),
        [10,15,20,30,50,70,100,150,200,300,500],
        [7,10,15,20,30,50,70,100,150,200,300],
        [300e3,1e6,3e6,10e6,30e6,100e6,300e6,1e9,3e9,10e9,30e9]):
        rows.append((ARM_DIAMONDOID, sm, us, sl, cost))

    # Exotic Laminate
    for sm, us, sl, cost in zip(range(5,16),
        [15,20,30,50,70,100,150,200,300,500,700],
        [10,15,20,30,50,70,100,150,200,300,500],
        [600e3,2e6,6e6,20e6,60e6,200e6,600e6,2e9,6e9,20e9,60e9]):
        rows.append((ARM_EXOTIC_LAM, sm, us, sl, cost))

    conn.executemany(
        "INSERT OR IGNORE INTO armor_sm_stats(system_id,sm,ddr_us,ddr_sl,cost_dollars) VALUES (?,?,?,?,?)",
        rows
    )


def populate_system_stats(conn):
    """Per-system SM stats for non-armor systems with known data (SS1 pp.13–20)."""
    rows = []

    def add(sid, sm, **kw):
        rows.append((sid, sm,
            kw.get('ws'), kw.get('cost'),
            kw.get('cap'), kw.get('launch'), kw.get('fuel'),
            kw.get('seats'), kw.get('cabins'), kw.get('areas'),
            kw.get('stations'), kw.get('complexity'), kw.get('csl_offset'),
            kw.get('pp'),
            kw.get('accel'), kw.get('dv'),
            kw.get('out_dollar'), kw.get('out_lbs'),
            kw.get('mining'), kw.get('refinery'),
            kw.get('max_ton'), kw.get('screen_ddr'),
            kw.get('variant'), kw.get('note'),
        ))

    # Cargo Hold (capacity in tons, cost negligible)
    for sm, cap in zip(range(5,16),[1.5,5,15,50,150,500,1500,5000,15000,50000,150000]):
        add(CARGO_HOLD, sm, ws=0, cost=0, cap=cap)

    # Passenger Seating
    for sm, seats, cost in zip(range(5,16),
        [2,6,20,60,200,600,2000,6000,20000,60000,200000],
        [10e3,30e3,100e3,300e3,1e6,3e6,10e6,30e6,100e6,300e6,1e9]):
        add(PASSENGER_SEATING, sm, ws=0, cost=cost, seats=seats)

    # Habitat (not available SM+5)
    for sm, cabins, ws, cost in zip(range(6,16),
        [1,2,6,20,60,200,600,2000,6000,20000],
        [0,0,0,0,1,3,10,30,100,300],
        [100e3,300e3,1e6,3e6,10e6,30e6,100e6,300e6,1e9,3e9]):
        add(HABITAT, sm, ws=ws, cost=cost, cabins=cabins)

    # Open Space (SM+8 to +15 only)
    for sm, areas, ws, cost in zip(range(8,16),
        [1,2,5,10,20,50,100,200],
        [0,0,1,3,10,30,100,300],
        [100e3,200e3,500e3,1e6,2e6,5e6,10e6,20e6]):
        add(OPEN_SPACE, sm, ws=ws, cost=cost, areas=areas)

    # Hangar Bay
    for sm, cap, launch, ws, cost in zip(range(5,16),
        [1,3,10,30,100,300,1000,3000,10000,30000,100000],
        [1,3,10,20,50,100,200,500,1000,2000,5000],
        [0,0,0,0,0,1,3,10,30,100,300],
        [3e3,10e3,30e3,100e3,300e3,1e6,3e6,10e6,30e6,100e6,300e6]):
        add(HANGAR_BAY, sm, ws=ws, cost=cost, cap=cap, launch=launch)

    # Control Room
    # complexity stored as numeric (e.g. 9 for C9), comm/sensor as offset from TL
    for sm, compl, csl, stations, ws, cost in zip(range(5,16),
        [6,7,7,8,8,9,9,10,10,11,11],
        [-6,-5,-4,-3,-2,-1,0,1,2,3,4],
        [1,2,3,4,6,10,15,20,30,40,60],
        [0,0,0,0,0,1,3,10,30,100,300],
        [60e3,200e3,600e3,2e6,6e6,20e6,60e6,200e6,600e6,2e9,6e9]):
        add(CONTROL_ROOM, sm, ws=ws, cost=cost,
            complexity=compl, csl_offset=csl, stations=stations)

    # Engine Room (SM+5 to +9 only; not needed SM+10+)
    for sm, ws, cost in zip(range(5,10),
        [1,1,1,1,2],
        [15e3,30e3,100e3,300e3,1e6]):
        add(ENGINE_ROOM, sm, ws=ws, cost=cost)

    # Enhanced Comm/Sensor Array (science=5×, tactical=5×, multipurpose=10× cost)
    for sm, csl, ws, base_cost in zip(range(5,16),
        [-4,-3,-2,-1,0,1,2,3,4,5,6],
        [0,0,0,0,0,1,3,10,30,100,300],
        [60e3,200e3,600e3,2e6,6e6,20e6,60e6,200e6,600e6,2e9,6e9]):
        add(ARRAY_ENHANCED,    sm, ws=ws, cost=base_cost,      csl_offset=csl)
        add(ARRAY_SCIENCE,     sm, ws=ws, cost=base_cost*5,    csl_offset=csl)
        add(ARRAY_TACTICAL,    sm, ws=ws, cost=base_cost*5,    csl_offset=csl)
        add(ARRAY_MULTIPURPOSE,sm, ws=ws, cost=base_cost*10,   csl_offset=csl)

    # Defensive ECM
    for sm, ws, cost in zip(range(5,16),
        [0,0,0,0,0,1,3,10,30,100,300],
        [300e3,1e6,3e6,10e6,30e6,100e6,300e6,1e9,3e9,10e9,30e9]):
        add(DEFENSIVE_ECM, sm, ws=ws, cost=cost)

    # External Clamp (no workspaces)
    for sm, cost in zip(range(5,16),
        [3e3,10e3,30e3,100e3,300e3,1e6,3e6,10e6,30e6,100e6,300e6]):
        add(EXT_CLAMP, sm, ws=0, cost=cost)

    # Cloaking Device
    for sm, ws, cost in zip(range(5,16),
        [0,0,0,0,0,1,3,10,30,100,300],
        [1e6,3e6,10e6,30e6,100e6,300e6,1e9,3e9,10e9,30e9,100e9]):
        add(CLOAKING, sm, ws=ws, cost=cost)

    # Contragravity Lifter
    for sm, ws, cost in zip(range(5,16),
        [0,0,0,0,0,1,3,10,30,100,300],
        [300e3,1e6,3e6,10e6,30e6,100e6,300e6,1e9,3e9,10e9,30e9]):
        add(SC_CONTRAGRAV, sm, ws=ws, cost=cost)

    # Force Screen (light and heavy stored as separate system_ids)
    for sm, ddr_l, ddr_h, ws, cost_l, cost_h in zip(range(5,16),
        [20,30,50,75,100,150,250,350,500,750,1000],
        [30,50,75,100,150,250,350,500,750,1000,1500],
        [0,0,0,0,0,1,3,10,30,100,300],
        [500e3,1.5e6,5e6,15e6,50e6,150e6,500e6,1.5e9,5e9,15e9,50e9],
        [1.5e6,5e6,15e6,50e6,150e6,500e6,1.5e9,5e9,15e9,50e9,150e9]):
        add(SC_FORCE_SCREEN_LIGHT, sm, ws=ws, cost=cost_l, screen_ddr=ddr_l)
        add(SC_FORCE_SCREEN_HEAVY, sm, ws=ws, cost=cost_h, screen_ddr=ddr_h)

    # Fuel Tank
    for sm, fuel, cost in zip(range(5,16),
        [1.5,5,15,50,150,500,1500,5000,15000,50000,150000],
        [10e3,30e3,100e3,300e3,1e6,3e6,10e6,30e6,100e6,300e6,1e9]):
        add(FUEL_TANK, sm, ws=0, cost=cost, fuel=fuel)

    # Jet Engine
    for sm, ws, cost in zip(range(5,16),
        [0,0,0,0,0,1,3,10,30,100,300],
        [300e3,1e6,3e6,10e6,30e6,100e6,300e6,1e9,3e9,10e9,30e9]):
        add(JET_ENGINE, sm, ws=ws, cost=cost)

    # Jump Gate (SM+9 to +15 only)
    for sm, max_ton, ws, cost in zip(range(9,16),
        [100,300,1000,3000,10000,30000,100000],
        [1,1,3,10,30,100,300],
        [150e6,500e6,1.5e9,5e9,50e9,150e9,500e9]):
        add(FTL_JUMP_GATE, sm, ws=ws, cost=cost, max_ton=max_ton)

    # Mining System and Chemical Refinery
    for sm, mine, ref, ws, cost in zip(range(5,16),
        [0.15,0.5,1.5,5,15,50,150,500,1500,5000,15000],
        [0.5,1.5,5,15,50,150,500,1500,5000,15000,50000],
        [0,0,0,0,0,1,3,10,30,100,300],
        [30e3,100e3,300e3,1e6,3e6,10e6,30e6,100e6,300e6,1e9,3e9]):
        add(IND_MINING,   sm, ws=ws, cost=cost, mining=mine)
        add(IND_REFINERY, sm, ws=ws, cost=cost, refinery=ref)

    # Factory: Fabricator (SM+6 to +15)
    for sm, out_d, out_l, ws, cost in zip(range(6,16),
        [5e3,15e3,50e3,150e3,500e3,1.5e6,5e6,15e6,150e6,500e6],
        [0.5,1.5,5,15,50,150,500,1500,5000,15000],
        [0,0,0,0,1,3,10,30,100,300],
        [5e6,15e6,50e6,150e6,500e6,1.5e9,5e9,15e9,50e9,150e9]):
        add(IND_FABRICATOR, sm, ws=ws, cost=cost, out_dollar=out_d, out_lbs=out_l)
        add(IND_ROBOFAC,    sm, ws=ws, cost=cost*2,  out_dollar=out_d*2,  out_lbs=out_l, note='Robofac: 2× fabricator cost/output')
        add(IND_NANOFACTORY,sm, ws=ws, cost=cost*4,  out_dollar=out_d*4,  out_lbs=out_l, note='Nanofactory: 4× fabricator cost/output')
        add(IND_REPLICATOR, sm, ws=ws, cost=cost*20, out_dollar=None, out_lbs=out_l, note='Replicator: lbs/hr from raw bulk matter')

    # Power Plant, Fuel Cell
    for sm, ws, cost in zip(range(5,16),
        [0,0,0,0,0,1,3,10,30,100,300],
        [15e3,50e3,1.5e6,5e6,15e6,50e6,150e6,500e6,1.5e9,5e9,15e9]):
        add(PP_FUEL_CELL,    sm, ws=ws, cost=cost,    pp=1)
        add(PP_MHD_TURBINE,  sm, ws=ws, cost=cost*2,  pp=2, note='MHD Turbine: 2× fuel cell cost')

    # Power Plant, Reactors
    for sm, ws, c_fis, c_fus, c_am, c_sf, c_tc in zip(range(5,16),
        [0,0,0,0,0,1,3,10,30,100,300],
        [100e3,300e3,1e6,3e6,10e6,30e6,100e6,300e6,1e9,3e9,10e9],
        [300e3,1e6,3e6,10e6,30e6,100e6,300e6,1e9,3e9,10e9,30e9],
        [600e3,2e6,6e6,20e6,60e6,200e6,600e6,2e9,6e9,20e9,60e9],
        [1e6,3e6,10e6,30e6,100e6,300e6,1e9,3e9,10e9,30e9,100e9],
        [2e6,6e6,20e6,60e6,200e6,600e6,2e9,6e9,20e9,60e9,200e9]):
        add(PP_FISSION,    sm, ws=ws, cost=c_fis, pp=1)
        add(PP_FUSION,     sm, ws=ws, cost=c_fus, pp=2)
        add(PP_ANTIMATTER, sm, ws=ws, cost=c_am,  pp=4)
        add(PP_SUPER_FUSION,sm,ws=ws, cost=c_sf,  pp=4)
        add(PP_TOTAL_CONV,  sm, ws=ws, cost=c_tc, pp=5)

    conn.executemany("""
        INSERT OR IGNORE INTO system_sm_stats
        (system_id,sm,workspaces,cost_dollars,capacity_tons,launch_rate_tons,
         fuel_tons,seats,cabins,areas,control_stations,computer_complexity,
         comm_sensor_level_offset,power_points,acceleration_g,delta_v_mps_per_tank,
         output_per_hour_dollars,output_per_hour_lbs,mining_tons_per_hour,
         refinery_tons_per_hour,max_tonnage,force_screen_ddr,cost_variant,stat_notes)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, rows)


def populate_ships(conn):
    BUREAU = 1  # SS-INDEX
    TYPE_FREIGHTER = 1
    TYPE_SHUTTLE   = 2

    STAR_FLOWER_NOTE = """\
Fast tramp freighter built for frontier operations in regions with primitive port facilities. \
Its reactionless drives produce enough thrust to lift from a planetary surface — making it \
independent of starport infrastructure. The class has a well-earned reputation for attracting \
smugglers, independent operators, and the occasional slaver.

> *"My first billet was chief engineer on the Rose of Rigel. The captain was a smuggler and a \
slaver — for some reason this class of ship tends to attract an unsavoury element."*
> — Captain Zeke Morrigan

**Crew (7):** Captain/navigator, pilot, chief engineer, comm/sensor operator (doubles as \
gunner when needed), engine room technician, steward, medic.

SM+8 streamlined hull; 1,000 tons loaded; 75 yards long. Equipped with artificial gravity. \
Top atmospheric speed 3,500 mph."""

    MIDNIGHT_SUN_STACK_NOTE = """\
Two-stage rocket designed to lift a crew from an Earth-gravity world to high orbit. \
The 300-ton first stage (booster) carries a 100-ton orbiter in its front hull. \
The booster falls away after accelerating the stack to 2.6 mps delta-V; the orbiter's \
own chemical engine adds a further 3.4 mps, giving a total delta-V of 6 mps — \
sufficient to reach low orbit.

> *"First time I went into space was aboard one of these relics, before they got the \
beanstalk up. 3G acceleration is not fun when you're five years old."*
> — Maya Bright

**Crew:** Pilot and co-pilot (in orbiter control room)."""

    MIDNIGHT_SUN_ORBITER_NOTE = """\
Second stage of the Midnight Sun stack; also operable as a standalone vehicle. \
Winged design feature gives full atmospheric flight capability (Air Handling/SR: +4/5). \
Carries 12 passengers in airliner seating plus 10 tons of cargo. \
Expendable fuel tanks (30 tons central hull + 30 tons rear hull) provide 3.4 mps delta-V."""

    ships = [
        # ship_id, hull_number, name, class_name, type_id, bureau_id, parent_ship_id,
        # tl, is_superscience, sm, is_streamlined, dst_hp, handling, stability_rating, ht,
        # move_accel_g, move_delta_v_mps, move_is_ftl, move_atm_only,
        # lwt_tons, load_tons,
        # occ_crew, occ_passengers, occ_has_artificial_grav, occ_is_short_voyage,
        # ddr_front, ddr_central, ddr_rear,
        # range_ftl, cost_dollars,
        # date_laid_down, date_commissioned, date_removed, fate_id,
        # notes
        (1, None, None, 'Star Flower',   TYPE_FREIGHTER, BUREAU, None,
         11, 1, 8, 1, 70, -1, 5, 13,
         2.0, None, 1, 0,
         1000.0, 301.0,
         7, 13, 1, 0,
         7, 7, 7,
         '2×', 44500000.0,
         0, 0, None, None,
         STAR_FLOWER_NOTE),

        (2, None, None, 'Midnight Sun',  TYPE_SHUTTLE, BUREAU, None,
         9, 0, 7, 1, 50, -1, 5, 12,
         3.0, 2.6, 0, 0,
         300.0, 11.6,
         2, 8, 0, 1,
         2, 2, 0,
         None, 3660000.0,
         0, 0, None, None,
         MIDNIGHT_SUN_STACK_NOTE),

        (3, None, None, 'Midnight Sun',  TYPE_SHUTTLE, BUREAU, 2,
         9, 0, 6, 1, 30, 0, 4, 12,
         3.0, 3.4, 0, 0,
         100.0, 11.4,
         2, 12, 0, 1,
         2, 2, 0,
         None, 1610000.0,
         0, 0, None, None,
         MIDNIGHT_SUN_ORBITER_NOTE),
    ]
    conn.executemany("""
        INSERT OR IGNORE INTO ships
        (ship_id,hull_number,name,class_name,type_id,bureau_id,parent_ship_id,
         tl,is_superscience,sm,is_streamlined,dst_hp,handling,stability_rating,ht,
         move_accel_g,move_delta_v_mps,move_is_ftl,move_atm_only,
         lwt_tons,load_tons,occ_crew,occ_passengers,occ_has_artificial_grav,occ_is_short_voyage,
         ddr_front,ddr_central,ddr_rear,range_ftl,cost_dollars,
         date_laid_down,date_commissioned,date_removed,fate_id,notes)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, ships)


def populate_slots(conn):
    # (ship_id, hull_section, slot_number, slot_to, is_core, is_high_energy, system_id, detail)
    slots = [
        # ---- Star Flower (ship_id=1) ----
        (1,'front',  1,None,0,0, ARM_METALLIC_LAM,  'dDR 7'),
        (1,'front',  2,None,0,0, CARGO_HOLD,         '50 tons'),
        (1,'front',  3,None,0,0, CARGO_HOLD,         '50 tons'),
        (1,'front',  4,None,0,0, CARGO_HOLD,         '50 tons'),
        (1,'front',  5,None,0,0, CARGO_HOLD,         '50 tons'),
        (1,'front',  6,None,0,0, ARRAY_ENHANCED,     'Level 10'),
        (1,'front',  None,None,1,0,CONTROL_ROOM,     '4 stations; Complexity 9'),
        (1,'central',1,None,0,0, ARM_METALLIC_LAM,  'dDR 7'),
        (1,'central',2,None,0,0, HABITAT,            '6 cabins; passengers'),
        (1,'central',3,None,0,0, HABITAT,            '4 cabins; 2-bed sickbay; crew'),
        (1,'central',4,None,0,0, CARGO_HOLD,         '50 tons'),
        (1,'central',5,None,0,0, CARGO_HOLD,         '50 tons'),
        (1,'central',6,None,0,1, WPN_TERTIARY,       '1 turret; 10 MJ laser; 43.5 tons cargo'),
        (1,'rear',   1,None,0,0, ARM_METALLIC_LAM,  'dDR 7'),
        (1,'rear',   2,None,0,1, RLS_STANDARD,       '1G acceleration'),
        (1,'rear',   3,None,0,1, RLS_STANDARD,       '1G acceleration'),
        (1,'rear',   4,None,0,1, FTL_STARDRIVE,      'FTL-1'),
        (1,'rear',   5,None,0,1, FTL_STARDRIVE,      'FTL-1'),
        (1,'rear',   6,None,0,0, ENGINE_ROOM,        '1 workspace'),
        (1,'rear',   None,None,1,0,PP_FUSION,        '2 Power Points'),

        # ---- Midnight Sun booster+orbiter (ship_id=2) ----
        (2,'front',  1,6,  0,0, UPPER_STAGE,        '100-ton upper stage (orbiter)'),
        (2,'central',1,6,  1,0, FUEL_TANK,          '105 tons rocket fuel (expendable)'),
        (2,'rear',   1,None,0,0,RE_CHEMICAL,        '3G acceleration'),
        (2,'rear',   2,6,  1,0, FUEL_TANK,          '90 tons rocket fuel (expendable)'),

        # ---- Midnight Sun orbiter only (ship_id=3) ----
        (3,'front',  1,None,0,0, ARM_LIGHT_ALLOY,   'dDR 2'),
        (3,'front',  2,None,0,0, CONTROL_ROOM,      '2 stations; Complexity 5; comm/sensor Level 4'),
        (3,'front',  3,4,  0,0, PASSENGER_SEATING,  '12 seats'),
        (3,'front',  5,6,  0,0, CARGO_HOLD,         '10 tons'),
        (3,'central',1,None,0,0, ARM_LIGHT_ALLOY,   'dDR 2'),
        (3,'central',2,6,  1,0, FUEL_TANK,          '30 tons rocket fuel (expendable)'),
        (3,'rear',   1,None,0,0, RE_CHEMICAL,       '3G acceleration'),
        (3,'rear',   2,6,  1,0, FUEL_TANK,          '30 tons rocket fuel (expendable)'),
    ]
    conn.executemany("""
        INSERT OR IGNORE INTO ship_system_slots
        (ship_id,hull_section,slot_number,slot_to,is_core,is_high_energy,system_id,detail)
        VALUES (?,?,?,?,?,?,?,?)
    """, slots)


def populate_design_features_junction(conn):
    # (ship_id, feature_id, notes)
    conn.executemany(
        "INSERT OR IGNORE INTO ship_design_features(ship_id,feature_id,notes) VALUES (?,?,?)",
        [
            (1, 1, 'Artificial gravity throughout; Occ suffix ASV'),
            (3, 2, 'Winged; air Handling/SR +4/5'),
        ]
    )


def main():
    conn = sqlite3.connect(WORLDS_DB)
    conn.execute("PRAGMA foreign_keys = ON")
    create_schema(conn)
    populate_reference(conn)
    populate_system_catalog(conn)
    populate_armor_stats(conn)
    populate_system_stats(conn)
    populate_ships(conn)
    populate_slots(conn)
    populate_design_features_junction(conn)
    conn.commit()

    # Summary
    for table in ['hull_sizes','design_bureaus','ship_types','ship_fates',
                  'design_features','ships','ship_system_slots',
                  'ship_system_catalog','armor_sm_stats','system_sm_stats',
                  'ship_design_features']:
        n = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  {table:30s} {n:>5} rows")

    conn.close()
    print(f"\nDatabase ready: {WORLDS_DB}")


if __name__ == '__main__':
    main()
