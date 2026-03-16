select
    id,
    period,
    state_id,
    state_description,
    sector_id,
    sector_name,
    price,
    sales,
    price_units,
    sales_units,
    temperature_c,
    demand_index,
    grid_stress_level,
    renewable_share_pct,
    enrichment_region,
    ingested_at
from raw.energy_enriched_data