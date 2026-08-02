import { apiGet } from "../core/api.js";
import { esc, idChip, tabela } from "../core/format.js";

export async function carregarPacientes(busca = "") {
  const alvo = document.getElementById("tabela-pacientes");
  try {
    const pacientes = await apiGet(`/pacientes${busca ? `?busca=${encodeURIComponent(busca)}` : ""}`);
    alvo.innerHTML = tabela(
      ["Nome", "CPF", "Convênio", "Tipo sanguíneo", "Alergias", "ID"],
      pacientes,
      (p) => `<tr>
        <td>${esc(p.nome)}</td>
        <td>${esc(p.cpf)}</td>
        <td>${esc(p.num_convenio || "—")}</td>
        <td>${esc(p.grupo_sanguineo || "—")}</td>
        <td>${esc(p.alergias || "—")}</td>
        <td>${idChip(p.id_pessoa)}</td>
      </tr>`
    );
  } catch {
    alvo.innerHTML = `<div class="empty">Não foi possível carregar os pacientes.</div>`;
  }
}

export function iniciarBuscaPaciente() {
  let debounceBusca;
  document.getElementById("busca-paciente").addEventListener("input", (e) => {
    clearTimeout(debounceBusca);
    debounceBusca = setTimeout(() => carregarPacientes(e.target.value.trim()), 300);
  });
}
