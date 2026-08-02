import { apiGet, apiPost } from "../core/api.js";
import { esc } from "../core/format.js";
import { showToast } from "../core/toast.js";
import { jaCarregado } from "../core/viewLoader.js";
import { carregarEscalas } from "../views/escalas.js";

export function iniciarModalEscala() {
  const modal = document.getElementById("modal-escala");

  document.getElementById("btn-nova-escala").addEventListener("click", async () => {
    modal.classList.add("is-open");
    const selU = document.getElementById("select-escala-unidade");
    const selR = document.getElementById("select-escala-residente");
    const selPre = document.getElementById("select-escala-preceptor");
    selU.innerHTML = selR.innerHTML = selPre.innerHTML = `<option>Carregando…</option>`;

    try {
      const [unidades, profissionais] = await Promise.all([apiGet("/unidades"), apiGet("/profissionais")]);
      const residentes = profissionais.filter((p) => p.papel_atual === "residente");
      const preceptores = profissionais.filter((p) => p.papel_atual === "preceptor");

      selU.innerHTML = unidades.map((u) => `<option value="${esc(u.id_unidade)}">${esc(u.nome)}</option>`).join("");
      selR.innerHTML = residentes.map((p) => `<option value="${esc(p.id_pessoa)}">${esc(p.nome)} (${esc(p.ano_residencia)})</option>`).join("");
      selPre.innerHTML = preceptores.map((p) => `<option value="${esc(p.id_pessoa)}">${esc(p.nome)}</option>`).join("");
    } catch {
      document.getElementById("erro-escala").textContent = "Não foi possível carregar unidades/equipe.";
    }
  });

  document.getElementById("form-escala").addEventListener("submit", async (e) => {
    e.preventDefault();
    const erro = document.getElementById("erro-escala");
    erro.textContent = "";
    const fd = new FormData(e.target);
    const payload = Object.fromEntries(fd.entries());
    try {
      await apiPost("/escalas", payload);
      modal.classList.remove("is-open");
      e.target.reset();
      showToast("Escala criada com sucesso.");
      jaCarregado.delete("escalas");
      carregarEscalas();
    } catch (err) {
      // Conflito vem do trigger trg_check_sobreposicao_escala (ou da UNIQUE) —
      // mostra a mensagem de negócio direto do banco, sem reformular.
      erro.textContent = err.message;
    }
  });
}
