# System Performance Analyser

A Flask + Tailwind CSS web dashboard for checking laptop performance in real time. It monitors CPU, RAM, disk, battery, network usage, top processes, and gives an overall laptop health/risk score.

## Features

- Live dashboard for CPU, RAM, disk, battery, and network usage
- Overall laptop health score with risk label
- Top processes table with normalized CPU usage
- Save performance logs to MySQL
- History page for saved logs
- Graph page using Chart.js
- Daily/weekly TXT and PDF report downloads

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Python, Flask |
| UI | Tailwind CSS, custom CSS |
| Charts | Chart.js |
| Monitoring | psutil |
| Database | MySQL |
| Reports | fpdf2 |

## Project Structure

```text
system-performance-analyser/
|-- app.py
|-- monitor.py
|-- database.py
|-- report.py
|-- settings.py
|-- paths.py
|-- setup.sql
|-- templates/
|   |-- index.html
|   |-- history.html
|   `-- graph.html
|-- static/
|   |-- style.css
|   `-- script.js
|-- requirements.txt
`-- README.md
```

## Run

```powershell
pip install -r requirements.txt
python app.py
```

Open:

```text
http://127.0.0.1:5000/
```

## MySQL

Default settings are in `settings.py`, and saved local credentials are read from `db_settings.json` if present.

The database/table are created automatically. You can also run `setup.sql` manually in MySQL Workbench.

## Generated Files

The app can create `reports/` and Python can create `__pycache__/` while running. These are ignored by git and can be deleted anytime.

## Author

Vishnu - Engineering Mini Project
