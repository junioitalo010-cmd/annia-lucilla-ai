 
from .memoria_longa import (
    recuperar_informacao,
    recuperar_todas_informacoes,
    guardar_informacao
)

import unicodedata
import re


# ==================================================
# 1. ESTADO DO DIÁLOGO
# ==================================================

historico = []

informacoes = {
    "nome_usuario": None,
    "assunto_atual": None,
    "nivel_conhecimento": None,
    "preferencia_aprendizado": None
}

estado_dialogo = {
    "assunto_atual": None,
    "aguardando_resposta": None,
    "ultima_pergunta": None
}


# ==================================================
# 2. NORMALIZAÇÃO DE TEXTO
# ==================================================

def normalizar(texto):
    texto = str(texto).lower().strip()
    texto = unicodedata.normalize("NFD", texto)

    texto = "".join(
        caractere
        for caractere in texto
        if unicodedata.category(caractere) != "Mn"
    )

    return " ".join(texto.split())


def contem_expressao(texto, expressao):
    texto = normalizar(texto)
    expressao = normalizar(expressao)

    return re.search(
        r"(?<!\w)" + re.escape(expressao) + r"(?!\w)",
        texto
    ) is not None


# ==================================================
# 3. REGISTRO DO HISTÓRICO
# ==================================================

def registrar_mensagem(remetente, mensagem):
    historico.append({
        "remetente": remetente,
        "mensagem": mensagem
    })

    if len(historico) > 200:
        del historico[:-200]


# ==================================================
# 4. IDENTIFICAÇÃO DE INTENÇÕES
# ==================================================

def identificar_intencao(texto):
    texto = normalizar(texto)

    if any(contem_expressao(texto, palavra) for palavra in [
        "ola",
        "oi",
        "bom dia",
        "boa tarde",
        "boa noite"
    ]):
        return "cumprimento"

    elif any(contem_expressao(texto, palavra) for palavra in [
        "tudo bem",
        "como voce esta",
        "como vai voce"
    ]):
        return "pergunta_bem_estar"

    elif any(contem_expressao(texto, palavra) for palavra in [
        "obrigado",
        "obrigada",
        "agradeco",
        "valeu"
    ]):
        return "agradecimento"

    elif any(contem_expressao(texto, palavra) for palavra in [
        "tchau",
        "ate mais",
        "ate logo"
    ]):
        return "despedida"

    elif any(expressao in texto for expressao in [
        "quero aprender",
        "quero estudar",
        "me ensine",
        "como aprender",
        "quero entender"
    ]):
        return "interesse_aprendizado"

    elif any(expressao in texto for expressao in [
        "estou feliz",
        "estou triste",
        "estou cansado",
        "estou animado",
        "estou preocupado"
    ]):
        return "expressao_pessoal"

    return "desconhecida"


def responder_intencao(texto):
    intencao = identificar_intencao(texto)

    if intencao == "cumprimento":
        return "Olá! Que bom conversar com você novamente!"

    elif intencao == "pergunta_bem_estar":
        return "Estou funcionando! E você, como está?"

    elif intencao == "agradecimento":
        return "Por nada! Fico feliz em poder ajudar."

    elif intencao == "despedida":
        return "Até logo! Estarei aqui quando precisar."

    elif intencao == "interesse_aprendizado":
        estado_dialogo["aguardando_resposta"] = "assunto_aprendizado"
        return "Que interessante! O que você gostaria de aprender?"

    elif intencao == "expressao_pessoal":
        return "Entendi! Quer conversar um pouco sobre como está se sentindo?"

    return None


# ==================================================
# 5. IDENTIFICAÇÃO DE INFORMAÇÕES
# ==================================================

def identificar_informacao(texto):
    texto_original = texto.strip()
    texto = normalizar(texto_original)

    regras = [
        ("meu nome e ", "nome_usuario"),
        ("me chamo ", "nome_usuario"),
        ("estou estudando ", "linguagem"),
        ("meu curso e ", "curso"),
        ("meu objetivo e ", "objetivo"),
        ("minha preferencia e ", "preferencia_aprendizado")
    ]

    for expressao, chave in regras:
        if expressao in texto:
            posicao = texto.find(expressao)
            valor = texto_original[posicao + len(expressao):].strip()

            for sufixo in (" atualmente", " hoje"):
                if normalizar(valor).endswith(sufixo):
                    valor = valor[:-len(sufixo)].strip()

            if valor:
                return chave, valor

    return None


# ==================================================
# 6. ATUALIZAÇÃO DO CONTEXTO
# ==================================================

def atualizar_contexto(texto):
    resultado = identificar_informacao(texto)

    if not resultado:
        return None

    chave, valor = resultado

    informacoes[chave] = valor
    guardar_informacao(chave, valor)

    if chave in ("curso", "linguagem", "objetivo"):
        estado_dialogo["assunto_atual"] = valor
        informacoes["assunto_atual"] = valor
        guardar_informacao("assunto_atual", valor)

    return (
        f"Entendi! Registrei essa informação: "
        f"{chave.replace('_', ' ')} = {valor}."
    )


# ==================================================
# 7. CONTINUIDADE DA CONVERSA
# ==================================================

