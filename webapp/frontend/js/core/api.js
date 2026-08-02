// Porta 5055: no macOS o AirPlay ocupa a 5000 e devolve 403.
export const API_BASE = "http://localhost:5055/api";

export async function apiGet(path) {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) throw new Error(`Falha ao buscar ${path}`);
  return res.json();
}

export async function apiPost(path, body) {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.erro || "Erro inesperado ao salvar.");
  return data;
}
