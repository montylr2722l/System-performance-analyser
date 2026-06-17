const setText = (id, value) => {
  const element = document.getElementById(id);
  if (element) element.textContent = value;
};

const setMeter = (id, value) => {
  const element = document.getElementById(id);
  if (element) element.style.width = `${Math.max(0, Math.min(100, value || 0))}%`;
};

const percent = (value) => (value === null || value === undefined ? "N/A" : `${Number(value).toFixed(1)}%`);

const escapeHtml = (value) => String(value ?? "").replace(/[&<>"']/g, (char) => ({
  "&": "&amp;",
  "<": "&lt;",
  ">": "&gt;",
  "\"": "&quot;",
  "'": "&#039;",
}[char]));

async function loadMetrics() {
  const status = document.getElementById("status-message");
  try {
    const response = await fetch("/api/metrics");
    const data = await response.json();
    if (!data.ok) throw new Error(data.error || "Unable to load metrics");

    const m = data.metrics;
    const health = m.health || {};
    setText("health-score", health.score === undefined ? "--" : `${health.score}/100`);
    setText("health-detail", `${health.label || "--"} - ${health.summary || "No score available"}`);
    setText("health-pill", `${health.risk_level || "--"}`);
    setMeter("health-bar", health.score || 0);

    setText("cpu-value", percent(m.cpu_usage));
    setText("cpu-detail", `${m.cpu_cores} cores | ${m.cpu_frequency_mhz} MHz`);
    setMeter("cpu-bar", m.cpu_usage);

    setText("ram-value", percent(m.ram_usage));
    setText("ram-detail", `${m.ram_used} / ${m.ram_total} used`);
    setMeter("ram-bar", m.ram_usage);

    setText("disk-value", percent(m.disk_usage));
    setText("disk-detail", `${m.disk_used} / ${m.disk_total} used`);
    setMeter("disk-bar", m.disk_usage);

    setText("battery-value", m.battery === null ? "N/A" : percent(m.battery));
    setText("battery-detail", m.battery_status);
    setMeter("battery-bar", m.battery || 0);

    setText("network-sent", m.network_sent);
    setText("network-received", m.network_received);
    setText("last-updated", data.timestamp);
    setText("system-os", data.system.os);
    setText("system-host", data.system.hostname);
    setText("system-uptime", data.system.uptime);

    const tbody = document.getElementById("process-table");
    if (tbody) {
      tbody.innerHTML = data.processes.map((proc) => `
        <tr>
          <td>${escapeHtml(proc.name || "Unknown")}</td>
          <td>${proc.pid}</td>
          <td title="Raw multi-core value: ${Number(proc.raw_cpu_percent || 0).toFixed(1)}%">${Number(proc.cpu_percent || 0).toFixed(1)}%</td>
          <td>${Number(proc.memory_percent || 0).toFixed(1)}%</td>
        </tr>
      `).join("");
    }

    if (status) status.textContent = `Last updated: ${data.timestamp}`;
  } catch (error) {
    if (status) status.textContent = `Error: ${error.message}`;
  }
}

async function saveLog() {
  const status = document.getElementById("status-message");
  if (status) status.textContent = "Saving log...";
  try {
    const response = await fetch("/api/save-log", { method: "POST" });
    const data = await response.json();
    if (!data.ok) throw new Error(data.error || "Unable to save log");
    if (status) status.textContent = `Log saved successfully. ID: ${data.log_id}`;
  } catch (error) {
    if (status) status.textContent = `Save failed: ${error.message}`;
  }
}

let performanceChart;

async function loadChart() {
  const canvas = document.getElementById("performance-chart");
  const status = document.getElementById("chart-status");
  if (!canvas || !window.Chart) return;

  try {
    const response = await fetch("/api/graph-data");
    const data = await response.json();
    if (!data.ok) throw new Error(data.error || "Unable to load graph data");

    if (performanceChart) performanceChart.destroy();
    performanceChart = new Chart(canvas, {
      type: "line",
      data: {
        labels: data.labels,
        datasets: [
          { label: "CPU %", data: data.cpu, borderColor: "#22d3ee", backgroundColor: "rgba(34, 211, 238, 0.12)", tension: 0.35 },
          { label: "RAM %", data: data.ram, borderColor: "#a3e635", backgroundColor: "rgba(163, 230, 53, 0.1)", tension: 0.35 },
          { label: "Disk %", data: data.disk, borderColor: "#f97316", backgroundColor: "rgba(249, 115, 22, 0.1)", tension: 0.35 },
        ],
      },
      options: {
        maintainAspectRatio: false,
        responsive: true,
        scales: {
          x: { ticks: { color: "#a1a1aa", maxRotation: 0 }, grid: { color: "#27272a" } },
          y: { min: 0, max: 100, ticks: { color: "#a1a1aa" }, grid: { color: "#27272a" } },
        },
        plugins: {
          legend: { labels: { color: "#e4e4e7" } },
        },
      },
    });
    if (status) status.textContent = data.labels.length ? "Showing last 50 saved logs." : "No saved logs yet.";
  } catch (error) {
    if (status) status.textContent = `Error: ${error.message}`;
  }
}

document.getElementById("refresh-btn")?.addEventListener("click", loadMetrics);
document.getElementById("save-log-btn")?.addEventListener("click", saveLog);
document.getElementById("reload-chart-btn")?.addEventListener("click", loadChart);

if (document.getElementById("cpu-value")) {
  loadMetrics();
  setInterval(loadMetrics, 3000);
}

if (document.getElementById("performance-chart")) {
  loadChart();
}
