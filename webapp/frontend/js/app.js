const API_BASE = "http://localhost:5000/api";


// helpers

async function apiGet(path) {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) throw new Error(`Falha ao buscar ${path}`);
  return res.json();
}

async function apiPost(path, body) {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.erro || "Erro inesperado ao salvar.");
  return data;
}

function fmtData(iso) {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleString("pt-BR", { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" });
}

function fmtDataCurta(iso) {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleDateString("pt-BR");
}

function fmtMoeda(v) {
  return Number(v || 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

function idChip(id) {
  if (!id) return "";
  return `<span class="id-chip">${String(id).slice(0, 8)}</span>`;
}

function riscoBadge(nivel) {
  const classe = { BAIXO: "badge--baixo", MEDIO: "badge--medio", ALTO: "badge--alto" }[nivel] || "";
  return `<span class="badge ${classe}">${nivel}</span>`;
}

function papelBadge(papel) {
  const classe = papel === "preceptor" ? "badge--preceptor" : "badge--residente";
  const rotulo = papel === "preceptor" ? "Preceptor" : "Residente";
  return `<span class="badge ${classe}">${rotulo}</span>`;
}

function tabela(colunas, linhas, montarLinha) {
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

function showToast(msg, isError = false) {
  const toast = document.getElementById("toast");
  toast.textContent = msg;
  toast.classList.toggle("is-error", isError);
  toast.classList.add("is-visible");
  clearTimeout(showToast._t);
  showToast._t = setTimeout(() => toast.classList.remove("is-visible"), 3200);
}

// navegação entre seções

const TITULOS = {
  "visao-geral": ["Painel", "Visão geral"],
  "pacientes": ["Prontuários", "Pacientes"],
  "profissionais": ["Equipe", "Residentes e preceptores"],
  "atendimentos": ["Registros", "Atendimentos"],
  "escalas": ["Plantões", "Escala semanal"],
  "indicadores": ["Analytics", "Indicadores"],
};

function irPara(view) {
  document.querySelectorAll(".nav__item").forEach((b) => b.classList.toggle("is-active", b.dataset.view === view));
  document.querySelectorAll(".view").forEach((s) => s.classList.toggle("is-active", s.id === `view-${view}`));
  const [eyebrow, titulo] = TITULOS[view] || ["Painel", view];
  document.getElementById("view-eyebrow").textContent = eyebrow;
  document.getElementById("view-title").textContent = titulo;
  carregarView(view);
}

document.getElementById("nav").addEventListener("click", (e) => {
  const btn = e.target.closest("[data-view]");
  if (btn) irPara(btn.dataset.view);
});
document.querySelectorAll(".link-btn[data-view]").forEach((b) => b.addEventListener("click", () => irPara(b.dataset.view)));

const jaCarregado = new Set();
function carregarView(view) {
  if (jaCarregado.has(view) && view !== "visao-geral") return; // simples cache de sessão
  jaCarregado.add(view);
  const map = {
    "visao-geral": carregarVisaoGeral,
    "pacientes": carregarPacientes,
    "profissionais": carregarProfissionais,
    "atendimentos": carregarAtendimentos,
    "escalas": carregarEscalas,
    "indicadores": carregarIndicadores,
  };
  (map[view] || (() => {}))();
}


// relógio + status da API

function atualizarRelogio() {
  document.getElementById("clock").textContent = new Date().toLocaleTimeString("pt-BR");
}
setInterval(atualizarRelogio, 1000);
atualizarRelogio();

async function checarSaude() {
  const dot = document.getElementById("db-status-dot");
  const texto = document.getElementById("db-status-text");
  try {
    const r = await apiGet("/health");
    dot.className = "status-dot is-ok";
    texto.textContent = "banco conectado";
  } catch {
    dot.className = "status-dot is-error";
    texto.textContent = "API offline";
  }
}


// visão geral


async function carregarVisaoGeral() {
  try {
    const s = await apiGet("/dashboard/summary");
    document.getElementById("stat-grid").innerHTML = `
      <div class="stat-card">
        <p class="stat-card__label">Pacientes cadastrados</p>
        <p class="stat-card__value">${s.total_pacientes}</p>
      </div>
      <div class="stat-card">
        <p class="stat-card__label">Atendimentos no mês</p>
        <p class="stat-card__value">${s.atendimentos_mes}</p>
      </div>
      <div class="stat-card stat-card--amber">
        <p class="stat-card__label">Plantões hoje</p>
        <p class="stat-card__value">${s.plantoes_hoje}</p>
      </div>
      <div class="stat-card stat-card--coral">
        <p class="stat-card__label">Faturamento do mês</p>
        <p class="stat-card__value">${fmtMoeda(s.faturamento_mes)}</p>
      </div>
    `;
  } catch {
    document.getElementById("stat-grid").innerHTML = `<div class="empty" style="grid-column:1/-1">Não foi possível carregar o resumo. Confira se a API (python app.py) está rodando em localhost:5000.</div>`;
  }

  try {
    const at = await apiGet("/atendimentos?limite=6");
    document.getElementById("preview-atendimentos").innerHTML = tabela(
      ["Data", "Paciente", "Residente", "Preceptor"],
      at,
      (a) => `<tr>
        <td>${fmtData(a.data_hora)}</td>
        <td>${a.paciente}</td>
        <td>${a.residente}</td>
        <td>${a.preceptor}</td>
      </tr>`
    );
  } catch {
    document.getElementById("preview-atendimentos").innerHTML = `<div class="empty">Sem dados disponíveis.</div>`;
  }
}


// pacientes


async function carregarPacientes(busca = "") {
  const alvo = document.getElementById("tabela-pacientes");
  try {
    const pacientes = await apiGet(`/pacientes${busca ? `?busca=${encodeURIComponent(busca)}` : ""}`);
    alvo.innerHTML = tabela(
      ["Nome", "CPF", "Convênio", "Tipo sanguíneo", "Alergias", "ID"],
      pacientes,
      (p) => `<tr>
        <td>${p.nome}</td>
        <td>${p.cpf}</td>
        <td>${p.num_convenio || "—"}</td>
        <td>${p.grupo_sanguineo || "—"}</td>
        <td>${p.alergias || "—"}</td>
        <td>${idChip(p.id_pessoa)}</td>
      </tr>`
    );
  } catch {
    alvo.innerHTML = `<div class="empty">Não foi possível carregar os pacientes.</div>`;
  }
}

let debounceBusca;
document.getElementById("busca-paciente").addEventListener("input", (e) => {
  clearTimeout(debounceBusca);
  debounceBusca = setTimeout(() => carregarPacientes(e.target.value.trim()), 300);
});


// profissionais

async function carregarProfissionais() {
  const alvo = document.getElementById("tabela-profissionais");
  try {
    const prof = await apiGet("/profissionais");
    alvo.innerHTML = tabela(
      ["Nome", "Papel", "CRM", "Especialidade", "Detalhe"],
      prof,
      (p) => `<tr>
        <td>${p.nome}</td>
        <td>${papelBadge(p.papel_atual)}</td>
        <td>${p.crm}</td>
        <td>${p.especialidade}</td>
        <td>${p.papel_atual === "preceptor" ? (p.titulacao || "—") : (p.ano_residencia || "—")}</td>
      </tr>`
    );
  } catch {
    alvo.innerHTML = `<div class="empty">Não foi possível carregar a equipe.</div>`;
  }
}


// atendimentos


async function carregarAtendimentos() {
  const alvo = document.getElementById("tabela-atendimentos");
  try {
    const at = await apiGet("/atendimentos?limite=200");
    alvo.innerHTML = tabela(
      ["Data", "Paciente", "Residente", "Preceptor", "Duração", "ID"],
      at,
      (a) => `<tr>
        <td>${fmtData(a.data_hora)}</td>
        <td>${a.paciente}</td>
        <td>${a.residente}</td>
        <td>${a.preceptor}</td>
        <td>${a.duracao_minutos} min</td>
        <td>${idChip(a.id_atendimento)}</td>
      </tr>`
    );
  } catch {
    alvo.innerHTML = `<div class="empty">Não foi possível carregar os atendimentos.</div>`;
  }
}


// escalas


const DIA_LEGIVEL = { segunda: "Segunda", terca: "Terça", quarta: "Quarta", quinta: "Quinta", sexta: "Sexta", sabado: "Sábado", domingo: "Domingo" };
const TURNO_LEGIVEL = { manha: "Manhã", tarde: "Tarde", noite: "Noite" };

async function carregarEscalas() {
  const alvo = document.getElementById("tabela-escalas");
  try {
    const esc = await apiGet("/escalas");
    alvo.innerHTML = tabela(
      ["Unidade", "Dia", "Turno", "Residente", "Preceptor"],
      esc,
      (e) => `<tr>
        <td>${e.unidade}</td>
        <td>${DIA_LEGIVEL[e.dia_semana] || e.dia_semana}</td>
        <td>${TURNO_LEGIVEL[e.turno] || e.turno}</td>
        <td>${e.residente}</td>
        <td>${e.preceptor}</td>
      </tr>`
    );
  } catch {
    alvo.innerHTML = `<div class="empty">Não foi possível carregar as escalas.</div>`;
  }
}


// indicadores

async function carregarIndicadores() {
  apiGet("/analytics/ranking-residentes")
    .then((rows) => {
      document.getElementById("ranking-residentes").innerHTML = tabela(
        ["Residente", "Ano", "Atendimentos"],
        rows,
        (r) => `<tr><td>${r.residente}</td><td>${r.ano_residencia}</td><td><strong>${r.total_atendimentos}</strong></td></tr>`
      );
    })
    .catch(() => { document.getElementById("ranking-residentes").innerHTML = `<div class="empty">Sem dados.</div>`; });

  apiGet("/analytics/tempo-medio-residente")
    .then((rows) => {
      document.getElementById("tempo-medio").innerHTML = tabela(
        ["Residente", "Especialidade", "Tempo médio"],
        rows,
        (r) => `<tr><td>${r.residente}</td><td>${r.especialidade}</td><td>${r.tempo_medio_minutos != null ? r.tempo_medio_minutos + " min" : "—"}</td></tr>`
      );
    })
    .catch(() => { document.getElementById("tempo-medio").innerHTML = `<div class="empty">Sem dados.</div>`; });

  apiGet("/analytics/plantoes-mes")
    .then((rows) => {
      document.getElementById("plantoes-mes").innerHTML = tabela(
        ["Unidade", "Residente", "Plantões"],
        rows,
        (r) => `<tr><td>${r.unidade}</td><td>${r.residente}</td><td><strong>${r.total_plantoes_no_mes}</strong></td></tr>`
      );
    })
    .catch(() => { document.getElementById("plantoes-mes").innerHTML = `<div class="empty">Sem dados.</div>`; });

  apiGet("/analytics/pacientes-sem-risco-alto")
    .then((rows) => {
      document.getElementById("sem-risco-alto").innerHTML = tabela(
        ["Paciente", "Convênio"],
        rows,
        (r) => `<tr><td>${r.paciente}</td><td>${r.num_convenio || "—"}</td></tr>`
      );
    })
    .catch(() => { document.getElementById("sem-risco-alto").innerHTML = `<div class="empty">Sem dados.</div>`; });
}

// modal: novo paciente


const modalPaciente = document.getElementById("modal-paciente");
document.getElementById("btn-novo-paciente").addEventListener("click", () => modalPaciente.classList.add("is-open"));

document.getElementById("form-paciente").addEventListener("submit", async (e) => {
  e.preventDefault();
  const erro = document.getElementById("erro-paciente");
  erro.textContent = "";
  const fd = new FormData(e.target);
  const payload = Object.fromEntries(fd.entries());
  try {
    await apiPost("/pacientes", payload);
    modalPaciente.classList.remove("is-open");
    e.target.reset();
    showToast("Prontuário criado com sucesso.");
    jaCarregado.delete("pacientes");
    carregarPacientes();
  } catch (err) {
    erro.textContent = err.message;
  }
});


// modal: novo atendimento

const modalAtendimento = document.getElementById("modal-atendimento");

document.getElementById("btn-novo-atendimento").addEventListener("click", async () => {
  modalAtendimento.classList.add("is-open");
  const selP = document.getElementById("select-paciente");
  const selR = document.getElementById("select-residente");
  const selPre = document.getElementById("select-preceptor");
  selP.innerHTML = selR.innerHTML = selPre.innerHTML = `<option>Carregando…</option>`;

  try {
    const [pacientes, profissionais] = await Promise.all([apiGet("/pacientes"), apiGet("/profissionais")]);
    const residentes = profissionais.filter((p) => p.papel_atual === "residente");
    const preceptores = profissionais.filter((p) => p.papel_atual === "preceptor");

    selP.innerHTML = pacientes.map((p) => `<option value="${p.id_pessoa}">${p.nome}</option>`).join("");
    selR.innerHTML = residentes.map((p) => `<option value="${p.id_pessoa}">${p.nome} (${p.ano_residencia})</option>`).join("");
    selPre.innerHTML = preceptores.map((p) => `<option value="${p.id_pessoa}">${p.nome}</option>`).join("");
  } catch {
    document.getElementById("erro-atendimento").textContent = "Não foi possível carregar pacientes/equipe.";
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
    modalAtendimento.classList.remove("is-open");
    e.target.reset();
    showToast("Atendimento registrado com sucesso.");
    jaCarregado.delete("atendimentos");
    carregarAtendimentos();
  } catch (err) {
    erro.textContent = err.message;
  }
});


// fechar modais


document.querySelectorAll("[data-close-modal]").forEach((btn) => {
  btn.addEventListener("click", () => btn.closest(".modal").classList.remove("is-open"));
});
document.querySelectorAll(".modal").forEach((m) => {
  m.addEventListener("click", (e) => { if (e.target === m) m.classList.remove("is-open"); });
});


// boot


checarSaude();
setInterval(checarSaude, 15000);
carregarVisaoGeral();
