
function definirCartao(chave, disponivel) {
    const card = document.getElementById("card-" + chave);
    if (!card) return;
    card.classList.toggle("has-data", disponivel);
    const botao = card.querySelector(".card-action");
    if (botao) {
        botao.disabled = !disponivel;
        if (!disponivel) botao.setAttribute("aria-expanded", "false");
    }
    const resumo = card.querySelector(".card-live");
    if (resumo) resumo.hidden = !disponivel;
    if (!disponivel) {
        const detalhe = document.getElementById("detail-" + chave);
        if (detalhe) detalhe.hidden = true;
    }
}
function iniciarControlesVisuais() {
    document.getElementById("collapse").addEventListener("click", function () {
        const recolhido = document.getElementById("shell").classList.toggle("collapsed");
        this.setAttribute("aria-expanded", String(!recolhido));
        this.textContent = recolhido ? "› Expandir menu" : "‹ Recolher menu";
        this.setAttribute("aria-label", recolhido ? "Expandir menu" : "Recolher menu");
    });
    const supervision = document.getElementById("supervision");
    const toggle = document.getElementById("supervisionToggle");
    toggle.addEventListener("click", function () {
        this.setAttribute("aria-expanded", String(supervision.classList.toggle("visible")));
    });
    document.getElementById("reconnect-top").addEventListener("click", () => botaoReconectar.click());
    document.querySelectorAll(".card-action").forEach(button => button.addEventListener("click", () => {
        if (button.disabled) return;
        const detail = document.getElementById("detail-" + button.dataset.details);
        detail.hidden = !detail.hidden;
        button.setAttribute("aria-expanded", String(!detail.hidden));
    }));
    document.getElementById("theme-toggle").addEventListener("click", function () {
        const dark = document.body.dataset.theme !== "dark";
        document.body.dataset.theme = dark ? "dark" : "light";
        this.setAttribute("aria-pressed", String(dark));
        this.setAttribute("aria-label", dark ? "Ativar tema claro" : "Ativar tema escuro");
    });
    const motion = document.getElementById("motion-toggle");
    motion.setAttribute("aria-pressed", String(window.matchMedia("(prefers-reduced-motion: reduce)").matches));
    motion.addEventListener("click", function () {
        const reduced = document.body.dataset.motion !== "reduced";
        document.body.dataset.motion = reduced ? "reduced" : "auto";
        this.setAttribute("aria-pressed", String(reduced || window.matchMedia("(prefers-reduced-motion: reduce)").matches));
    });
    const menu = document.getElementById("mobile-menu");
    const clone = document.getElementById("menu-content").cloneNode(true);
    clone.removeAttribute("id");
    document.getElementById("mobile-menu-content").appendChild(clone);
    document.getElementById("more-toggle").addEventListener("click", () => menu.showModal());
    document.getElementById("close-menu").addEventListener("click", () => menu.close());
    document.querySelectorAll("[data-navigate]").forEach(button => button.addEventListener("click", () => {
        const destination = button.dataset.navigate;
        if (menu.open) menu.close();
        if (destination === "supervisao" || destination === "diagnostico") {
            supervision.classList.add("visible");
            toggle.setAttribute("aria-expanded", "true");
            if (destination === "diagnostico" && !document.querySelector('#card-inteligencia .card-action').disabled) {
                document.getElementById("detail-inteligencia").hidden = false;
                document.querySelector('#card-inteligencia .card-action').setAttribute("aria-expanded", "true");
            }
            supervision.scrollIntoView({block: "start"});
        } else {
            const target = destination === "chat" ? document.getElementById("mensagem") : document.getElementById("home");
            target.scrollIntoView({block: "start"});
            if (destination === "chat") target.focus();
        }
    }));
}

const formulario = document.getElementById("formulario");
const campoMensagem = document.getElementById("mensagem");
const botaoEnviar = document.getElementById("enviar");
const conversa = document.getElementById("conversa");

const indicador = document.getElementById("indicador");
const textoEstado = document.getElementById("texto-estado");

let socket = null;
let aguardandoResposta = false;
let ultimoTextoEnviado = "";
let diagnosticoSeq = 0;
let estadoSeq = 0;
const botaoReconectar = document.getElementById("reconectar");
const estadoDiagnostico = document.getElementById("estado-diagnostico");
const verificacaoTexto = document.getElementById("diagnostico-verificacao");
const confiabilidadeTexto = document.getElementById("diagnostico-confiabilidade");

function atualizarResumo(id, texto) {
    const elemento = document.getElementById(id);
    if (elemento) elemento.textContent = texto;
}

