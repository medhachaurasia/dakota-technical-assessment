# Dakota Analytics - Energy Data Pipeline

## Problem Statement

Energy market data is available through public sources like the U.S. Energy Information Administration (EIA) API, but the raw data is not immediately ready for analysis. It often needs to be enriched, structured, validated, and transformed before it can be used to generate meaningful insights.

The goal of this project was to design a small but realistic data pipeline that can automatically ingest energy data, enrich it with additional context, transform it into analytics-ready datasets, and produce a simple analytical report. The system should also be reproducible and easy to run locally.

## Solution Overview

To solve this problem, I built an end-to-end data pipeline that combines several common data engineering components. This project implements an end-to-end data pipeline for ingesting, enriching, transforming, and analyzing energy market data.

The pipeline retrieves energy data from the EIA API using a Python ingestion script. Each record is then enriched through a lightweight FastAPI service that generates additional contextual signals.

The enriched data is stored in PostgreSQL and transformed using dbt to create analytics-ready models. dbt tests are also used to validate data quality.

A Prefect workflow orchestrates the entire process, ensuring the steps run in the correct order — ingestion, transformation, testing, and report generation.

Finally, a Jupyter notebook is used to explore and visualize the resulting dataset.

The system is containerized using Docker and automated through a Makefile so the entire pipeline can be reproduced and executed locally with a few simple commands.

## System Components & Data Pipeline Flow

1.	FastAPI Service: This provides an enrichment API that generates additional contextual signals for energy records
2.	Prefect Orchestration Flow (pipeline.py): This is used to manage pipeline execution
3.	Python Ingestion Script (fetch_data.py) retrieves energy data from the EIA API
4.	Retrieved records are enriched via the FastAPI service
5.	Enriched data is stored in PostgreSQL raw tables
6.	dbt models transform the data into analytics-ready datasets
7.	A Jupyter notebook performs analysis and visualization

Steps 1–6 of the pipeline can be executed using a single command via the Makefile, ensuring the pipeline can be reproduced easily in a fresh environment.

## Project Structure
```
dakota-technical-assessment/
├── README.md              # Setup instructions
├── docker-compose.yml     # All services defined
├── run.bat       # Startup script 
├── .env.example          # Environment variables template
├── Makefile              
│
├── api/                  # FastAPI service
├── ingestion/            # Data ingestion clients
├── orchestration/        # Prefect orchestrator flow
├── database/             # Schema and init scripts
├── dbt/                  # dbt project
├── reports/              # Analytical notebook
│
├── docs/                 #  DOCUMENTATION
│   ├── architecture.md   # System architecture and design
│   ├── decisions.md      # Technical decisions and rationale
│   └── er_diagram.png    # Database schema diagram
│
└── tests/                #  tests

```

## Prerequisites
The following tools must be installed:
- Python 3.11 
- Docker Desktop
- Make  (for running automation commands via Makefile)

Note: The project was validated using a local virtual environment and Docker-based services. Python 3.11 is recommended for best package compatibility.

## Reproducibility
After cloning the repository, the full pipeline can be executed with:

```bash
make setup
make run
make test
make report
make clean
```

This will:
- Install required dependencies
- Start required Docker services
- Execute the Prefect pipeline
- Run dbt transformations and tests
- Stop services

## Setup
Clone the repository and install dependencies:
Run:
```bash
make setup
```

This command installs all required Python dependencies defined in requirements.txt

## Running the Pipeline

Execute the full pipeline with:
```bash
make run
```

This command runs the pipeline startup script and performs the following steps:
- Starts Docker services (PostgreSQL and FastAPI enrichment API)
- Executes the Prefect orchestration flow
- Retrieves energy data from the EIA API
- Enriches records using the FastAPI service
- Loads enriched records into the PostgreSQL raw table
- Executes dbt transformations
- Runs dbt data quality tests

Example successful output:

Done. PASS=9 WARN=0 ERROR=0 SKIP=0 NO-OP=0 TOTAL=9
=====================================
Pipeline completed successfully
====================================

## Running Tests

Python unit tests validate core ingestion logic.
Run tests with:
```bash
make test
```

This executes:
- Python unit tests in the tests/ directory
- dbt data tests validating analytics models

## Viewing the Report

The analytical report can be opened with:
make report

This command points to the analytical notebook located in:
reports/energy_analysis.ipynb

The Jupyter notebook contains the exploratory analysis and visualizations built on top of the analytics dataset.  
The notebook includes executed outputs and can be opened directly to review the results.

## Cleaning the Environment
To stop and remove running Docker services
```bash
make clean
```
This stops PostgreSQL and the FastAPI service containers.

## API Service

The FastAPI service provides an enrichment endpoint used by the ingestion pipeline to generate additional contextual metrics.

Health endpoint:
http://localhost:8000/health

Example response:
{
  "status": "healthy",
  "service": "dakota-enrichment-api",
  "version": "1.0"
}

The enrichment endpoint used by the ingestion pipeline is:

http://localhost:8000/enrichment


## Documentation
Additional documentation is available in the docs/ directory:

architecture.md  – System architecture and data flow
decisions.md     – Key technical decisions and trade-offs
er_diagram.png   – Database schema diagram

## Summary
This project demonstrates a modern data engineering workflow combining:
- Python-based ingestion
- PostgreSQL storage
- dbt transformation layer
- containerized infrastructure
- automated pipeline execution

The system is designed to be modular, reproducible, and easy to run, providing a clear example of a production-style data pipeline.
A Jupyter notebook is included for exploratory analysis and visualization of the final analytics dataset.

##Benefits

This approach provides several practical benefits.

First, the pipeline is modular, with clear separation between ingestion, enrichment, storage, transformation, and reporting. Each component can be modified or extended independently without impacting the rest of the system.

Second, the use of Prefect orchestration ensures that pipeline tasks run in the correct order and can automatically retry if a step fails. This improves reliability compared to running scripts manually.

Third, dbt transformations and tests help ensure that the analytical datasets are structured and validated before they are used for analysis.

Finally, the project is designed to be fully reproducible. With Docker services and Makefile automation, the entire pipeline can be executed locally with only a few commands, making it easy to set up and run in a new environment.

