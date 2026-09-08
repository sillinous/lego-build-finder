PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS sets (
    set_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    year INTEGER
);

CREATE TABLE IF NOT EXISTS set_inventory (
    set_id TEXT NOT NULL REFERENCES sets(set_id) ON DELETE CASCADE,
    part_id TEXT NOT NULL,
    color TEXT NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    PRIMARY KEY (set_id, part_id, color)
);

CREATE TABLE IF NOT EXISTS parts (
    part_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    part_category_id TEXT
);

CREATE TABLE IF NOT EXISTS colors (
    color_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    rgb TEXT,
    is_trans BOOLEAN NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_set_inventory_part_color
    ON set_inventory(part_id, color);

CREATE INDEX IF NOT EXISTS idx_set_inventory_set
    ON set_inventory(set_id);

CREATE INDEX IF NOT EXISTS idx_sets_name
    ON sets(name);

CREATE INDEX IF NOT EXISTS idx_parts_name
    ON parts(name);

CREATE INDEX IF NOT EXISTS idx_colors_name
    ON colors(name);
