// Lightweight SVG chart helpers (bar + sparkline)

export function barChart(labels, values, opts = {}) {
  const w = opts.width || 560;
  const h = opts.height || 180;
  const pad = 26;
  const max = Math.max(...values, 1) * 1.1;
  const n = labels.length;
  const bw = (w - pad * 2) / n;
  const color = opts.color || "#1d7f63";
  const bars = values.map((v, i) => {
    const bh = (v / max) * (h - pad * 2);
    const x = pad + i * bw + bw * 0.15;
    const y = h - pad - bh;
    return `<rect x="${x.toFixed(1)}" y="${y.toFixed(1)}" width="${(bw * 0.7).toFixed(1)}" height="${bh.toFixed(1)}" fill="${color}" rx="2"><title>${labels[i]}: ${v}</title></rect>
    <text x="${(x + bw * 0.35).toFixed(1)}" y="${(y - 4).toFixed(1)}" font-size="10" text-anchor="middle" fill="#5c6b68">${v}</text>
    <text x="${(x + bw * 0.35).toFixed(1)}" y="${(h - 8).toFixed(1)}" font-size="9.5" text-anchor="middle" fill="#8d9b98">${labels[i]}</text>`;
  }).join("");
  return `<svg viewBox="0 0 ${w} ${h}" style="width:100%;height:auto"><rect x="0" y="0" width="${w}" height="${h}" fill="#fff" rx="8"/><line x1="${pad}" y1="${h - pad}" x2="${w - pad}" y2="${h - pad}" stroke="#e3dcd0"/><line x1="${pad}" y1="${pad}" x2="${pad}" y2="${h - pad}" stroke="#e3dcd0"/>${bars}</svg>`;
}

export function sparkline(values, opts = {}) {
  if (!values || values.length < 2) return `<div class="muted small">Not enough data</div>`;
  const w = opts.width || 260;
  const h = opts.height || 60;
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const pts = values.map((v, i) => {
    const x = (i / (values.length - 1)) * (w - 10) + 5;
    const y = h - 8 - ((v - min) / range) * (h - 16);
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(" ");
  const color = opts.color || "#13614d";
  return `<svg viewBox="0 0 ${w} ${h}" style="width:100%;height:auto"><polyline class="spark" points="${pts}" style="stroke:${color}"/></svg>`;
}

export function horizontalBars(items, opts = {}) {
  // items: [{label, value, max}]
  const vmax = opts.max || Math.max(...items.map((i) => i.value), 1);
  return `<div class="vstack">` + items.map((i) => `
    <div>
      <div class="row space-between small"><b>${i.label}</b><span class="muted">${i.value}${i.suffix || ""}</span></div>
      <div style="background:#f2ead9;border-radius:6px;height:10px"><div style="width:${Math.min(100, (i.value / vmax) * 100).toFixed(0)}%;background:${i.color || "#1d7f63"};height:10px;border-radius:6px"></div></div>
    </div>`).join("") + `</div>`;
}