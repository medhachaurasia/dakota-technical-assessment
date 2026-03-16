CREATE TABLE IF NOT EXISTS analytics.monthly_energy_summary (
    period DATE NOT NULL,
    state_id VARCHAR(10) NOT NULL,
    state_description VARCHAR(100),
    sector_id VARCHAR(20) NOT NULL,
    sector_name VARCHAR(100),
    avg_price NUMERIC(10, 2),
    total_sales NUMERIC(14, 2),
    avg_temperature_c NUMERIC(6, 2),
    avg_demand_index NUMERIC(6, 2),
    avg_renewable_share_pct NUMERIC(6, 2),
    high_grid_stress_flag BOOLEAN,
    record_count INTEGER,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (period, state_id, sector_id)
);

CREATE INDEX IF NOT EXISTS idx_analytics_monthly_period
    ON analytics.monthly_energy_summary(period);

CREATE INDEX IF NOT EXISTS idx_analytics_monthly_state_sector
    ON analytics.monthly_energy_summary(state_id, sector_id);