function estadoAnalise(analise, politica) {
    if (politica?.estado === "modelo_nao_verificado") return "Não verificada";
    if (!analise || !analise.disponivel) return "Sem análise";
    return analise.bloquear_resposta === true ? "Bloqueada"
        : analise.bloquear_resposta === false ? "Liberada" : "Indeterminada";
}

function resumirAnalise(analise, politica) {
    if (politica?.estado === "modelo_nao_verificado") return `Critério rigoroso: ${estadoAnalise(analise)} · comunicação não verificada`;
    if (!analise || !analise.disponivel) return "Sem análise";
    const estado = analise.bloquear_resposta === true ? "Bloqueada"
        : analise.bloquear_resposta === false ? "Liberada" : "Indeterminado";
    return `${estado} · ${String(analise.nivel || "Nível não informado").replaceAll("_", " ")}`;
}

async function consultarDiagnostico() {
    const consulta = ++diagnosticoSeq;
    try {
        const resposta = await fetch("/api/diagnostico", {cache: "no-store"});
        if (!resposta.ok) throw new Error("Falha no diagnóstico");
        const dados = await resposta.json();
        if (consulta !== diagnosticoSeq) return;
        definirCartao("inteligencia", Boolean(dados.verificacao?.disponivel || dados.confiabilidade?.disponivel));
        verificacaoTexto.textContent = resumirAnalise(dados.verificacao, dados.politica_resposta);
        confiabilidadeTexto.textContent = resumirAnalise(dados.confiabilidade, dados.politica_resposta);
        atualizarResumo("resumo-verificacao", estadoAnalise(dados.verificacao, dados.politica_resposta));
        atualizarResumo("resumo-confiabilidade", estadoAnalise(dados.confiabilidade, dados.politica_resposta));
        estadoDiagnostico.textContent = dados.politica_resposta?.estado === "modelo_nao_verificado"
            ? "Conhecimento do modelo comunicado como não verificado; diagnósticos originais preservados"
            : dados.verificacao?.disponivel || dados.confiabilidade?.disponivel
            ? "Última análise disponível no núcleo" : "Nenhuma resposta analisada nesta execução";
    } catch {
        if (consulta !== diagnosticoSeq) return;
        definirCartao("inteligencia", false);
        estadoDiagnostico.textContent = "Diagnóstico indisponível; valores anteriores não confirmados";
        verificacaoTexto.textContent = "Indisponível";
        confiabilidadeTexto.textContent = "Indisponível";
        atualizarResumo("resumo-verificacao", "Indisponível");
        atualizarResumo("resumo-confiabilidade", "Indisponível");
    }
}


function atualizarConexao(online, texto) {
    indicador.classList.toggle("online", online);
    indicador.classList.toggle("offline", !online);

    textoEstado.textContent = texto;
    atualizarResumo("resumo-conexao", texto);
    if (!online) atualizarResumo("resumo-nucleo", "Não confirmado");
}

function adicionarMensagem(remetente, texto, tipo) {
    const mensagem = document.createElement("div");
    mensagem.className = `mensagem ${tipo}`;

    const nome = document.createElement("div");
    nome.className = "nome";
    nome.textContent = remetente;

    const conteudo = document.createElement("div");
    conteudo.className = "conteudo";
    conteudo.textContent = texto;

    mensagem.appendChild(nome);
    mensagem.appendChild(conteudo);

    const vazio = document.getElementById("chat-empty");
    if (vazio) vazio.hidden = true;
    if (tipo === "luci" && remetente === "Luci") {
        const simbolo = document.createElement("img");
        simbolo.src = "/static/img/luci-v25.png"; simbolo.alt = "";
        nome.prepend(simbolo);
    }
    conversa.appendChild(mensagem);
    const total = conversa.querySelectorAll(".mensagem:not(.saudacao)").length;
    atualizarResumo("resumo-mensagens", `${total} ${total === 1 ? "mensagem" : "mensagens"}`);
    conversa.scrollTop = conversa.scrollHeight;
}

async function consultarEstado() {
    const consulta = ++estadoSeq;
    try {
        const resposta = await fetch("/api/estado", {cache: "no-store"});

        if (!resposta.ok) {
            throw new Error("Falha ao consultar o núcleo.");
        }

        const estado = await resposta.json();
        if (consulta !== estadoSeq) return;
        definirCartao("sistema", typeof estado.ativo === "boolean");
        atualizarResumo("versao-nucleo", String(estado.versao || "Não informada"));
        atualizarResumo("resumo-nucleo", estado.ativo ? "Ativo" : "Inativo");

        if (socket && socket.readyState === WebSocket.OPEN && estado.ativo) {
            atualizarConexao(true, "Chat conectado · núcleo ativo");
        } else {
            atualizarConexao(false, estado.ativo ? "API disponível · chat desconectado" : "Núcleo indisponível");
        }

    } catch (erro) {
        if (consulta !== estadoSeq) return;
        definirCartao("sistema", false);
        atualizarConexao(false, "Servidor indisponível");
    }
}

