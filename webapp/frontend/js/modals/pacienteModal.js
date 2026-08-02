import { apiPost } from "../core/api.js";
import { showToast } from "../core/toast.js";
import { jaCarregado } from "../core/viewLoader.js";
import { carregarPacientes } from "../views/pacientes.js";

export function iniciarModalPaciente() {
  const modal = document.getElementById("modal-paciente");
  document.getElementById("btn-novo-paciente").addEventListener("click", () => modal.classList.add("is-open"));

  document.getElementById("form-paciente").addEventListener("submit", async (e) => {
    e.preventDefault();
    const erro = document.getElementById("erro-paciente");
    erro.textContent = "";
    const fd = new FormData(e.target);
    const payload = Object.fromEntries(fd.entries());
    try {
      await apiPost("/pacientes", payload);
      modal.classList.remove("is-open");
      e.target.reset();
      showToast("Prontuário criado com sucesso.");
      jaCarregado.delete("pacientes");
      carregarPacientes();
    } catch (err) {
      erro.textContent = err.message;
    }
  });
}
