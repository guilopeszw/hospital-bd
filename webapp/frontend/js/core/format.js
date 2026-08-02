export function fmtData(iso) {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleString("pt-BR", { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" });
}

export function fmtDataCurta(iso) {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleDateString("pt-BR");
}

export function fmtMoeda(v) {
  return Number(v || 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

// Escapa qualquer string vinda da API antes de ir para innerHTML.
// Dados de paciente (nome, alergias...) são gravados sem sanitização
// no banco; sem isso, um nome como <img onerror=...> executaria ao
// renderizar a tabela (XSS armazenado).
export function esc(s) {
  if (s == null) return "";
  return String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

export function idChip(id) {
  if (!id) return "";
  return `<span class="id-chip">${String(id).slice(0, 8)}</span>`;
}

export function riscoBadge(nivel) {
  const classe = { BAIXO: "badge--baixo", MEDIO: "badge--medio", ALTO: "badge--alto" }[nivel] || "";
  return `<span class="badge ${classe}">${esc(nivel)}</span>`;
}

export function papelBadge(papel) {
  const classe = papel === "preceptor" ? "badge--preceptor" : "badge--residente";
  const rotulo = papel === "preceptor" ? "Preceptor" : "Residente";
  return `<span class="badge ${classe}">${rotulo}</span>`;
}

export function tabela(colunas, linhas, montarLinha) {
  if (!linhas || linhas.length === 0) {
    return `<div class="empty">Nenhum registro encontrado ainda.</div>`;
  }
  return `
    <table>
      <thead><tr>${colunas.map((c) => `<th>${c}</th>`).join("")}</tr></thead>
      <tbody>${linhas.map(montarLinha).join("")}</tbody>
    </table>
  `;
}