function conectar() {
    if (socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) return;
    atualizarConexao(false, "Conectando...");
    const protocolo = window.location.protocol === "https:"
        ? "wss:"
        : "ws:";

    socket = new WebSocket(
        `${protocolo}//${window.location.host}/ws`
    );

    const canalAtual = socket;
    socket.addEventListener("open", () => {
        if (canalAtual !== socket) return;
        consultarEstado();
        consultarDiagnostico();
    });

    socket.addEventListener("message", (evento) => {
        if (canalAtual !== socket) return;
        let dados;

        try {
            dados = JSON.parse(evento.data);
        } catch {
            adicionarMensagem(
                "Sistema",
                "Recebi uma resposta em formato inválido.",
                "luci"
            );
            finalizarEnvio();
            return;
        }

        if (dados.tipo === "resposta" && typeof dados.mensagem === "string") {
            ultimoTextoEnviado = "";
            document.getElementById("aviso-envio").textContent = "";
            adicionarMensagem(
                "Luci",
                String(dados.mensagem),
                "luci"
            );

            consultarEstado();
        } else if (dados.tipo === "erro") {
            adicionarMensagem(
                "Sistema",
                String(dados.mensagem),
                "luci"
            );
        }

        finalizarEnvio();
        consultarDiagnostico();
    });

    socket.addEventListener("close", () => {
        if (canalAtual !== socket) return;
        ++estadoSeq; ++diagnosticoSeq;
        definirCartao("sistema", false); definirCartao("inteligencia", false);
        if (aguardandoResposta && ultimoTextoEnviado) {
            if (!campoMensagem.value) campoMensagem.value = ultimoTextoEnviado;
            document.getElementById("aviso-envio").textContent = "A conexão caiu antes da confirmação. A mensagem pode ter sido processada; ela não foi reenviada automaticamente.";
        }
        atualizarConexao(false, "Desconectado");
        estadoDiagnostico.textContent = "Conexão perdida; use Reconectar";
        verificacaoTexto.textContent = "Indisponível";
        confiabilidadeTexto.textContent = "Indisponível";
        atualizarResumo("resumo-verificacao", "Indisponível");
        atualizarResumo("resumo-confiabilidade", "Indisponível");
        finalizarEnvio();
    });

    socket.addEventListener("error", () => {
        if (canalAtual !== socket) return;
        atualizarConexao(false, "Erro de conexão");
    });
}

function finalizarEnvio() {
    aguardandoResposta = false;
    botaoEnviar.disabled = false;
    campoMensagem.disabled = false;
    botaoEnviar.textContent = "Enviar";
}

formulario.addEventListener("submit", (evento) => {
    evento.preventDefault();

    const texto = campoMensagem.value.trim();

    if (!texto || aguardandoResposta) {
        return;
    }

    if (!socket || socket.readyState !== WebSocket.OPEN) {
        adicionarMensagem(
            "Sistema",
            "Não foi possível conectar ao servidor.",
            "luci"
        );
        return;
    }

    if (texto.length > 10000) {
        adicionarMensagem(
            "Sistema",
            "A mensagem ultrapassa o limite permitido.",
            "luci"
        );
        return;
    }

    ultimoTextoEnviado = texto;
    adicionarMensagem("Você", texto, "usuario");

    aguardandoResposta = true;
    botaoEnviar.disabled = true;
    campoMensagem.disabled = true;
    botaoEnviar.textContent = "Enviando...";

    try {
        socket.send(JSON.stringify({mensagem: texto}));
    } catch {
        adicionarMensagem("Sistema", "Falha no envio. Seu texto foi preservado para nova tentativa.", "luci");
        finalizarEnvio();
        return;
    }

    campoMensagem.value = "";
});

campoMensagem.addEventListener("keydown", (evento) => {
    if (evento.key === "Enter" && !evento.shiftKey) {
        evento.preventDefault();
        formulario.requestSubmit();
    }
});

botaoReconectar.addEventListener("click", () => {
    conectar();
    consultarDiagnostico();
});
iniciarControlesVisuais();
consultarEstado();
consultarDiagnostico();
conectar();

for (const item of document.querySelectorAll(".nav-item")) {
    item.addEventListener("click", () => {
        document.querySelectorAll(".nav-item").forEach(link => {
            link.classList.remove("ativo");
            link.removeAttribute("aria-current");
        });
        item.classList.add("ativo");
        item.setAttribute("aria-current", "location");
    });
}
