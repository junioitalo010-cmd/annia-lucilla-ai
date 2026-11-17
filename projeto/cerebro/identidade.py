import re

from pathlib import Path
from datetime import datetime
import json
import unicodedata


PASTA_PROJETO = Path(__file__).resolve().parent.parent

ARQUIVO_IDENTIDADE = PASTA_PROJETO / "dados" / "identidade.json"
ARQUIVO_HISTORIA = PASTA_PROJETO / "dados" / "historia_luci.json"


def normalizar(texto):
    texto = str(texto or "").lower().strip()
    texto = unicodedata.normalize("NFD", texto)

    return "".join(
        caractere
        for caractere in texto
        if unicodedata.category(caractere) != "Mn"
    )


def carregar_json(caminho):
    try:
        with open(caminho, "r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)

        return dados if isinstance(dados, dict) else {}

    except (OSError, json.JSONDecodeError):
        return {}


def carregar_identidade():
    return carregar_json(ARQUIVO_IDENTIDADE)


def carregar_historia():
    return carregar_json(ARQUIVO_HISTORIA)


def obter_nome(identidade, historia):
    dados_historia = historia.get("identidade", {})

    if not isinstance(dados_historia, dict):
        dados_historia = {}

    return (
        identidade.get("nome_completo")
        or identidade.get("nome")
        or dados_historia.get("nome")
        or "ANNIA LUCILLA"
    )


def formatar_data(data):
    try:
        data_objeto = datetime.strptime(data, "%Y-%m-%d")
        return data_objeto.strftime("%d/%m/%Y")
    except (ValueError, TypeError):
        return None


def responder_identidade(pergunta):
    if not isinstance(pergunta, str) or not pergunta.strip():
        return None

    pergunta_normalizada = re.sub(r'\s+',' ',normalizar(pergunta)).strip().rstrip('.!? ')

    identidade = carregar_identidade()
    historia = carregar_historia()

    dados_historia = historia.get("identidade", {})

    if not isinstance(dados_historia, dict):
        dados_historia = {}

    nome = obter_nome(identidade, historia)
    apelido = (
        identidade.get("apelido")
        or dados_historia.get("apelido")
        or "Luci"
    )
    criador = (
        identidade.get("criador")
        or dados_historia.get("criador")
    )
    versao = identidade.get("versao")
    proposito = identidade.get("proposito")

    data_nascimento = (
        dados_historia.get("data_nascimento")
        or identidade.get("data_nascimento")
    )

    def contem(expressao):
        return expressao in pergunta_normalizada

    # O objeto da pergunta é o criador, mesmo contendo a palavra "nome".
    # Correspondência completa evita capturar citações e perguntas compostas.
    nome_criador=re.fullmatch(
        r'(?:qual(?: e)?(?: o)? nome (?:do|de) (?:seu|teu) criador|'
        r'como se chama (?:o )?(?:seu|teu) criador|'
        r'qual(?: e)?(?: o)? nome de quem (?:te criou|criou voce))',
        pergunta_normalizada)
    if nome_criador:
        if criador:return f'Meu criador é {criador}.'
        return 'A informação sobre meu criador ainda não está registrada.'

    # VERSAO
    termos_versao = (
        "qual sua versao",
        "qual e sua versao",
        "qual e a sua versao",
        "qual a sua versao",
        "qual versao voce e",
        "em qual versao voce esta",
        "qual e o numero da sua versao"
    )

    if any(contem(termo) for termo in termos_versao):
        if versao:
            return f"Sou a {nome}, versão {versao}."

        return "Minha versão ainda não está registrada."

    # NOME
    termos_nome = (
        "qual seu nome",
        "qual e seu nome",
        "qual e o seu nome",
        "qual o seu nome",
        "qual seu nome completo",
        "qual e seu nome completo",
        "qual e o seu nome completo",
        "como voce se chama",
        "quem e voce",
        "quem voce e"
    )

    if any(contem(termo) for termo in termos_nome):
        return f"Meu nome é {nome}, mas você pode me chamar de {apelido}."

    # APELIDO
    termos_apelido = (
        "qual seu apelido",
        "qual e seu apelido",
        "como posso te chamar",
        "posso te chamar de que"
    )

    if any(contem(termo) for termo in termos_apelido):
        return f"Meu apelido é {apelido}."

    # CRIADOR
    termos_criador = (
        "quem criou voce",
        "quem te criou",
        "quem e seu criador",
        "quem e o seu criador",
        "quem desenvolveu voce",
        "quem desenvolveu a luci"
    )

    if any(contem(termo) for termo in termos_criador):
        if criador:
            return (
                f"Fui criada por {criador}, "
                f"como parte do projeto {nome}."
            )

        return "A informação sobre meu criador ainda não está registrada."

    # DATA DE NASCIMENTO
    termos_nascimento = (
        "quando voce nasceu",
        "quando foi seu nascimento",
        "qual sua data de nascimento",
        "qual e sua data de nascimento",
        "quando voce foi criada",
        "qual o dia do seu nascimento"
    )

    if any(contem(termo) for termo in termos_nascimento):
        data_formatada = formatar_data(data_nascimento)

        if data_formatada:
            return (
                f"Nasci oficialmente em {data_formatada}, "
                "data que marca o início do meu desenvolvimento."
            )

        return "Minha data de nascimento ainda não está registrada."

    # PROPOSITO
    termos_proposito = (
        "qual seu proposito",
        "qual e seu proposito",
        "qual o seu proposito",
        "qual e o seu proposito",
        "qual sua finalidade",
        "para que voce foi criada",
        "para que voce existe",
        "qual sua funcao"
    )

    if any(contem(termo) for termo in termos_proposito):
        if proposito:
            proposito = proposito.strip()
            proposito = proposito[0].lower() + proposito[1:]

            return f"Meu propósito é {proposito}"

        return "Meu propósito ainda não está registrado."

    return None
