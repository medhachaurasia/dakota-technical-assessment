{{ config(
    materialized='incremental',
    unique_key=['period', 'state_id', 'sector_id']
) }}

select
    period,
    state_id,
    state_description,
    sector_id,
    sector_name,
    avg(price) as avg_price,
    sum(sales) as total_sales,
    avg(temperature_c) as avg_temperature_c,
    avg(demand_index) as avg_demand_index,
    avg(renewable_share_pct) as avg_renewable_share_pct,
    bool_or(grid_stress_level = 'high') as high_grid_stress_flag,
    count(*) as record_count,
    current_timestamp as updated_at
from {{ ref('stg_energy_enriched_data') }}

{% if is_incremental() %}
where period >= (
    select coalesce(max(period), '1900-01-01'::date) - interval '1 month'
    from {{ this }}
)
{% endif %}

group by
    period,
    state_id,
    state_description,
    sector_id,
    sector_name