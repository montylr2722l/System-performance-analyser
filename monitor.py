"""System performance data collection using psutil."""

import platform
import psutil


def _format_bytes(value):
    """Convert bytes to human-readable format."""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024:
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} PB"


def get_cpu_info():
    """Collect CPU usage, cores, and frequency."""
    freq = psutil.cpu_freq()
    return {
        "usage": psutil.cpu_percent(interval=0.5),
        "cores": psutil.cpu_count(logical=False) or psutil.cpu_count(),
        "logical_cores": psutil.cpu_count(logical=True),
        "frequency_mhz": round(freq.current, 0) if freq else 0,
    }


def get_ram_info():
    """Collect RAM statistics."""
    mem = psutil.virtual_memory()
    return {
        "total": mem.total,
        "used": mem.used,
        "available": mem.available,
        "usage": mem.percent,
        "total_str": _format_bytes(mem.total),
        "used_str": _format_bytes(mem.used),
        "available_str": _format_bytes(mem.available),
    }


def get_disk_info():
    """Collect disk usage for the primary partition."""
    root = "C:\\" if platform.system() == "Windows" else "/"
    disk = psutil.disk_usage(root)
    return {
        "total": disk.total,
        "used": disk.used,
        "free": disk.free,
        "usage": disk.percent,
        "total_str": _format_bytes(disk.total),
        "used_str": _format_bytes(disk.used),
        "free_str": _format_bytes(disk.free),
    }


def get_network_info():
    """Collect network I/O statistics."""
    net = psutil.net_io_counters()
    return {
        "bytes_sent": net.bytes_sent,
        "bytes_received": net.bytes_recv,
        "sent_str": _format_bytes(net.bytes_sent),
        "received_str": _format_bytes(net.bytes_recv),
    }


def get_battery_info():
    """Collect battery status (laptops only)."""
    battery = psutil.sensors_battery()
    if battery is None:
        return {
            "available": False,
            "percent": None,
            "charging": None,
            "status": "N/A (Desktop PC)",
        }
    return {
        "available": True,
        "percent": battery.percent,
        "charging": battery.power_plugged,
        "status": "Charging" if battery.power_plugged else "On Battery",
    }


def get_system_info():
    """Collect basic system information."""
    boot = psutil.boot_time()
    from datetime import datetime

    uptime_seconds = datetime.now().timestamp() - boot
    hours, remainder = divmod(int(uptime_seconds), 3600)
    minutes, _ = divmod(remainder, 60)

    return {
        "os": f"{platform.system()} {platform.release()}",
        "hostname": platform.node(),
        "processor": platform.processor() or "Unknown CPU",
        "uptime": f"{hours}h {minutes}m",
    }


def get_top_processes(limit=8):
    """Return top processes sorted by CPU usage."""
    processes = []
    logical_cpus = psutil.cpu_count(logical=True) or 1
    for proc in psutil.process_iter(["pid", "name"]):
        try:
            with proc.oneshot():
                cpu = proc.cpu_percent(interval=0)
                mem = proc.memory_percent()
                name = proc.info.get("name") or proc.name()
            if proc.pid == 0 or (name and name.lower() == "system idle process"):
                continue
            normalized_cpu = min(cpu / logical_cpus, 100)
            processes.append({
                "pid": proc.pid,
                "name": name,
                "cpu_percent": normalized_cpu,
                "raw_cpu_percent": cpu,
                "memory_percent": mem,
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    processes.sort(
        key=lambda p: (p["cpu_percent"] or 0, p["memory_percent"] or 0),
        reverse=True,
    )
    return processes[:limit]


def get_health_score(metrics):
    """Return an overall laptop health score from current performance pressure."""
    risk = 0
    factors = []

    cpu = metrics["cpu_usage"]
    ram = metrics["ram_usage"]
    disk = metrics["disk_usage"]
    battery = metrics.get("battery")
    on_battery = metrics.get("battery_charging") is False

    if cpu >= 90:
        risk += 30
        factors.append("CPU usage is critical")
    elif cpu >= 70:
        risk += 18
        factors.append("CPU usage is high")
    elif cpu >= 50:
        risk += 8
        factors.append("CPU usage is moderate")

    if ram >= 90:
        risk += 30
        factors.append("RAM usage is critical")
    elif ram >= 75:
        risk += 18
        factors.append("RAM usage is high")
    elif ram >= 60:
        risk += 8
        factors.append("RAM usage is moderate")

    if disk >= 90:
        risk += 22
        factors.append("Disk is nearly full")
    elif disk >= 80:
        risk += 12
        factors.append("Disk space is getting tight")
    elif disk >= 70:
        risk += 6
        factors.append("Disk usage is moderate")

    if battery is not None and on_battery:
        if battery <= 15:
            risk += 18
            factors.append("Battery is very low")
        elif battery <= 30:
            risk += 10
            factors.append("Battery is low")

    score = max(0, min(100, 100 - risk))
    if score >= 85:
        label = "Excellent"
        risk_level = "Low Risk"
        summary = "Laptop is in good condition."
    elif score >= 70:
        label = "Good"
        risk_level = "Low-Medium Risk"
        summary = "Laptop is healthy with some resource pressure."
    elif score >= 50:
        label = "Fair"
        risk_level = "Medium Risk"
        summary = "Laptop is usable, but performance pressure is noticeable."
    else:
        label = "Poor"
        risk_level = "High Risk"
        summary = "Laptop is under heavy load and may feel slow."

    return {
        "score": score,
        "label": label,
        "risk_level": risk_level,
        "summary": summary,
        "factors": factors or ["No major performance risk detected"],
    }


def collect_all_metrics():
    """Collect all system performance metrics."""
    cpu = get_cpu_info()
    ram = get_ram_info()
    disk = get_disk_info()
    network = get_network_info()
    battery = get_battery_info()

    metrics = {
        "cpu_usage": cpu["usage"],
        "cpu_cores": cpu["cores"],
        "cpu_logical_cores": cpu["logical_cores"],
        "cpu_frequency_mhz": cpu["frequency_mhz"],
        "ram_usage": ram["usage"],
        "ram_total": ram["total_str"],
        "ram_used": ram["used_str"],
        "ram_available": ram["available_str"],
        "disk_usage": disk["usage"],
        "disk_total": disk["total_str"],
        "disk_used": disk["used_str"],
        "disk_free": disk["free_str"],
        "bytes_sent": network["bytes_sent"],
        "bytes_received": network["bytes_received"],
        "network_sent": network["sent_str"],
        "network_received": network["received_str"],
        "battery": battery["percent"] if battery["available"] else None,
        "battery_status": battery["status"],
        "battery_charging": battery["charging"],
    }
    metrics["health"] = get_health_score(metrics)
    return metrics
