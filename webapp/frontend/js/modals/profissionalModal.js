import { apiPost } from "../core/api.js";
import { showToast } from "../core/toast.js";
import { jaCarregado } from "../core/viewLoader.js";
import { carregarProfissionais } from "../views/profissionais.js";

export function iniciarModalProfissional() {
  const modal = document.getElementById("modal-profissional");
  const selectTipo = document.getElementById("select-profissional-tipo");
  const campoAnoResidencia = document.getElementById("campo-ano-residencia");
  const campoTitulacao = document.getElementById("campo-titulacao");

  function alternarCamposPorTipo() {
    const ehResidente = selectTipo.value === "residente";
    campoAnoResidencia.style.display = ehResidente ? "" : "none";
    campoTitulacao.style.display = ehResidente ? "none" : "";
  }

  selectTipo.addEventListener("change", alternarCamposPorTipo);

  document.getElementById("btn-novo-profissional").addEventListener("click", () => {
    alternarCamposPorTipo();
    modal.classList.add("is-open");
  });

  document.getElementById("form-profissional").addEventListener("submit", async (e) => {
    e.preventDefault();
    const erro = document.getElementById("erro-profissional");
    erro.textContent = "";
    const fd = new FormData(e.target);
    const payload = Object.fromEntries(fd.entries());
    // só manda o campo relevante ao papel escolhido, evitando enviar
    // um titulacao/ano_residencia vazio ou irrelevante para a API
    if (payload.tipo === "residente") {
      delete payload.titulacao;
    } else {
      delete payload.ano_residencia;
    }
    try {
      await apiPost("/profissionais", payload);
      modal.classList.remove("is-open");
      e.target.reset();
      alternarCamposPorTipo();
      showToast("Profissional cadastrado com sucesso.");
      jaCarregado.delete("profissionais");
      carregarProfissionais();
    } catch (err) {
      erro.textContent = err.message;
    }
  });
}