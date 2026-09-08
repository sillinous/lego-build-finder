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

CREATE INDEX IF NOT EXISTS idx_set_inventory_part_color
    ON set_inventory(part_id, color);

CREATE INDEX IF NOT EXISTS idx_set_inventory_set
    ON set_inventory(set_id);

CREATE INDEX IF NOT EXISTS idx_sets_name
    ON sets(name);
