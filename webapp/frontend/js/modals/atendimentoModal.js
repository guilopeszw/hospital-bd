import { apiGet, apiPost } from "../core/api.js";
import { esc } from "../core/format.js";
import { showToast } from "../core/toast.js";
import { jaCarregado } from "../core/viewLoader.js";
import { carregarAtendimentos } from "../views/atendimentos.js";

export function iniciarModalAtendimento() {
  const modal = document.getElementById("modal-atendimento");

  document.getElementById("btn-novo-atendimento").addEventListener("click", async () => {
    modal.classList.add("is-open");
    const selP = document.getElementById("select-paciente");
    const selR = document.getElementById("select-residente");
    const selPre = document.getElementById("select-preceptor");
    const selU = document.getElementById("select-unidade");
    selP.innerHTML = selR.innerHTML = selPre.innerHTML = selU.innerHTML = `<option>Carregando…</option>`;

    try {
      const [pacientes, profissionais, unidades] = await Promise.all([
        apiGet("/pacientes"), apiGet("/profissionais"), apiGet("/unidades"),
      ]);
      const residentes = profissionais.filter((p) => p.papel_atual === "residente");
      const preceptores = profissionais.filter((p) => p.papel_atual === "preceptor");

      selP.innerHTML = pacientes.map((p) => `<option value="${esc(p.id_pessoa)}">${esc(p.nome)}</option>`).join("");
      selR.innerHTML = residentes.map((p) => `<option value="${esc(p.id_pessoa)}">${esc(p.nome)} (${esc(p.ano_residencia)})</option>`).join("");
      selPre.innerHTML = preceptores.map((p) => `<option value="${esc(p.id_pessoa)}">${esc(p.nome)}</option>`).join("");
      selU.innerHTML = unidades.map((u) => `<option value="${esc(u.id_unidade)}">${esc(u.nome)}</option>`).join("");
    } catch {
      document.getElementById("erro-atendimento").textContent = "Não foi possível carregar pacientes/equipe/unidades.";
    }
  });

  document.getElementById("form-atendimento").addEventListener("submit", async (e) => {
    e.preventDefault();
    const erro = document.getElementById("erro-atendimento");
    erro.textContent = "";
    const fd = new FormData(e.target);
    const payload = Object.fromEntries(fd.entries());
    try {
      await apiPost("/atendimentos", payload);
      modal.classList.remove("is-open");
      e.target.reset();
      showToast("Atendimento registrado com sucesso.");
      jaCarregado.delete("atendimentos");
      carregarAtendimentos();
    } catch (err) {
      erro.textContent = err.message;
    }
  });
}
