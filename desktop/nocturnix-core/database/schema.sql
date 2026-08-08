PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS app_settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS import_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT, source_path TEXT NOT NULL, source_type TEXT NOT NULL,
    imported_at TEXT NOT NULL, status TEXT NOT NULL, row_count INTEGER NOT NULL DEFAULT 0, notes TEXT
);
CREATE TABLE IF NOT EXISTS devices (
    device_id TEXT PRIMARY KEY, manufacturer_id TEXT, manufacturer TEXT, device_family_id TEXT,
    device_type_id TEXT, model TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS services (
    service_id TEXT PRIMARY KEY, internal_name TEXT NOT NULL, public_name TEXT,
    service_type_id TEXT, service_type_name TEXT, active INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS pricing_records (
    pricing_record_id TEXT PRIMARY KEY, device_id TEXT NOT NULL, service_id TEXT NOT NULL,
    part_cost_cents INTEGER, retail_price_cents INTEGER, approval_status TEXT NOT NULL DEFAULT 'draft',
    public_approved INTEGER NOT NULL DEFAULT 0, square_approved INTEGER NOT NULL DEFAULT 0, updated_at TEXT,
    FOREIGN KEY(device_id) REFERENCES devices(device_id), FOREIGN KEY(service_id) REFERENCES services(service_id)
);
CREATE TABLE IF NOT EXISTS integration_map (
    pricing_record_id TEXT PRIMARY KEY, square_item_id TEXT, square_variation_id TEXT,
    website_service_id TEXT, last_synced_at TEXT, sync_status TEXT NOT NULL DEFAULT 'not_synced', last_error TEXT,
    FOREIGN KEY(pricing_record_id) REFERENCES pricing_records(pricing_record_id)
);
CREATE TABLE IF NOT EXISTS sync_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT, integration TEXT NOT NULL, direction TEXT NOT NULL,
    started_at TEXT NOT NULL, completed_at TEXT, status TEXT NOT NULL, record_count INTEGER NOT NULL DEFAULT 0,
    message TEXT
);
