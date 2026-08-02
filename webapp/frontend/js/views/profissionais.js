import { apiGet } from "../core/api.js";
import { esc, papelBadge, tabela } from "../core/format.js";

export async function carregarProfissionais() {
  const alvo = document.getElementById("tabela-profissionais");
  try {
    const prof = await apiGet("/profissionais");
    alvo.innerHTML = tabela(
      ["Nome", "Papel", "CRM", "Especialidade", "Detalhe"],
      prof,
      (p) => `<tr>
        <td>${esc(p.nome)}</td>
        <td>${papelBadge(p.papel_atual)}</td>
        <td>${esc(p.crm)}</td>
        <td>${esc(p.especialidade)}</td>
        <td>${esc(p.papel_atual === "preceptor" ? (p.titulacao || "—") : (p.ano_residencia || "—"))}</td>
      </tr>`
    );
  } catch {
    alvo.innerHTML = `<div class="empty">Não foi possível carregar a equipe.</div>`;
  }
}
