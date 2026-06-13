"""Performance graph generation using Matplotlib."""

import matplotlib.pyplot as plt
from matplotlib.figure import Figure


def _apply_dark_theme(fig, ax):
    """Apply dark theme styling to a matplotlib figure."""
    fig.patch.set_facecolor("#0f1419")
    ax.set_facecolor("#1a2332")
    ax.tick_params(colors="#94a3b8")
    ax.xaxis.label.set_color("#f1f5f9")
    ax.yaxis.label.set_color("#f1f5f9")
    ax.title.set_color("#f1f5f9")
    for spine in ax.spines.values():
        spine.set_color("#334155")
    ax.grid(True, alpha=0.2, color="#64748b")


def create_performance_graph(logs):
    """Create a multi-line performance trend graph."""
    fig = Figure(figsize=(10, 5), dpi=100)
    ax = fig.add_subplot(111)

    if not logs:
        ax.text(
            0.5, 0.5,
            "No data available.\nSave some logs first!",
            ha="center", va="center",
            fontsize=14, color="#94a3b8",
            transform=ax.transAxes,
        )
        _apply_dark_theme(fig, ax)
        ax.set_xticks([])
        ax.set_yticks([])
        return fig

    times = [row["log_time"].strftime("%H:%M") for row in logs]
    cpu = [row["cpu_usage"] for row in logs]
    ram = [row["ram_usage"] for row in logs]
    disk = [row["disk_usage"] for row in logs]

    ax.plot(times, cpu, marker="o", linewidth=2, markersize=4,
            color="#00d4aa", label="CPU Usage (%)")
    ax.plot(times, ram, marker="s", linewidth=2, markersize=4,
            color="#3b82f6", label="RAM Usage (%)")
    ax.plot(times, disk, marker="^", linewidth=2, markersize=4,
            color="#8b5cf6", label="Disk Usage (%)")

    ax.set_title("Performance Trends Over Time", fontsize=14, fontweight="bold", pad=15)
    ax.set_xlabel("Time")
    ax.set_ylabel("Usage (%)")
    ax.set_ylim(0, 100)
    ax.legend(loc="upper right", facecolor="#1a2332", edgecolor="#334155",
              labelcolor="#f1f5f9")

    if len(times) > 8:
        ax.tick_params(axis="x", rotation=45)

    _apply_dark_theme(fig, ax)
    fig.tight_layout()
    return fig


def create_single_metric_graph(logs, metric="cpu_usage", title="CPU Usage Trend", color="#00d4aa"):
    """Create a single metric trend graph."""
    fig = Figure(figsize=(8, 4), dpi=100)
    ax = fig.add_subplot(111)

    if not logs:
        ax.text(
            0.5, 0.5, "No data available.",
            ha="center", va="center", fontsize=14, color="#94a3b8",
            transform=ax.transAxes,
        )
        _apply_dark_theme(fig, ax)
        return fig

    times = [row["log_time"].strftime("%H:%M") for row in logs]
    values = [row[metric] for row in logs]

    ax.fill_between(range(len(times)), values, alpha=0.15, color=color)
    ax.plot(range(len(times)), values, marker="o", linewidth=2.5,
            markersize=5, color=color)

    ax.set_title(title, fontsize=13, fontweight="bold", pad=12)
    ax.set_xticks(range(len(times)))
    ax.set_xticklabels(times, rotation=45 if len(times) > 6 else 0)
    ax.set_ylabel("Usage (%)")
    ax.set_ylim(0, 100)

    _apply_dark_theme(fig, ax)
    fig.tight_layout()
    return fig
