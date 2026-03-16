# System Architecture

## Overview

The pipeline is designed using a layered architecture separating ingestion, enrichment, storage and analytics processing.
The system integrates external API data, internal enrichment services, and warehouse transformations.

## Main Architecture Components

• **External Data Source**  
The EIA API provides electricity retail sales data including price and sales metrics.

• **FastAPI Enrichment Service**  
A local API service generates additional operational metrics used to enrich the energy data.

• **Python Ingestion Pipeline**  
The ingestion script retrieves data from the EIA API and combines it with enrichment data.

• **PostgreSQL Warehouse**  
Stores both raw enriched records and analytics tables.

• **dbt Transformation Layer**  
Transforms raw data into aggregated analytics models.

• **Prefect Orchestration Flow**  
Coordinates pipeline execution and task dependencies.

Prefect manages task dependencies, retries, and logging, ensuring reliable and observable pipeline execution.

## Pipeline Flow

EIA API Public Dataset
        +
FastAPI Enrichment API
        ↓
Python Ingestion
        ↓
PostgreSQL raw table
    ↓
dbt transformations
    ↓
analytics.monthly_energy_summary
    ↓
exploratory analysis (using Jupyter Notebook)

## Data Ingestion

The ingestion script retrieves electricity retail sales data from the EIA API.

API configuration:

frequency = monthly
stateid = CO
data = price, sales
length = 360

This configuration retrieves approximately five years of monthly electricity retail data.

Each record retrieved from the EIA API is then enriched by calling the FastAPI enrichment endpoint, which generates additional contextual metrics such as temperature, demand index, and renewable energy share. The ingestion pipeline merges the EIA data with the enrichment response in memory using Python before storing the combined records in the PostgreSQL raw database layer.

## Database Architecture

1)Raw Layer

Table: raw.energy_enriched_data
This table stores the enriched records exactly as produced by the ingestion pipeline.

Important columns include:

- period
- state_id
- sector_id
- price
- sales
- temperature_c
- demand_index
- grid_stress_level
- renewable_share_pct
- enrichment_region
- ingested_at

Indexes

- period (supports efficient time-based filtering)
- state_id + sector_id + period (supports analytical queries grouped by business dimensions and time)

2)Transformation Layer

The analytics dataset is produced using dbt.

The transformation logic first looks up the enriched source data through a dbt reference:

{{ ref('stg_energy_enriched_data') }}

This reference ensures the analytics model reads from the latest staged enriched dataset and preserves clear model lineage inside dbt. After reading the staged dataset, the model aggregates electricity retail data by:

month (period)
state (state_id)
sector (sector_id)

During this step, the model calculates summary metrics such as:

- average electricity price
- total electricity sales
- average temperature
- average demand index
- average renewable share percentage
- high grid stress flag
- record count

This means the transformation layer performs both:

- lookup / reference of enriched staged data
- aggregation into analytics-ready monthly summaries

3)Incremental Processing

The dbt model uses incremental materialization with the unique key:

- period
- state_id
- sector_id

When dbt runs, it processes only new periods beyond the latest existing period in the target analytics table, while historical aggregates remain unchanged. This incremental strategy improves efficiency by avoiding full recomputation of previously processed months.

4)Analytics Layer

Table: analytics.monthly_energy_summary

Primary key:
- period
- state_id
- sector_id

Metrics stored in the analytics table include:

- average price
- total sales
- average temperature
- average demand index
- renewable share percentage
- grid stress indicators

## Testing and Data Quality

To improve reliability, the pipeline includes both code-level and data-level validation. Python unit tests validate key ingestion functions such as session creation, enrichment API response validation, and record combination logic. In addition, dbt data tests validate the analytical models to ensure required fields and model outputs maintain expected data quality. These validation layers complement the runtime data validation implemented in the ingestion pipeline.

## Architecture Summary

The architecture separates data ingestion, enrichment, storage, and analytics processing into distinct layers. 
External electricity retail sales data is enriched using a FastAPI service before being stored in the PostgreSQL raw layer. 
dbt is used to transform raw data into incremental analytical models, while Prefect orchestrates pipeline execution and ensures reliable task management.

This layered approach keeps the pipeline modular, maintainable, and easy to extend.