from pathlib import Path
import shutil
import subprocess

from prefect import flow, task, get_run_logger


PROJECT_ROOT = Path(__file__).resolve().parent.parent


@task(name="run-ingestion", retries=2, retry_delay_seconds=5)
def run_ingestion():
    """
    Run the ingestion pipeline to fetch source data from EIA and enrich it
    through the FastAPI service.
    """
    logger = get_run_logger()
    logger.info("Starting ingestion pipeline")

    result = subprocess.run(
        ["python", "ingestion/fetch_data.py"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        logger.error("Ingestion failed")
        raise RuntimeError(f"Ingestion failed:\n{result.stderr}")

    logger.info("Ingestion completed successfully")
    return result.stdout


@task(name="run-dbt-transformations", retries=2, retry_delay_seconds=5)
def run_dbt():
    """
    Run dbt transformations to create analytics-ready models.
    """
    logger = get_run_logger()
    logger.info("Starting dbt transformations")

    if shutil.which("dbt") is None:
        raise RuntimeError(
            "dbt command not found. Please install dbt-core and dbt-postgres."
        )

    dbt_project_dir = PROJECT_ROOT / "dbt"

    if not dbt_project_dir.exists():
        raise RuntimeError("dbt project folder not found.")

    result = subprocess.run(
        ["dbt", "run"],
        cwd=dbt_project_dir,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        logger.error("dbt run failed")
        raise RuntimeError(f"dbt run failed:\n{result.stderr}")

    logger.info("dbt transformations completed successfully")
    return result.stdout


@task(name="run-data-quality-checks", retries=1, retry_delay_seconds=5)
def run_dbt_tests():
    """
    Run dbt tests to validate model quality and data integrity.
    """
    logger = get_run_logger()
    logger.info("Starting dbt data quality checks")

    if shutil.which("dbt") is None:
        raise RuntimeError(
            "dbt command not found. Please install dbt-core and dbt-postgres."
        )

    dbt_project_dir = PROJECT_ROOT / "dbt"

    if not dbt_project_dir.exists():
        raise RuntimeError("dbt project folder not found.")

    result = subprocess.run(
        ["dbt", "test"],
        cwd=dbt_project_dir,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        logger.error("dbt tests failed")
        raise RuntimeError(f"dbt test failed:\n{result.stderr}")

    logger.info("dbt data quality checks completed successfully")
    return result.stdout


@task(name="generate-report", retries=1, retry_delay_seconds=5)
def run_report():
    """
    Generate the final report from transformed analytical data.
    """
    logger = get_run_logger()
    logger.info("Starting report generation")

    report_script = PROJECT_ROOT / "reports" / "generate_report.py"

    if not report_script.exists():
        raise RuntimeError("Report generation script not found.")

    result = subprocess.run(
        ["python", str(report_script)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        logger.error("Report generation failed")
        raise RuntimeError(f"Report generation failed:\n{result.stderr}")

    logger.info("Report generation completed successfully")
    return result.stdout


@flow(name="dakota-energy-pipeline")
def energy_pipeline():
    """
    End-to-end orchestration flow:
    1. Run ingestion
    2. Run dbt transformations
    3. Run dbt tests / data quality checks
    4. Generate report
    """
    logger = get_run_logger()
    logger.info("Starting Dakota energy pipeline")

    ingestion_result = run_ingestion()
    dbt_result = run_dbt()
    dbt_test_result = run_dbt_tests()
    report_result = run_report()

    logger.info("Dakota energy pipeline completed successfully")

    return {
        "ingestion": ingestion_result,
        "dbt_run": dbt_result,
        "dbt_test": dbt_test_result,
        "report": report_result,
    }


if __name__ == "__main__":
    energy_pipeline()