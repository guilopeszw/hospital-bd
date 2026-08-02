import { apiGet } from "./api.js";

export function iniciarRelogio() {
  const atualizar = () => {
    document.getElementById("clock").textContent = new Date().toLocaleTimeString("pt-BR");
  };
  setInterval(atualizar, 1000);
  atualizar();
}

export async function checarSaude() {
  const dot = document.getElementById("db-status-dot");
  const texto = document.getElementById("db-status-text");
  try {
    await apiGet("/health");
    dot.className = "status-dot is-ok";
    texto.textContent = "banco conectado";
  } catch {
    dot.className = "status-dot is-error";
    texto.textContent = "API offline";
  }
}

export function iniciarChecagemSaude() {
  checarSaude();
  setInterval(checarSaude, 15000);
}
