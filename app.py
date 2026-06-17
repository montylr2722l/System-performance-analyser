"""Flask web application for System Performance Analyser."""

import threading
import webbrowser
from datetime import datetime

from flask import Flask, jsonify, redirect, render_template, request, send_file, url_for

from database import (
    fetch_all_logs,
    fetch_logs_for_graph,
    fetch_report_stats,
    init_database,
    insert_log,
    test_connection,
)

from monitor import collect_all_metrics, get_system_info, get_top_processes
from report import generate_pdf_report, generate_txt_report
from settings import get_db_config, save_db_config, test_db_config


app = Flask(__name__)


# ==========================
# Helpers
# ==========================
def _format_time(value):
    if isinstance(value, datetime):
        return value.strftime("%d-%m-%Y %I:%M %p")
    return str(value)


def _db_status():
    try:
        init_database()
        ok, message = test_connection()
        return {"ok": ok, "message": message}
    except Exception as exc:
        return {"ok": False, "message": str(exc)}


# ==========================
# Routes
# ==========================
@app.route("/")
def index():
    return render_template(
        "index.html",
        db_status=_db_status()
    )


@app.route("/history")
def history():
    logs = []
    error = None

    try:
        logs = fetch_all_logs(limit=100)
    except Exception as exc:
        error = str(exc)

    return render_template(
        "history.html",
        logs=logs,
        error=error
    )


@app.route("/graph")
def graph():
    return render_template("graph.html")


@app.route("/settings", methods=["GET", "POST"])
def settings():
    message = None
    ok = None
    config = get_db_config()

    if request.method == "POST":
        password = request.form.get("password", "").strip()
        if not password:
            password = config.get("password", "")

        save_db_config(
            host=request.form.get("host", "localhost").strip(),
            port=request.form.get("port", 3306),
            user=request.form.get("user", "root").strip(),
            password=password,
            database=request.form.get("database", "system_performance").strip(),
        )
        config = get_db_config()
        ok, message = test_db_config(config)

    return render_template(
        "settings.html",
        config=config,
        message=message,
        ok=ok,
        db_status=_db_status(),
    )


# ==========================
# API
# ==========================
@app.route("/api/metrics")
def api_metrics():
    try:
        return jsonify({
            "ok": True,
            "metrics": collect_all_metrics(),
            "system": get_system_info(),
            "processes": get_top_processes(),
            "timestamp": datetime.now().strftime("%d-%m-%Y %I:%M:%S %p")
        })

    except Exception as exc:
        return jsonify({
            "ok": False,
            "error": str(exc)
        }), 500


@app.route("/api/save-log", methods=["POST"])
def api_save_log():
    try:
        metrics = collect_all_metrics()
        log_id = insert_log(metrics)

        return jsonify({
            "ok": True,
            "log_id": log_id,
            "metrics": metrics
        })

    except Exception as exc:
        return jsonify({
            "ok": False,
            "error": str(exc)
        }), 500


@app.route("/api/graph-data")
def api_graph_data():
    try:
        logs = fetch_logs_for_graph(limit=50)

        return jsonify({
            "ok": True,
            "labels": [_format_time(row["log_time"]) for row in logs],
            "cpu": [float(row["cpu_usage"]) for row in logs],
            "ram": [float(row["ram_usage"]) for row in logs],
            "disk": [float(row["disk_usage"]) for row in logs]
        })

    except Exception as exc:
        return jsonify({
            "ok": False,
            "error": str(exc)
        }), 500


# ==========================
# Reports
# ==========================
@app.route("/report/<period>/<file_type>")
def download_report(period, file_type):

    if period not in {"daily", "weekly"}:
        return redirect(url_for("index"))

    if file_type not in {"txt", "pdf"}:
        return redirect(url_for("index"))

    try:
        stats = fetch_report_stats(period)

        if file_type == "pdf":
            filepath, _ = generate_pdf_report(stats)
        else:
            filepath, _ = generate_txt_report(stats)

        return send_file(filepath, as_attachment=True)

    except Exception as exc:
        return render_template(
            "index.html",
            db_status={
                "ok": False,
                "message": str(exc)
            }
        )


# ==========================
# Auto Browser Launch
# ==========================
def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000")


# ==========================
# Main
# ==========================
if __name__ == "__main__":

    threading.Timer(2, open_browser).start()

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False,
        use_reloader=False
    )