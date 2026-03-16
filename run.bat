@echo off
setlocal

echo =====================================
echo Dakota Analytics Data Pipeline
echo =====================================

cd /d "%~dp0"

echo.
echo [1/6] Activating virtual environment...
call ".\.venv\Scripts\activate.bat"
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment.
    exit /b 1
)

echo.
echo [2/6] Starting Docker services...
docker compose up -d --build
if errorlevel 1 (
    echo ERROR: Failed to start docker services.
    exit /b 1
)

echo.
echo [3/6] Waiting for services to initialize...
timeout /t 15 /nobreak >nul

echo.
echo [4/6] Running ingestion pipeline...
python ingestion\fetch_data.py
if errorlevel 1 (
    echo ERROR: Ingestion failed.
    exit /b 1
)

echo.
echo [5/6] Running dbt transformations...
cd dbt
dbt run --profiles-dir .
if errorlevel 1 (
    echo ERROR: dbt run failed.
    cd ..
    exit /b 1
)

echo.
echo [6/6] Running dbt tests...
dbt test --profiles-dir .
if errorlevel 1 (
    echo ERROR: dbt test failed.
    cd ..
    exit /b 1
)

cd ..

echo.
echo =====================================
echo Pipeline completed successfully
echo =====================================
echo.
echo Outputs:
echo - Raw data loaded into PostgreSQL
echo - Analytics models built in dbt
echo - Report notebook available at reports\energy_analysis.ipynb
echo.
echo To stop services:
echo docker compose down

endlocal