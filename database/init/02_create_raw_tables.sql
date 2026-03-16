CREATE TABLE IF NOT EXISTS raw.energy_enriched_data (
    id BIGSERIAL PRIMARY KEY,
    period DATE NOT NULL,
    state_id VARCHAR(10) NOT NULL,
    state_description VARCHAR(100),
    sector_id VARCHAR(20) NOT NULL,
    sector_name VARCHAR(100),
    price NUMERIC(10, 2),
    sales NUMERIC(14, 2),
    price_units VARCHAR(100),
    sales_units VARCHAR(100),
    temperature_c NUMERIC(6, 2),
    demand_index NUMERIC(6, 2),
    grid_stress_level VARCHAR(20),
    renewable_share_pct NUMERIC(6, 2),
    enrichment_region VARCHAR(10),
    ingested_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_raw_energy_period
    ON raw.energy_enriched_data(period);

CREATE INDEX IF NOT EXISTS idx_raw_energy_state_sector_period
    ON raw.energy_enriched_data(state_id, sector_id, period);