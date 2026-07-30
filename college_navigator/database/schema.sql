-- =====================================================================
-- AI-Powered Smart QR-Based College Navigation System
-- Database Schema (SQLite compatible, portable to PostgreSQL)
-- =====================================================================

-- ---------------------------------------------------------------------
-- Table: locations
-- Stores every destination that can be navigated to on campus
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS locations (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    category        TEXT NOT NULL,          -- e.g. Academic, Admin, Hostel, Sports
    building        TEXT,                   -- e.g. "Block A"
    floor           TEXT,                   -- e.g. "Ground Floor"
    latitude        REAL NOT NULL,
    longitude       REAL NOT NULL,
    description     TEXT,
    icon            TEXT DEFAULT 'bi-geo-alt-fill',   -- Bootstrap icon class
    timings         TEXT,                   -- e.g. "9:00 AM - 5:00 PM"
    contact         TEXT,
    node_id         INTEGER,                -- FK -> graph_nodes.id (nearest routable node)
    is_active       INTEGER DEFAULT 1,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (node_id) REFERENCES graph_nodes(id)
);

-- ---------------------------------------------------------------------
-- Table: graph_nodes
-- Waypoints that make up the walkable path network of the campus.
-- Locations are linked to their nearest node so routing can be
-- computed with Dijkstra's algorithm over real walking paths instead
-- of a straight line through buildings.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS graph_nodes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    label           TEXT,                   -- optional human label e.g. "Junction 3"
    latitude        REAL NOT NULL,
    longitude       REAL NOT NULL
);

-- ---------------------------------------------------------------------
-- Table: graph_edges
-- Undirected walkable path segments between two nodes, with a
-- pre-computed distance in meters used as the edge weight.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS graph_edges (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    node_a_id       INTEGER NOT NULL,
    node_b_id       INTEGER NOT NULL,
    distance_m      REAL NOT NULL,
    FOREIGN KEY (node_a_id) REFERENCES graph_nodes(id),
    FOREIGN KEY (node_b_id) REFERENCES graph_nodes(id)
);

-- ---------------------------------------------------------------------
-- Table: admins
-- Administrator accounts for the admin panel (passwords are hashed,
-- never stored in plain text).
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS admins (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    username        TEXT UNIQUE NOT NULL,
    password_hash   TEXT NOT NULL,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ---------------------------------------------------------------------
-- Table: visitor_logs
-- Analytics: every time a visitor requests a route, we log it so the
-- admin dashboard can show "most searched destinations", peak times,
-- etc.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS visitor_logs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    location_id     INTEGER,
    source          TEXT DEFAULT 'qr',      -- qr | search | chatbot
    user_agent      TEXT,
    timestamp       DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (location_id) REFERENCES locations(id)
);

-- ---------------------------------------------------------------------
-- Table: chatbot_faq
-- Knowledge base the rule-based / fuzzy-matching chatbot draws answers
-- from, in addition to the live locations table.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS chatbot_faq (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    question        TEXT NOT NULL,
    answer          TEXT NOT NULL,
    keywords        TEXT                    -- comma separated keywords for matching
);

-- ---------------------------------------------------------------------
-- Table: qr_codes
-- Tracks every QR code generated so the admin can regenerate,
-- deactivate, or download them again.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS qr_codes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    location_id     INTEGER NOT NULL,
    file_path       TEXT NOT NULL,
    target_url      TEXT NOT NULL,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (location_id) REFERENCES locations(id)
);

CREATE INDEX IF NOT EXISTS idx_locations_category ON locations(category);
CREATE INDEX IF NOT EXISTS idx_visitor_logs_location ON visitor_logs(location_id);
