# Technical Decisions

This document summarizes the key implementation decisions made for this assessment.

## Design Objectives

The pipeline was designed to simulate a realistic production-style data engineering workflow with clear separation between ingestion, enrichment, storage, transformation, and analytics layers.

The main design goals were:
- modularity
- reproducibility
- reliability
- clear data validation
- efficient downstream analytics processing

## Choice of Data Source

The pipeline uses the EIA API as the primary source of Electricity Retail Sales Data.

The dataset includes:
- reporting period
- state
- sector
- electricity price
- electricity sales

The API was configured to retrieve:
- monthly frequency data
- Colorado (stateid = CO)
- price and sales fields
- approximately five years of historical data

This provided a realistic time-series dataset with enough historical depth to support transformations and reporting.

## FastAPI Enrichment Layer
A separate FastAPI enrichment service was implemented to simulate the addition of operational or contextual signals to the source dataset.

The service generates additional fields such as:
- temperature_c
- demand_index
- grid_stress_level
- renewable_share_pct

Separating enrichment into an API layer keeps the ingestion script simpler and makes the design more modular. It also reflects how real-world data platforms often integrate external services or feature generation layers before loading records into a warehouse.

## Prefect Orchestration

Prefect was selected to orchestrate the pipeline because it provides a clear task-based workflow with logging and retry support. Prefect also provides observability into pipeline execution through structured task logs, making debugging and monitoring easier.

The Prefect flow coordinates the following tasks:

- ingestion
- dbt transformations
- dbt tests

Prefect was useful here because it provides:
- structured task execution
- task-level retries
- centralized logging
- clearer pipeline sequencing

Task retries were configured as follows:

ingestion: retries=2, retry_delay_seconds=5
dbt run: retries=2, retry_delay_seconds=5
dbt tests: retries=1, retry_delay_seconds=5

This helps the pipeline recover from temporary failures without requiring manual reruns.

## API Retry Strategy
External API calls use a retry strategy implemented using the requests library with HTTPAdapter and urllib3 Retry.

Retry configuration:

total retries = 3
backoff factor = 1
retry status codes:
429
500
502
503
504

This improves reliability when temporary API failures occur.

## Data Validation Strategy

Source records are validated before loading into PostgreSQL.

Records are skipped when:
- period is missing
- state_id is missing
- price is missing

These fields were treated as mandatory because they are required to define the analytical grain and calculate key metrics. Loading records without them would create incomplete or invalid downstream aggregates.

Why records were skipped

The skip logic was intentionally implemented to prevent low-quality source records from entering the warehouse. Since the pipeline aggregates data by period, state_id, and sector_id, missing values in these key fields would break the analytical model design.

Records with missing price were also skipped because price is one of the main business measures in the dataset and is required for analytics outputs. Skipping invalid records ensures that only structurally valid data enters the warehouse, preventing downstream aggregation errors.

## Enrichment response validation

Although the enrichment values are synthetically generated for the purpose of this assessment, the ingestion pipeline treats the API as an external dependency. For this reason, the enrichment response is validated before records are written to the warehouse.

The following fields are required from the enrichment API:
- date
- region
- temperature_c
- demand_index
- grid_stress_level
- renewable_share_pct

If any required field is missing, the record is rejected and logged.

This validation step ensures that incomplete enrichment responses do not propagate into the raw warehouse tables and affect downstream analytical models.

## Raw Data Loading Strategy
The raw table is reloaded on each ingestion run using:

TRUNCATE TABLE raw.energy_enriched_data RESTART IDENTITY;

This approach was chosen because:
- it simplifies ingestion logic
- it guarantees a consistent raw dataset
- the source dataset is small enough that full reload is practical

This means the raw layer is fully refreshed on each run.
In a real production scenario, watermark-based incremental loading could be used to avoid reloading the entire dataset.

## Incremental Analytics Strategy
The analytics model is implemented using dbt incremental materialization.

Unique key:
- period
- state_id
- sector_id

This matches the analytical grain of the model.
During incremental runs, only records with periods greater than the latest period in the target analytics table are processed.

This means:
- the raw table is fully reloaded
- the analytics table is incrementally updated

This design keeps ingestion simple while improving efficiency in the transformation layer.


## dbt Transformation Design
The analytics model reads from the staged enriched dataset using:

{{ ref('stg_energy_enriched_data') }}


This dbt reference acts as a lookup to the staged source model and preserves lineage between the raw and analytics layers.

The analytics model aggregates records by:
- period (month)
- state_id
- sector_id

During this step, the model calculates aggregated metrics including:
- average electricity price
- total electricity sales
- average temperature
- average demand index
- renewable share percentage
- grid stress indicators
- record count

## Database Constraints and Keys
The analytics table is modeled at the grain of:
- period
- state_id
- sector_id

This is enforced through the table design using the primary key / unique key combination.
The raw table stores source-level records with enrichment fields and an ingested_at timestamp for traceability.

If the schema defines NOT NULL constraints on key fields, these constraints support data quality by preventing incomplete records from being stored in critical warehouse columns.

## Database Indexing
Indexes were added to improve performance for both transformation queries and analytical access patterns.

Raw table: raw.energy_enriched_data
Indexes include:
- period
- (state_id, sector_id, period)

Justification:
- period supports time-based filtering during validation and transformation
- (state_id, sector_id, period) supports source-level queries filtered by business dimensions and time

Analytics table: analytics.monthly_energy_summary

The analytics table is modeled at the grain of:
- period
- state_id
- sector_id

Supporting indexes and key structure improve query performance for common analytical filters such as time range, state, and sector.
This indexing approach reflects the fact that the raw layer is optimized for ingestion and transformation, while the analytics layer is optimized for reporting and notebook-based analysis.

## Logging

Python logging is used throughout the ingestion process to capture:
- API requests
- skipped records
- enrichment failures
- output file generation
- database loading status

This improves visibility during pipeline execution and makes debugging easier.


## Containerized Environment
Docker is used to run:
- PostgreSQL database
- FastAPI enrichment service

Containerization ensures that infrastructure services can be reproduced consistently across machines without requiring complex manual setup.

## Testing Approach

Two levels of testing were included in the project.

- Python unit tests were written for ingestion functions such as session creation, enrichment response validation, and record combination logic.
- dbt data tests were used to validate analytical model quality and key constraints in the warehouse layer.

This combination provides both code-level validation and data-level validation across the pipeline.

## Decision Summary

The pipeline was designed to demonstrate a modular and reliable data engineering workflow.

Electricity retail sales data is retrieved from the EIA API and enriched using a FastAPI service that generates additional contextual signals. Basic validation rules ensure incomplete records are skipped before loading data into the warehouse.

The raw dataset is refreshed during ingestion to keep the pipeline simple, while dbt incremental models are used to efficiently build aggregated analytics tables.

Prefect orchestrates the pipeline execution with retries and logging, and database indexes were added to support efficient transformations and analytical queries.

A Jupyter notebook is included for exploratory analysis and visualization of the final analytics dataset.