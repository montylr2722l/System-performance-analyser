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


def collect_all_metrics():
    """Collect all system performance metrics."""
    cpu = get_cpu_info()
    ram = get_ram_info()
    disk = get_disk_info()
    network = get_network_info()
    battery = get_battery_info()

    return {
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
