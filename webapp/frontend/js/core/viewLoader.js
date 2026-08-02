import { carregarVisaoGeral } from "../views/visaoGeral.js";
import { carregarPacientes } from "../views/pacientes.js";
import { carregarProfissionais } from "../views/profissionais.js";
import { carregarAtendimentos } from "../views/atendimentos.js";
import { carregarEscalas } from "../views/escalas.js";
import { carregarIndicadores } from "../views/indicadores.js";

const CARREGADORES = {
  "visao-geral": carregarVisaoGeral,
  "pacientes": carregarPacientes,
  "profissionais": carregarProfissionais,
  "atendimentos": carregarAtendimentos,
  "escalas": carregarEscalas,
  "indicadores": carregarIndicadores,
};

export const jaCarregado = new Set();

export function carregarView(view) {
  if (jaCarregado.has(view) && view !== "visao-geral") return; // simples cache de sessão
  jaCarregado.add(view);
  (CARREGADORES[view] || (() => {}))();
}
