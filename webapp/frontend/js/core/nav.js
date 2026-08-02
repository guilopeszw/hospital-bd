import { TITULOS } from "./constants.js";
import { carregarView } from "./viewLoader.js";

function irPara(view) {
  document.querySelectorAll(".nav__item").forEach((b) => b.classList.toggle("is-active", b.dataset.view === view));
  document.querySelectorAll(".view").forEach((s) => s.classList.toggle("is-active", s.id === `view-${view}`));
  const [eyebrow, titulo] = TITULOS[view] || ["Painel", view];
  document.getElementById("view-eyebrow").textContent = eyebrow;
  document.getElementById("view-title").textContent = titulo;
  carregarView(view);
}

export function iniciarNav() {
  document.getElementById("nav").addEventListener("click", (e) => {
    const btn = e.target.closest("[data-view]");
    if (btn) irPara(btn.dataset.view);
  });
  document.querySelectorAll(".link-btn[data-view]").forEach((b) => b.addEventListener("click", () => irPara(b.dataset.view)));
}