def processar_continuidade(texto):
    aguardando = estado_dialogo.get("aguardando_resposta")

    if not aguardando:
        return None

    valor = texto.strip()

    if not valor:
        return None

    if aguardando == "assunto_aprendizado":
        informacoes["assunto_atual"] = valor
        estado_dialogo["assunto_atual"] = valor

        guardar_informacao("assunto_atual", valor)

        estado_dialogo["aguardando_resposta"] = None

        return (
            f"Ótimo! Vamos trabalhar com {valor}. "
            "Como você prefere começar?"
        )

    if aguardando == "nivel_conhecimento":
        informacoes["nivel_conhecimento"] = valor
        guardar_informacao("nivel_conhecimento", valor)

        estado_dialogo["aguardando_resposta"] = None

        return f"Entendi! Vou considerar seu nível como: {valor}."

    if aguardando == "preferencia_aprendizado":
        informacoes["preferencia_aprendizado"] = valor
        guardar_informacao("preferencia_aprendizado", valor)

        estado_dialogo["aguardando_resposta"] = None

        return f"Entendi! Vou considerar essa preferência: {valor}."

    return None


# ==================================================
# 8. CONSULTA À MEMÓRIA DO USUÁRIO
# ==================================================

def responder_contexto(texto):
    pergunta = normalizar(texto)

    substituicoes = {
        "qeu": "que",
        "voçe": "voce",
        "min": "mim"
    }

    palavras = pergunta.split()
    pergunta = " ".join(
        substituicoes.get(palavra, palavra)
        for palavra in palavras
    )

    dados = recuperar_todas_informacoes()

    if not isinstance(dados, dict):
        dados = {}

    dados.update({
        chave: valor
        for chave, valor in informacoes.items()
        if valor is not None
    })

    perguntas_estudos = [
        "o que voce lembra sobre meus estudos",
        "o que voce sabe sobre meus estudos",
        "me fale sobre meus estudos",
        "como estao meus estudos",
        "quais sao meus estudos"
    ]

    if any(p in pergunta for p in perguntas_estudos):
        chaves_estudos = [
            "curso",
            "linguagem",
            "assunto_estudado",
            "assunto_atual",
            "nivel_conhecimento",
            "preferencia_aprendizado",
            "objetivo"
        ]

        registros = []

        for chave in chaves_estudos:
            valor = dados.get(chave)

            if valor is not None:
                registros.append(
                    f"- {chave.replace('_', ' ')}: {valor}"
                )

        if not registros:
            return "Ainda não tenho informações sobre seus estudos."

        return (
            "Aqui está o que lembro sobre seus estudos:\n"
            + "\n".join(registros)
        )

    perguntas_gerais = [
        "o que voce lembra sobre mim",
        "o que voce sabe sobre mim",
        "quais informacoes voce tem sobre mim",
        "me fale sobre mim",
        "quem sou eu"
    ]

    if any(p in pergunta for p in perguntas_gerais):
        dados_validos = {
            chave: valor
            for chave, valor in dados.items()
            if valor is not None
        }

        if not dados_validos:
            return "Ainda não tenho informações pessoais registradas."

        resposta = "Estas são as informações que tenho registradas:\n"

        for chave, valor in dados_validos.items():
            resposta += f"- {chave.replace('_', ' ')}: {valor}\n"

        return resposta.strip()

    consultas = {
        "nome_usuario": [
            "qual e meu nome",
            "como eu me chamo",
            "voce sabe meu nome"
        ],
        "linguagem": [
            "qual linguagem estou estudando",
            "o que estou estudando atualmente"
        ],
        "curso": [
            "qual e meu curso",
            "o que eu estudo"
        ],
        "objetivo": [
            "qual e meu objetivo"
        ],
        "nivel_conhecimento": [
            "qual meu nivel",
            "qual e meu nivel de conhecimento"
        ],
        "preferencia_aprendizado": [
            "como prefiro aprender"
        ],
        "assunto_atual": [
            "qual assunto estamos estudando",
            "qual e nosso assunto atual"
        ]
    }

    for chave, expressoes in consultas.items():
        if any(expressao in pergunta for expressao in expressoes):
            valor = dados.get(chave)

            if valor is None:
                valor = recuperar_informacao(chave)

            if valor is not None:
                return f"Tenho registrado que: {valor}."

            return "Ainda não tenho essa informação registrada."

    return None


# ==================================================
# 9. MEMÓRIA AUTOBIOGRÁFICA DA LUCI
# ==================================================

def responder_autobiografia(texto):
    pergunta = normalizar(texto)

    termos = [
        "sua historia",
        "sua origem",
        "quando voce nasceu",
        "sua data de nascimento",
        "quando foi criada",
        "quem te criou",
        "sua versao",
        "sua evolucao",
        "seus marcos"
    ]

    if not any(termo in pergunta for termo in termos):
        return None

    try:
        from .memoria_autobiografica import (
            recuperar_identidade,
            recuperar_marcos
        )

        identidade = recuperar_identidade()
        marcos = recuperar_marcos()

        if not isinstance(identidade, dict):
            identidade = {}

        if not isinstance(marcos, list):
            marcos = []

        nome = identidade.get("nome", "ANNIA LUCILLA")
        criador = identidade.get("criador", "Italo Junio")
        nascimento = identidade.get(
            "data_nascimento",
            "31 de outubro de 2026"
        )
        versao = identidade.get("versao", "1.0")

        resposta = (
            f"Sou {nome}, também conhecida como Luci. "
            f"Fui criada por {criador}. "
            f"Meu nascimento oficial foi em {nascimento}. "
            f"Minha versão atual registrada é {versao}."
        )

        if marcos:
            resposta += "\n\nAlguns marcos da minha história:"

            for marco in marcos[-5:]:
                resposta += f"\n- {marco}"

        return resposta

    except Exception:
        return (
            "Sou a ANNIA LUCILLA, também chamada de Luci. "
            "Meu criador é Italo Junio e meu nascimento oficial "
            "foi em 31 de outubro de 2026. "
            "Minha versão atual é 1.0."
        )
