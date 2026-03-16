setup:
	py -3.11 -m venv .venv
	.\.venv\Scripts\python -m pip install --upgrade pip
	.\.venv\Scripts\python -m pip install -r requirements.txt

run:
	.\run.bat

test:
	python -m unittest discover -s tests

report:
	echo "Open reports/energy_analysis.ipynb to view the analysis."

clean:
	docker compose down