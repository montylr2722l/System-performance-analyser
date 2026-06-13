"""System Performance Analyser - Desktop GUI Application."""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from config import COLORS, AUTO_REFRESH_INTERVAL_MS
from settings import get_db_config, save_db_config, test_db_config
from monitor import collect_all_metrics
from database import (
    init_database,
    test_connection,
    insert_log,
    fetch_all_logs,
    fetch_logs_for_graph,
    fetch_report_stats,
)
from graphs import create_performance_graph
from report import generate_txt_report, generate_pdf_report


class MetricCard(tk.Frame):
    """A styled card widget showing a metric with a progress bar."""

    def __init__(self, parent, title, icon, accent_color, **kwargs):
        super().__init__(
            parent,
            bg=COLORS["bg_card"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
            **kwargs,
        )

        self.accent_color = accent_color
        self.value_var = tk.StringVar(value="--")
        self.detail_var = tk.StringVar(value="")
        self.progress_var = tk.DoubleVar(value=0)

        header = tk.Frame(self, bg=COLORS["bg_card"])
        header.pack(fill="x", padx=16, pady=(14, 4))

        tk.Label(
            header, text=icon, font=("Segoe UI", 16),
            bg=COLORS["bg_card"], fg=accent_color,
        ).pack(side="left")

        tk.Label(
            header, text=title, font=("Segoe UI", 10),
            bg=COLORS["bg_card"], fg=COLORS["text_secondary"],
        ).pack(side="left", padx=(8, 0))

        tk.Label(
            self, textvariable=self.value_var,
            font=("Segoe UI", 28, "bold"),
            bg=COLORS["bg_card"], fg=COLORS["text_primary"],
        ).pack(anchor="w", padx=16)

        style = ttk.Style()
        style.configure(
            f"{title}.Horizontal.TProgressbar",
            troughcolor=COLORS["bg_dark"],
            background=accent_color,
            thickness=6,
        )
        self.progress = ttk.Progressbar(
            self, variable=self.progress_var,
            maximum=100, length=200,
            style=f"{title}.Horizontal.TProgressbar",
        )
        self.progress.pack(fill="x", padx=16, pady=(4, 2))

        tk.Label(
            self, textvariable=self.detail_var,
            font=("Segoe UI", 9),
            bg=COLORS["bg_card"], fg=COLORS["text_muted"],
        ).pack(anchor="w", padx=16, pady=(0, 14))

    def update_metric(self, value, detail="", is_percent=True):
        if is_percent and value is not None:
            self.value_var.set(f"{value:.1f}%")
            self.progress_var.set(value)
        elif value is not None:
            self.value_var.set(str(value))
            self.progress_var.set(0)
        else:
            self.value_var.set("N/A")
            self.progress_var.set(0)
        self.detail_var.set(detail)


class StyledButton(tk.Button):
    """Custom styled button."""

    def __init__(self, parent, text, command, color=None, **kwargs):
        super().__init__(
            parent,
            text=text,
            command=command,
            font=("Segoe UI", 10, "bold"),
            bg=color or COLORS["accent"],
            fg="#ffffff",
            activebackground=COLORS["accent_blue"],
            activeforeground="#ffffff",
            relief="flat",
            cursor="hand2",
            padx=18,
            pady=10,
            **kwargs,
        )
        self.bind("<Enter>", lambda e: self.config(bg=COLORS["accent_blue"]))
        self.bind("<Leave>", lambda e: self.config(bg=color or COLORS["accent"]))


class SystemPerformanceApp:
    """Main application window."""

    def __init__(self, root):
        self.root = root
        self.root.title("System Performance Analyser")
        self.root.geometry("960x720")
        self.root.minsize(860, 640)
        self.root.configure(bg=COLORS["bg_dark"])

        self.current_metrics = {}
        self.auto_refresh_enabled = tk.BooleanVar(value=True)
        self.refresh_job = None

        self._setup_styles()
        self._build_ui()
        self._check_database()
        self.refresh_metrics()

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Treeview",
            background=COLORS["bg_card"],
            foreground=COLORS["text_primary"],
            fieldbackground=COLORS["bg_card"],
            borderwidth=0,
            font=("Segoe UI", 10),
            rowheight=30,
        )
        style.configure(
            "Treeview.Heading",
            background=COLORS["bg_dark"],
            foreground=COLORS["text_secondary"],
            font=("Segoe UI", 10, "bold"),
            borderwidth=0,
        )
        style.map(
            "Treeview",
            background=[("selected", COLORS["accent_blue"])],
            foreground=[("selected", "#ffffff")],
        )

    def _build_ui(self):
        self._build_header()
        self._build_metrics_grid()
        self._build_network_section()
        self._build_action_buttons()
        self._build_status_bar()

    def _build_header(self):
        header = tk.Frame(self.root, bg=COLORS["bg_dark"])
        header.pack(fill="x", padx=24, pady=(20, 8))

        tk.Label(
            header,
            text="⚡ SYSTEM PERFORMANCE ANALYSER",
            font=("Segoe UI", 20, "bold"),
            bg=COLORS["bg_dark"],
            fg=COLORS["text_primary"],
        ).pack(side="left")

        self.time_label = tk.Label(
            header, text="",
            font=("Segoe UI", 10),
            bg=COLORS["bg_dark"],
            fg=COLORS["text_muted"],
        )
        self.time_label.pack(side="right", pady=8)

        tk.Label(
            header,
            text="Real-time system monitoring & analytics",
            font=("Segoe UI", 10),
            bg=COLORS["bg_dark"],
            fg=COLORS["text_secondary"],
        ).pack(side="left", padx=(12, 0), pady=(8, 0))

    def _build_metrics_grid(self):
        grid_frame = tk.Frame(self.root, bg=COLORS["bg_dark"])
        grid_frame.pack(fill="both", expand=True, padx=24, pady=12)

        for i in range(2):
            grid_frame.columnconfigure(i, weight=1, uniform="card")
        for i in range(2):
            grid_frame.rowconfigure(i, weight=1, uniform="card")

        self.cpu_card = MetricCard(grid_frame, "CPU Usage", "🖥", COLORS["accent"])
        self.cpu_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=(0, 8))

        self.ram_card = MetricCard(grid_frame, "RAM Usage", "💾", COLORS["accent_blue"])
        self.ram_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=(0, 8))

        self.disk_card = MetricCard(grid_frame, "Disk Usage", "💿", COLORS["accent_purple"])
        self.disk_card.grid(row=1, column=0, sticky="nsew", padx=(0, 8), pady=(8, 0))

        self.battery_card = MetricCard(grid_frame, "Battery", "🔋", COLORS["accent_orange"])
        self.battery_card.grid(row=1, column=1, sticky="nsew", padx=(8, 0), pady=(8, 0))

    def _build_network_section(self):
        net_frame = tk.Frame(
            self.root, bg=COLORS["bg_card"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )
        net_frame.pack(fill="x", padx=24, pady=(0, 12))

        inner = tk.Frame(net_frame, bg=COLORS["bg_card"])
        inner.pack(fill="x", padx=16, pady=12)

        tk.Label(
            inner, text="🌐  Network Activity",
            font=("Segoe UI", 11, "bold"),
            bg=COLORS["bg_card"], fg=COLORS["text_primary"],
        ).pack(side="left")

        self.sent_var = tk.StringVar(value="Sent: --")
        self.recv_var = tk.StringVar(value="Received: --")

        tk.Label(
            inner, textvariable=self.sent_var,
            font=("Segoe UI", 10),
            bg=COLORS["bg_card"], fg=COLORS["accent"],
        ).pack(side="right", padx=(20, 0))

        tk.Label(
            inner, textvariable=self.recv_var,
            font=("Segoe UI", 10),
            bg=COLORS["bg_card"], fg=COLORS["accent_blue"],
        ).pack(side="right")

    def _build_action_buttons(self):
        btn_frame = tk.Frame(self.root, bg=COLORS["bg_dark"])
        btn_frame.pack(fill="x", padx=24, pady=(0, 8))

        buttons = [
            ("🔄  Refresh", self.refresh_metrics, COLORS["accent"]),
            ("💾  Save Log", self.save_log, COLORS["success"]),
            ("📋  View History", self.show_history, COLORS["accent_blue"]),
            ("📊  Performance Graph", self.show_graph, COLORS["accent_purple"]),
            ("📄  Generate Report", self.show_report_dialog, COLORS["accent_orange"]),
            ("⚙  DB Settings", self.show_db_settings, COLORS["text_muted"]),
        ]

        for text, cmd, color in buttons:
            StyledButton(btn_frame, text, cmd, color=color).pack(
                side="left", padx=(0, 10), pady=4
            )

        auto_frame = tk.Frame(btn_frame, bg=COLORS["bg_dark"])
        auto_frame.pack(side="right")

        tk.Checkbutton(
            auto_frame,
            text="Auto Refresh (3s)",
            variable=self.auto_refresh_enabled,
            command=self._toggle_auto_refresh,
            font=("Segoe UI", 9),
            bg=COLORS["bg_dark"],
            fg=COLORS["text_secondary"],
            selectcolor=COLORS["bg_card"],
            activebackground=COLORS["bg_dark"],
            activeforeground=COLORS["text_primary"],
        ).pack()

    def _build_status_bar(self):
        status_frame = tk.Frame(self.root, bg=COLORS["bg_card"], height=32)
        status_frame.pack(fill="x", side="bottom")
        status_frame.pack_propagate(False)

        self.status_var = tk.StringVar(value="Ready")
        tk.Label(
            status_frame, textvariable=self.status_var,
            font=("Segoe UI", 9),
            bg=COLORS["bg_card"], fg=COLORS["text_muted"],
            anchor="w",
        ).pack(fill="x", padx=16, pady=6)

        self.db_status_var = tk.StringVar(value="DB: Checking...")
        db_label = tk.Label(
            status_frame, textvariable=self.db_status_var,
            font=("Segoe UI", 9),
            bg=COLORS["bg_card"], fg=COLORS["text_muted"],
            cursor="hand2",
        )
        db_label.pack(side="right", padx=16)
        db_label.bind("<Button-1>", lambda e: self.show_db_settings())

    def _check_database(self):
        try:
            init_database()
            ok, msg = test_connection()
            if ok:
                self.db_status_var.set("DB: Connected ✓")
            else:
                self.db_status_var.set("DB: Error — click to fix")
                self.root.after(300, lambda: self.show_db_settings(msg))
        except Exception as exc:
            self.db_status_var.set("DB: Error — click to fix")
            self.root.after(300, lambda: self.show_db_settings(str(exc)))

    def refresh_metrics(self):
        try:
            self.current_metrics = collect_all_metrics()
            m = self.current_metrics

            self.cpu_card.update_metric(
                m["cpu_usage"],
                f"{m['cpu_cores']} cores | {m['cpu_frequency_mhz']:.0f} MHz",
            )
            self.ram_card.update_metric(
                m["ram_usage"],
                f"{m['ram_used']} / {m['ram_total']} used",
            )
            self.disk_card.update_metric(
                m["disk_usage"],
                f"{m['disk_used']} / {m['disk_total']} used",
            )

            if m["battery"] is not None:
                self.battery_card.update_metric(
                    m["battery"],
                    m["battery_status"],
                )
            else:
                self.battery_card.update_metric(None, m["battery_status"], is_percent=False)

            self.sent_var.set(f"↑ Sent: {m['network_sent']}")
            self.recv_var.set(f"↓ Received: {m['network_received']}")

            now = datetime.now().strftime("%d-%m-%Y  %I:%M:%S %p")
            self.time_label.config(text=now)
            self.status_var.set(f"Last updated: {now}")

        except Exception as exc:
            self.status_var.set(f"Error: {exc}")

        if self.auto_refresh_enabled.get():
            self._schedule_refresh()

    def _schedule_refresh(self):
        if self.refresh_job:
            self.root.after_cancel(self.refresh_job)
        self.refresh_job = self.root.after(AUTO_REFRESH_INTERVAL_MS, self.refresh_metrics)

    def _toggle_auto_refresh(self):
        if self.auto_refresh_enabled.get():
            self._schedule_refresh()
        elif self.refresh_job:
            self.root.after_cancel(self.refresh_job)

    def save_log(self):
        if not self.current_metrics:
            messagebox.showinfo("Info", "Please refresh metrics first.")
            return
        try:
            log_id = insert_log(self.current_metrics)
            self.status_var.set(f"Log saved successfully (ID: {log_id})")
            messagebox.showinfo(
                "Success",
                f"Performance log saved!\n\n"
                f"CPU: {self.current_metrics['cpu_usage']:.1f}%\n"
                f"RAM: {self.current_metrics['ram_usage']:.1f}%\n"
                f"Disk: {self.current_metrics['disk_usage']:.1f}%",
            )
        except Exception as exc:
            error_msg = str(exc)
            if "1045" in error_msg or "Access denied" in error_msg:
                if messagebox.askyesno(
                    "Database Error",
                    f"Failed to save log:\n{error_msg}\n\n"
                    "MySQL password is incorrect.\nOpen Database Settings now?",
                ):
                    self.show_db_settings(error_msg)
            else:
                messagebox.showerror("Error", f"Failed to save log:\n{exc}")

    def show_history(self):
        try:
            logs = fetch_all_logs()
        except Exception as exc:
            messagebox.showerror("Error", f"Failed to fetch history:\n{exc}")
            return

        window = tk.Toplevel(self.root)
        window.title("Performance History")
        window.geometry("780x480")
        window.configure(bg=COLORS["bg_dark"])
        window.transient(self.root)

        tk.Label(
            window, text="📋  Performance History",
            font=("Segoe UI", 16, "bold"),
            bg=COLORS["bg_dark"], fg=COLORS["text_primary"],
        ).pack(pady=(16, 8))

        table_frame = tk.Frame(window, bg=COLORS["bg_dark"])
        table_frame.pack(fill="both", expand=True, padx=20, pady=(0, 16))

        columns = ("time", "cpu", "ram", "disk", "battery", "sent", "received")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)

        headings = {
            "time": ("Date & Time", 160),
            "cpu": ("CPU %", 70),
            "ram": ("RAM %", 70),
            "disk": ("Disk %", 70),
            "battery": ("Battery %", 80),
            "sent": ("Sent (MB)", 90),
            "received": ("Received (MB)", 100),
        }
        for col, (heading, width) in headings.items():
            tree.heading(col, text=heading)
            tree.column(col, width=width, anchor="center")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        if not logs:
            tree.insert("", "end", values=("No records found", "", "", "", "", "", ""))
        else:
            for row in logs:
                battery = f"{row['battery']:.0f}" if row["battery"] is not None else "N/A"
                sent_mb = row["bytes_sent"] / (1024 * 1024)
                recv_mb = row["bytes_received"] / (1024 * 1024)
                tree.insert("", "end", values=(
                    row["log_time"].strftime("%d-%m-%Y %I:%M %p"),
                    f"{row['cpu_usage']:.1f}",
                    f"{row['ram_usage']:.1f}",
                    f"{row['disk_usage']:.1f}",
                    battery,
                    f"{sent_mb:.1f}",
                    f"{recv_mb:.1f}",
                ))

        count_label = tk.Label(
            window,
            text=f"Total records: {len(logs)}",
            font=("Segoe UI", 9),
            bg=COLORS["bg_dark"], fg=COLORS["text_muted"],
        )
        count_label.pack(pady=(0, 12))

    def show_graph(self):
        try:
            logs = fetch_logs_for_graph()
        except Exception as exc:
            messagebox.showerror("Error", f"Failed to fetch data for graph:\n{exc}")
            return

        window = tk.Toplevel(self.root)
        window.title("Performance Graph")
        window.geometry("900x520")
        window.configure(bg=COLORS["bg_dark"])
        window.transient(self.root)

        tk.Label(
            window, text="📊  Performance Trends",
            font=("Segoe UI", 16, "bold"),
            bg=COLORS["bg_dark"], fg=COLORS["text_primary"],
        ).pack(pady=(16, 4))

        fig = create_performance_graph(logs)
        canvas = FigureCanvasTkAgg(fig, master=window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=16, pady=(0, 16))

    def show_report_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Generate Report")
        dialog.geometry("420x320")
        dialog.configure(bg=COLORS["bg_dark"])
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(
            dialog, text="📄  Generate Performance Report",
            font=("Segoe UI", 14, "bold"),
            bg=COLORS["bg_dark"], fg=COLORS["text_primary"],
        ).pack(pady=(20, 12))

        period_var = tk.StringVar(value="daily")

        period_frame = tk.Frame(dialog, bg=COLORS["bg_dark"])
        period_frame.pack(pady=8)

        for text, value in [("Daily Report", "daily"), ("Weekly Report", "weekly")]:
            tk.Radiobutton(
                period_frame, text=text, variable=period_var, value=value,
                font=("Segoe UI", 10),
                bg=COLORS["bg_dark"], fg=COLORS["text_primary"],
                selectcolor=COLORS["bg_card"],
                activebackground=COLORS["bg_dark"],
            ).pack(anchor="w", padx=40)

        preview = tk.Text(
            dialog, height=8, width=46,
            font=("Consolas", 9),
            bg=COLORS["bg_card"], fg=COLORS["text_primary"],
            relief="flat", wrap="word",
        )
        preview.pack(padx=20, pady=12)

        def generate(fmt):
            try:
                stats = fetch_report_stats(period_var.get())
                if fmt == "txt":
                    filepath, content = generate_txt_report(stats)
                else:
                    filepath, content = generate_pdf_report(stats)

                preview.delete("1.0", "end")
                preview.insert("1.0", content)
                messagebox.showinfo("Report Saved", f"Report saved to:\n{filepath}")
            except Exception as exc:
                messagebox.showerror("Error", f"Report generation failed:\n{exc}")

        btn_row = tk.Frame(dialog, bg=COLORS["bg_dark"])
        btn_row.pack(pady=(0, 16))

        StyledButton(btn_row, "Save as TXT", lambda: generate("txt"), COLORS["accent"]).pack(
            side="left", padx=8
        )
        StyledButton(btn_row, "Save as PDF", lambda: generate("pdf"), COLORS["accent_orange"]).pack(
            side="left", padx=8
        )

    def show_db_settings(self, error_msg=None):
        """Open dialog to configure MySQL connection."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Database Settings")
        dialog.geometry("460x420")
        dialog.configure(bg=COLORS["bg_dark"])
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)

        tk.Label(
            dialog, text="⚙  MySQL Database Settings",
            font=("Segoe UI", 14, "bold"),
            bg=COLORS["bg_dark"], fg=COLORS["text_primary"],
        ).pack(pady=(20, 8))

        if error_msg:
            tk.Label(
                dialog,
                text=f"Error: {error_msg[:120]}",
                font=("Segoe UI", 9),
                bg=COLORS["bg_dark"], fg=COLORS["danger"],
                wraplength=400,
            ).pack(pady=(0, 8))

        cfg = get_db_config()
        fields = {}
        form = tk.Frame(dialog, bg=COLORS["bg_dark"])
        form.pack(padx=24, pady=8, fill="x")

        for label, key in [
            ("Host", "host"), ("Port", "port"), ("Username", "user"),
            ("Password", "password"), ("Database", "database"),
        ]:
            row = tk.Frame(form, bg=COLORS["bg_dark"])
            row.pack(fill="x", pady=6)
            tk.Label(
                row, text=label, width=12, anchor="w",
                font=("Segoe UI", 10),
                bg=COLORS["bg_dark"], fg=COLORS["text_secondary"],
            ).pack(side="left")
            entry = tk.Entry(
                row, font=("Segoe UI", 10),
                bg=COLORS["bg_card"], fg=COLORS["text_primary"],
                insertbackground=COLORS["text_primary"],
                relief="flat", show="*" if key == "password" else "",
            )
            entry.insert(0, str(cfg.get(key, "")))
            entry.pack(side="left", fill="x", expand=True, ipady=6)
            fields[key] = entry

        status_var = tk.StringVar(value="Enter your MySQL root password and click Test Connection.")
        tk.Label(
            dialog, textvariable=status_var,
            font=("Segoe UI", 9), wraplength=400,
            bg=COLORS["bg_dark"], fg=COLORS["text_muted"],
        ).pack(pady=8)

        def test_and_save():
            config = {
                "host": fields["host"].get().strip(),
                "port": int(fields["port"].get().strip() or 3306),
                "user": fields["user"].get().strip(),
                "password": fields["password"].get(),
                "database": fields["database"].get().strip(),
            }
            ok, msg = test_db_config(config)
            if ok:
                save_db_config(**config)
                try:
                    init_database()
                    self.db_status_var.set("DB: Connected ✓")
                    status_var.set("Connected and saved successfully!")
                    messagebox.showinfo("Success", "MySQL connected!\nYou can now Save Log.")
                    dialog.destroy()
                except Exception as exc:
                    status_var.set(f"Saved but setup failed: {exc}")
            else:
                status_var.set(f"Connection failed: {msg}")

        btn_row = tk.Frame(dialog, bg=COLORS["bg_dark"])
        btn_row.pack(pady=(8, 16))
        StyledButton(btn_row, "Test & Save", test_and_save, COLORS["accent"]).pack(side="left", padx=8)
        StyledButton(btn_row, "Cancel", dialog.destroy, COLORS["text_muted"]).pack(side="left", padx=8)

        tk.Label(
            dialog,
            text="Tip: MySQL Workbench me jo password use karte ho,\n"
                 "wahi yahan daalo. XAMPP me aksar password blank hota hai.",
            font=("Segoe UI", 8),
            bg=COLORS["bg_dark"], fg=COLORS["text_muted"],
            justify="left",
        ).pack(pady=(0, 12))

    def on_close(self):
        if self.refresh_job:
            self.root.after_cancel(self.refresh_job)
        self.root.destroy()


def main():
    root = tk.Tk()
    app = SystemPerformanceApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
