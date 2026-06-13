"""MySQL database connection and operations."""

from datetime import datetime

import mysql.connector
from mysql.connector import Error

from settings import get_db_config


def get_connection():
    """Create and return a MySQL connection."""
    return mysql.connector.connect(**get_db_config())


def init_database():
    """Create database and table if they do not exist."""
    config = get_db_config()
    database_name = config.pop("database")

    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()

    cursor.execute(
        f"CREATE DATABASE IF NOT EXISTS {database_name} "
        "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
    )
    cursor.execute(f"USE {database_name}")

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS performance_logs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            log_time DATETIME NOT NULL,
            cpu_usage FLOAT NOT NULL,
            ram_usage FLOAT NOT NULL,
            disk_usage FLOAT NOT NULL,
            battery FLOAT DEFAULT NULL,
            bytes_sent BIGINT DEFAULT 0,
            bytes_received BIGINT DEFAULT 0
        )
        """
    )

    conn.commit()
    cursor.close()
    conn.close()


def test_connection():
    """Test MySQL connection. Returns (success, message)."""
    try:
        init_database()
        conn = get_connection()
        conn.close()
        return True, "Connected successfully"
    except Error as exc:
        return False, str(exc)


def insert_log(metrics):
    """Insert a performance log record."""
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        INSERT INTO performance_logs
        (log_time, cpu_usage, ram_usage, disk_usage, battery, bytes_sent, bytes_received)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    values = (
        datetime.now(),
        metrics["cpu_usage"],
        metrics["ram_usage"],
        metrics["disk_usage"],
        metrics.get("battery"),
        metrics["bytes_sent"],
        metrics["bytes_received"],
    )

    cursor.execute(query, values)
    conn.commit()
    log_id = cursor.lastrowid
    cursor.close()
    conn.close()
    return log_id


def fetch_all_logs(limit=100):
    """Fetch performance logs, newest first."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT id, log_time, cpu_usage, ram_usage, disk_usage,
               battery, bytes_sent, bytes_received
        FROM performance_logs
        ORDER BY log_time DESC
        LIMIT %s
        """,
        (limit,),
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def fetch_logs_for_graph(limit=50):
    """Fetch logs ordered by time for graph plotting."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT log_time, cpu_usage, ram_usage, disk_usage
        FROM performance_logs
        ORDER BY log_time ASC
        LIMIT %s
        """,
        (limit,),
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def fetch_report_stats(period="daily"):
    """Fetch aggregated statistics for report generation."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    if period == "weekly":
        date_filter = "log_time >= DATE_SUB(NOW(), INTERVAL 7 DAY)"
        period_label = "Weekly"
    else:
        date_filter = "DATE(log_time) = CURDATE()"
        period_label = "Daily"

    cursor.execute(
        f"""
        SELECT
            COUNT(*) AS total_records,
            AVG(cpu_usage) AS avg_cpu,
            MAX(cpu_usage) AS max_cpu,
            MIN(cpu_usage) AS min_cpu,
            AVG(ram_usage) AS avg_ram,
            MAX(ram_usage) AS max_ram,
            MIN(ram_usage) AS min_ram,
            AVG(disk_usage) AS avg_disk,
            MAX(disk_usage) AS max_disk,
            MIN(disk_usage) AS min_disk
        FROM performance_logs
        WHERE {date_filter}
        """
    )
    stats = cursor.fetchone()
    cursor.close()
    conn.close()
    stats["period_label"] = period_label
    return stats
