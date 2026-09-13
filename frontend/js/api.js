// API client for the Oasis backend

const API = window.OASIS_API_BASE || localStorage.getItem("oasis_api_base") || "/api/v1";

function token() {
  return localStorage.getItem("oasis_token") || "";
}

function setToken(t) {
  localStorage.setItem("oasis_token", t);
}

function clearToken() {
  localStorage.removeItem("oasis_token");
  localStorage.removeItem("oasis_user");
}

async function request(path, { method = "GET", body, multipart } = {}) {
  const headers = {};
  const t = token();
  if (t) headers["Authorization"] = "Bearer " + t;
  if (multipart) {
    // body is FormData
    const res = await fetch(API + path, { method, headers, body: multipart });
    return handle(res);
  }
  if (body !== undefined) {
    headers["Content-Type"] = "application/json";
  }
  const res = await fetch(API + path, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  return handle(res);
}

async function handle(res) {
  if (res.status === 401) {
    clearToken();
    window.dispatchEvent(new Event("auth:logout"));
    throw new Error("Session expired. Please sign in again.");
  }
  const text = await res.text();
  let data;
  try {
    data = text ? JSON.parse(text) : {};
  } catch {
    data = { message: text };
  }
  if (!res.ok) {
    const err = new Error(data.detail || data.message || ("Request failed (" + res.status + ")"));
    err.status = res.status;
    err.data = data;
    throw err;
  }
  return data;
}

export const api = {
  get: (p) => request(p),
  post: (p, body) => request(p, { method: "POST", body }),
  patch: (p, body) => request(p, { method: "PATCH", body }),
  del: (p) => request(p, { method: "DELETE" }),
  upload: (p, formData) => request(p, { method: "POST", multipart: formData }),
  token,
  setToken,
  clearToken,
};