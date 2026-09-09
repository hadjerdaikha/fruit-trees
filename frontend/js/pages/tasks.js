// Tasks page — list, create, filter by status/priority

import { api } from "../api.js";
import { esc, fmtDate, pill, toast, getStore } from "../ui.js";

const farmId = Number(getStore("oasis_farm_id", 1));

export const page = async () => {
  let tasks = [], zones = [];
  try { tasks = await api.get(`/tasks?farm_id=${farmId}&limit=50`); } catch {}
  try { const m = await api.get(`/farms/${farmId}/map`); m.fields.forEach((f) => f.blocks.forEach((b) => b.zones.forEach((z) => zones.push({ id: z.id, name: z.name })))); } catch {}

  const statusOpts = ["open", "in_progress", "done", "overdue"];
  const active = tasks.filter((t) => t.status !== "done");

  return `
  <h2 style="margin:0 0 4px">Tasks</h2>
  <div class="grid grid-3 mb">
    <div class="card kpi"><div class="kpi-label">Open</div><div class="kpi-value">${active.length}</div></div>
    <div class="card kpi"><div class="kpi-label">Done</div><div class="kpi-value">${tasks.filter((t) => t.status === "done").length}</div></div>
    <div class="card kpi"><div class="kpi-label">Zones</div><div class="kpi-value">${zones.length}</div></div>
  </div>
  <section class="card mb">
    <div class="row space-between">
      <h3 style="margin:0">All tasks</h3>
      <button class="btn" id="new-task-btn">+ New task</button>
    </div>
    <div class="hstack mt mb small">
      ${["all", "open", "in_progress", "done", "overdue"].map((s) => `<button class="layer-pill ${s === "all" ? "active" : ""}" data-filter="${s}">${s.replace("_", " ")}</button>`).join("")}
    </div>
    <table class="data"><thead><tr><th>Title</th><th>Priority</th><th>Zone</th><th>Due</th><th>Status</th></tr></thead>
    <tbody id="task-tbody">${taskRows(tasks)}</tbody></table>
  </section>
  <div id="task-modal" data-modal-root></div>`;
};

export const mount = () => {
  document.getElementById("new-task-btn")?.addEventListener("click", () => openNewTask(zones));
  document.querySelectorAll("[data-filter]").forEach((b) => b.addEventListener("click", () => filterTasks(b.dataset.filter)));
};

let allTasks = [];

function taskRows(tasks) {
  allTasks = tasks;
  return tasks.length ? tasks.map((t) => `<tr>
    <td><b>${esc(t.title)}</b>${t.description ? `<div class="small muted">${esc(t.description)}</div>` : ""}</td>
    <td>${pill(t.priority || "medium", t.priority || "medium")}</td>
    <td class="small">${esc(t.zone_name || t.zone_id || "—")}</td>
    <td class="small muted">${fmtDate(t.due_date)}</td>
    <td>${pill(t.status || "open", t.status || "open")}</td>
  </tr>`).join("") : '<tr><td colspan="5"><div class="empty">No tasks</div></td></tr>';
}

function openNewTask(zones) {
  const opts = zones.map((z) => `<option value="${z.id}">${esc(z.name)}</option>`).join("");
  import("../ui.js").then(({ openModal, closeModal }) => {
    openModal(`<h3>New task</h3>
      <label class="fld"><div class="fld-k">Title</div><input class="input" id="tt-title" /></label>
      <label class="fld"><div class="fld-k">Description</div><textarea class="input" id="tt-desc" rows="2"></textarea></label>
      <div class="row"><label class="fld"><div class="fld-k">Priority</div><select class="input" id="tt-pri"><option>low</option><option selected>medium</option><option>high</option><option>critical</option></select></label>
      <label class="fld"><div class="fld-k">Zone</div><select class="input" id="tt-zone">${opts}</select></label></div>
      <label class="fld"><div class="fld-k">Due</div><input type="date" class="input" id="tt-due" /></label>
      <div class="hstack mt"><button class="btn" id="tt-save">Create</button><button class="btn secondary" data-modal-close>Cancel</button></div>`);
    document.getElementById("tt-save").addEventListener("click", async () => {
      try {
        await api.post("/tasks", {
          title: document.getElementById("tt-title").value || "Task",
          description: document.getElementById("tt-desc").value || "",
          priority: document.getElementById("tt-pri").value,
          zone_id: Number(document.getElementById("tt-zone").value) || undefined,
          due_date: document.getElementById("tt-due").value || undefined,
          farm_id: farmId,
        });
        toast("Task created");
        closeModal();
        location.reload();
      } catch (e) { toast(e.message, "error"); }
    });
  });
}

function filterTasks(filter) {
  const rows = allTasks.filter((t) => filter === "all" || t.status === filter);
  document.getElementById("task-tbody").innerHTML = taskRows(rows);
  document.querySelectorAll("[data-filter]").forEach((b) => b.classList.toggle("active", b.dataset.filter === filter));
}