import json
import logging
import os
import time
from pathlib import Path

import psycopg2
import requests
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

EIA_API_KEY = os.getenv("EIA_API_KEY")
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")

if not EIA_API_KEY:
    raise ValueError("EIA_API_KEY is not set in .env")

if not all([POSTGRES_HOST, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD]):
    raise ValueError("PostgreSQL environment variables are not fully configured in .env")

EIA_URL = (
    "https://api.eia.gov/v2/electricity/retail-sales/data/"
    f"?api_key={EIA_API_KEY}"
    "&frequency=monthly"
    "&data[]=price"
    "&data[]=sales"
    "&facets[stateid][]=CO"
    "&sort[0][column]=period"
    "&sort[0][direction]=desc"
    "&length=360"
)

ENRICHMENT_URL = "http://127.0.0.1:8000/enrichment"


def create_session() -> requests.Session:
    """
    Create an HTTP session with retry support for temporary failures.
    """
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)

    session = requests.Session()
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def get_db_connection():
    """
    Create a PostgreSQL connection using environment variables.
    """
    return psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
    )


def fetch_eia_data(session: requests.Session) -> list[dict]:
    """
    Fetch primary data from the EIA API.
    """
    logging.info("Fetching data from EIA API")

    response = session.get(EIA_URL, timeout=30)
    response.raise_for_status()

    payload = response.json()
    records = payload.get("response", {}).get("data", [])

    if not records:
        raise ValueError("No data returned from EIA API")

    logging.info("Fetched %s records from EIA API", len(records))
    return records


def fetch_enrichment(session: requests.Session, date_value: str, region: str) -> dict:
    """
    Fetch enrichment data from the local FastAPI service.
    """
    response = session.get(
        ENRICHMENT_URL,
        params={"date": date_value, "region": region},
        timeout=10
    )
    response.raise_for_status()

    enrichment = response.json()

    required_keys = [
        "date",
        "region",
        "temperature_c",
        "demand_index",
        "grid_stress_level",
        "renewable_share_pct",
    ]

    for key in required_keys:
        if key not in enrichment:
            raise ValueError(f"Missing key in enrichment response: {key}")

    return enrichment


def combine_data(eia_data: list[dict], session: requests.Session) -> list[dict]:
    """
    Combine EIA records with FastAPI enrichment data.
    Skip records only when mandatory fields are missing.
    """
    combined = []

    for record in eia_data:
        period = record.get("period")
        state_id = record.get("stateid")

        if not period:
            logging.warning("Skipping record with missing period")
            continue

        if not state_id:
            logging.warning("Skipping record with missing state_id for period %s", period)
            continue

        if record.get("price") is None:
            logging.warning(
                "Skipping record with missing price for period %s",
                period
            )
            continue

        period_date = f"{period}-01"

        try:
            enrichment = fetch_enrichment(session, period_date, state_id)

            sales_value = record.get("sales")
            sales_value = round(float(sales_value), 2) if sales_value is not None else None

            combined_record = {
                "period": period_date,
                "state_id": state_id,
                "state_description": record.get("stateDescription"),
                "sector_id": record.get("sectorid"),
                "sector_name": record.get("sectorName"),
                "price": round(float(record.get("price")), 2),
                "sales": sales_value,
                "price_units": record.get("price-units"),
                "sales_units": record.get("sales-units"),
                "temperature_c": enrichment.get("temperature_c"),
                "demand_index": enrichment.get("demand_index"),
                "grid_stress_level": enrichment.get("grid_stress_level"),
                "renewable_share_pct": enrichment.get("renewable_share_pct"),
                "enrichment_region": enrichment.get("region"),
            }

            combined.append(combined_record)

            time.sleep(0.1)

        except Exception as exc:
            logging.warning(
                "Failed to enrich record for date %s and region %s: %s",
                period_date,
                state_id,
                exc
            )

    logging.info("Created %s enriched records", len(combined))
    return combined


def save_output(records: list[dict]) -> None:
    """
    Save the enriched records to JSON output.
    """
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / "enriched_data.json"

    with output_file.open("w", encoding="utf-8") as file:
        json.dump(records, file, indent=2)

    logging.info("Saved output to %s", output_file)


def clear_raw_table(cursor) -> None:
    """
    Clear the raw table before loading fresh data.
    """
    cursor.execute("TRUNCATE TABLE raw.energy_enriched_data RESTART IDENTITY;")


def load_to_postgres(records: list[dict]) -> None:
    """
    Load enriched records into PostgreSQL raw table.
    """
    if not records:
        logging.warning("No records to load into PostgreSQL")
        return

    insert_sql = """
        INSERT INTO raw.energy_enriched_data (
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
        )
        VALUES (
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, CURRENT_TIMESTAMP
        );
    """

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        clear_raw_table(cursor)

        for record in records:
            cursor.execute(
                insert_sql,
                (
                    record["period"],
                    record["state_id"],
                    record["state_description"],
                    record["sector_id"],
                    record["sector_name"],
                    record["price"],
                    record["sales"],
                    record["price_units"],
                    record["sales_units"],
                    record["temperature_c"],
                    record["demand_index"],
                    record["grid_stress_level"],
                    record["renewable_share_pct"],
                    record["enrichment_region"],
                )
            )

        conn.commit()
        logging.info("Loaded %s records into raw.energy_enriched_data", len(records))

    except Exception as exc:
        if conn:
            conn.rollback()
        logging.error("Failed to load data into PostgreSQL: %s", exc)
        raise

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def main() -> None:
    session = create_session()
    eia_data = fetch_eia_data(session)
    combined_data = combine_data(eia_data, session)
    save_output(combined_data)
    load_to_postgres(combined_data)
    logging.info("Ingestion completed successfully")


if __name__ == "__main__":
    main()