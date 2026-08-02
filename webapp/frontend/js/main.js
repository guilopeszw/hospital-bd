import { iniciarNav } from "./core/nav.js";
import { iniciarRelogio, iniciarChecagemSaude } from "./core/health.js";
import { carregarVisaoGeral } from "./views/visaoGeral.js";
import { iniciarBuscaPaciente } from "./views/pacientes.js";
import { iniciarModalPaciente } from "./modals/pacienteModal.js";
import { iniciarModalProfissional } from "./modals/profissionalModal.js";
import { iniciarModalAtendimento } from "./modals/atendimentoModal.js";
import { iniciarModalEscala } from "./modals/escalaModal.js";
import { iniciarFechamentoModais } from "./modals/closeModals.js";

iniciarNav();
iniciarBuscaPaciente();
iniciarModalPaciente();
iniciarModalProfissional();
iniciarModalAtendimento();
iniciarModalEscala();
iniciarFechamentoModais();

iniciarRelogio();
iniciarChecagemSaude();
carregarVisaoGeral();