 
from pathlib import Path
from datetime import datetime
import json
import re
import unicodedata


PASTA_PROJETO = Path(__file__).resolve().parent.parent
ARQUIVO_MEMORIA = PASTA_PROJETO / "dados" / "memoria.json"
_persistencia = None


def configurar_persistencia_sqlite(caminho=None):
    """Opt-in explicito da bancada, antes de iniciar trabalhadores.

    None restaura backend JSON. Nao migra dados nem cria banco automaticamente.
    """
    global _persistencia
    from .persistencia_sqlite import MemoriaSQLite
    _persistencia = MemoriaSQLite(caminho) if caminho is not None else None


def _atualizar_memoria(mutacao, operacao):
    if _persistencia is not None:
        return _persistencia.atualizar(mutacao, operacao)
    memoria = carregar_memoria()
    resultado = mutacao(memoria)
    salvar_memoria(memoria)
    return resultado


def estado_persistencia():
    """Checagem pontual, sem expor conteudo, caminhos ou excecoes."""
    if _persistencia is None:
        return {'backend': 'json', 'disponivel': None, 'estado': 'nao_verificado'}
    import sqlite3
    try:
        _persistencia.ler()
        return {'backend': 'sqlite', 'disponivel': True, 'estado': 'disponivel'}
    except (sqlite3.Error, OSError, ValueError):
        return {'backend': 'sqlite', 'disponivel': False, 'estado': 'indisponivel'}

LIMITE_HISTORICO = 200
LIMITE_RESUMOS = 50

PALAVRAS_IGNORADAS = {
    "a", "o", "as", "os", "um", "uma", "uns", "umas",
    "de", "do", "da", "dos", "das", "em", "no", "na",
    "nos", "nas", "para", "por", "com", "sem", "e",
    "ou", "que", "qual", "quais", "como", "quando",
    "onde", "quem", "porque", "meu", "minha", "meus",
    "minhas", "seu", "sua", "seus", "suas", "eu",
    "voce", "ele", "ela", "isso", "isto", "esse",
    "essa", "este", "esta", "foi", "ser", "estar",
    "ter", "tem", "tinha", "muito", "mais", "menos",
    "sobre", "tambem", "ja", "agora", "entao"
}


# Estrutura padrão da memória
def memoria_padrao():
    return {
        "versao": 3,
        "informacoes_usuario": {},
        "historico": [],
        "resumos": []
    }


# Carrega a memória do computador
def carregar_memoria():
    if _persistencia is not None:
        return _persistencia.ler()
    if not ARQUIVO_MEMORIA.exists():
        return memoria_padrao()

    if ARQUIVO_MEMORIA.stat().st_size == 0:
        return memoria_padrao()

    try:
        with open(ARQUIVO_MEMORIA, "r", encoding="utf-8") as arquivo:
            memoria = json.load(arquivo)

    except json.JSONDecodeError as erro:
        raise ValueError(
            "O arquivo de memória está com formato inválido. "
            "Faça uma cópia de segurança antes de alterá-lo."
        ) from erro

    if not isinstance(memoria, dict):
        raise ValueError("A estrutura do arquivo de memória é inválida.")

    # Compatibilidade com versões anteriores
    memoria.setdefault("versao", 3)
    memoria.setdefault("informacoes_usuario", {})
    memoria.setdefault("historico", [])
    memoria.setdefault("resumos", [])

    if not isinstance(memoria["informacoes_usuario"], dict):
        memoria["informacoes_usuario"] = {}

    if not isinstance(memoria["historico"], list):
        memoria["historico"] = []

    if not isinstance(memoria["resumos"], list):
        memoria["resumos"] = []

    memoria["versao"] = 3

    return memoria


# Salva a memória no computador
def salvar_memoria(memoria):
    if _persistencia is not None:
        return _persistencia.salvar(memoria)
    ARQUIVO_MEMORIA.parent.mkdir(parents=True, exist_ok=True)

    arquivo_temporario = ARQUIVO_MEMORIA.with_suffix(".tmp")

    with open(arquivo_temporario, "w", encoding="utf-8") as arquivo:
        json.dump(
            memoria,
            arquivo,
            ensure_ascii=False,
            indent=4
        )

    arquivo_temporario.replace(ARQUIVO_MEMORIA)

    return True


# Guarda ou atualiza uma informação
def guardar_informacao(chave, valor):
    if not chave or valor is None:
        return False

    def alterar(memoria):
        memoria["informacoes_usuario"][chave] = valor
        return True
    return _atualizar_memoria(alterar, 'guardar_informacao')


# Recupera uma informação específica
def recuperar_informacao(chave):
    memoria = carregar_memoria()
    return memoria["informacoes_usuario"].get(chave)


# Recupera todas as informações armazenadas
def recuperar_todas_informacoes():
    memoria = carregar_memoria()
    return memoria["informacoes_usuario"]


# Remove uma informação específica
def esquecer_informacao(chave):
    def alterar(memoria):
        if chave in memoria["informacoes_usuario"]:
            del memoria["informacoes_usuario"][chave]
            return True
        return False
    return _atualizar_memoria(alterar, 'esquecer_informacao')


# Guarda uma mensagem no histórico
def guardar_historico(remetente, mensagem):
    registro = {
        "remetente": remetente,
        "mensagem": mensagem,
        "data": datetime.now().astimezone().isoformat(
            timespec="seconds"
        )
    }

    def alterar(memoria):
        memoria["historico"].append(registro)
        memoria["historico"] = memoria["historico"][-LIMITE_HISTORICO:]
        return True
    return _atualizar_memoria(alterar, 'guardar_historico')


# Recupera o histórico de conversas
def recuperar_historico(limite=20):
    memoria = carregar_memoria()

    if limite <= 0:
        return []

    return memoria["historico"][-limite:]


# Normaliza texto para facilitar a busca
def normalizar_texto(texto):
    texto = str(texto).lower()

    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(
        caractere for caractere in texto
        if unicodedata.category(caractere) != "Mn"
    )

    return texto


# Extrai palavras relevantes
def extrair_palavras(texto):
    texto = normalizar_texto(texto)

    palavras = re.findall(r"[a-z0-9]+", texto)

    return {
        palavra for palavra in palavras
        if len(palavra) > 2 and palavra not in PALAVRAS_IGNORADAS
    }


# Procura mensagens antigas relacionadas à pergunta atual
def buscar_memorias(consulta, limite=5):
    if not consulta or limite <= 0:
        return []

    memoria = carregar_memoria()

    palavras_consulta = extrair_palavras(consulta)

    if not palavras_consulta:
        return []

    resultados = []

    # Busca no histórico
    for indice, registro in enumerate(memoria["historico"]):
        if not isinstance(registro, dict):
            continue

        mensagem = registro.get("mensagem", "")

        if not isinstance(mensagem, str):
            continue

        palavras_mensagem = extrair_palavras(mensagem)

        correspondencias = palavras_consulta.intersection(
            palavras_mensagem
        )

        if not correspondencias:
            continue

        pontuacao = len(correspondencias) / len(palavras_consulta)

        # Pequeno peso adicional para mensagens mais recentes
        pontuacao += indice / max(len(memoria["historico"]), 1) * 0.15

        resultados.append({
            "tipo": "historico",
            "remetente": registro.get("remetente", "desconhecido"),
            "mensagem": mensagem,
            "data": registro.get("data", ""),
            "pontuacao": pontuacao
        })

    # Busca nos resumos
    for resumo in memoria["resumos"]:
        if not isinstance(resumo, dict):
            continue

        texto = resumo.get("conteudo", "")

        if not isinstance(texto, str):
            continue

        palavras_resumo = extrair_palavras(texto)

        correspondencias = palavras_consulta.intersection(
            palavras_resumo
        )

        if not correspondencias:
            continue

        pontuacao = len(correspondencias) / len(palavras_consulta)

        resultados.append({
            "tipo": "resumo",
            "assunto": resumo.get("assunto", "Conversa anterior"),
            "mensagem": texto,
            "data": resumo.get("data", ""),
            "pontuacao": pontuacao
        })

    resultados.sort(
        key=lambda item: item["pontuacao"],
        reverse=True
    )

    return resultados[:limite]


# Salva um resumo de conversa
def guardar_resumo(assunto, conteudo):
    if not assunto or not conteudo:
        return False

    resumo = {
        "assunto": assunto,
        "conteudo": conteudo,
        "data": datetime.now().astimezone().isoformat(
            timespec="seconds"
        )
    }

    def alterar(memoria):
        memoria["resumos"].append(resumo)
        memoria["resumos"] = memoria["resumos"][-LIMITE_RESUMOS:]
        return True
    return _atualizar_memoria(alterar, 'guardar_resumo')


# Recupera os resumos armazenados
def recuperar_resumos(limite=10):
    memoria = carregar_memoria()

    if limite <= 0:
        return []

    return memoria["resumos"][-limite:]


# Monta um contexto de lembranças para a IA
def montar_contexto_memoria(consulta, limite=5):
    informacoes = recuperar_todas_informacoes()
    lembrancas = buscar_memorias(consulta, limite)

    partes = []

    if informacoes:
        partes.append("INFORMAÇÕES CONHECIDAS SOBRE O USUÁRIO:")

        for chave, valor in informacoes.items():
            partes.append(f"- {chave.replace('_', ' ')}: {valor}")

    if lembrancas:
        partes.append("\nLEMBRANÇAS RELACIONADAS À CONVERSA:")

        for lembranca in lembrancas:
            partes.append(
                f"- [{lembranca['tipo']}] "
                f"{lembranca['mensagem']}"
            )

    if not partes:
        return "Nenhuma lembrança relevante encontrada."

    return "\n".join(partes)


# Exibe um resumo da memória
def exibir_memoria():
    memoria = carregar_memoria()

    print("\n========== MEMÓRIA DA LUCI ==========")

    print("\nINFORMAÇÕES ARMAZENADAS:")

    for chave, valor in memoria["informacoes_usuario"].items():
        print(f"{chave}: {valor}")

    print("\nTOTAL DE MENSAGENS:")
    print(len(memoria["historico"]))

    print("\nTOTAL DE RESUMOS:")
    print(len(memoria["resumos"]))

    print("\n=====================================")

def recuperar_declaracoes_relevantes(consulta, limite=5):
    """Recupera dados do usuario; nao interpreta nem executa instrucoes salvas.

    Heuristica lexical conservadora, limitada ao historico ja retido.
    Perguntas e pedidos de consulta nao servem de declaracao pessoal.
    """
    if not isinstance(consulta, str) or not consulta.strip():
        return []
    if isinstance(limite, bool) or not isinstance(limite, int) or not 1 <= limite <= 10:
        raise ValueError("Limite de declaracoes deve estar entre 1 e 10.")
    termos = extrair_palavras(consulta)
    if not termos:
        return []
    candidatos = []
    vistos = set()
    registros = recuperar_historico(LIMITE_HISTORICO)
    if not isinstance(registros, list):
        return []
    for indice in range(len(registros) - 1, -1, -1):
        registro = registros[indice]
        if not isinstance(registro, dict) or registro.get("remetente") != "usuario":
            continue
        texto = registro.get("mensagem")
        if not isinstance(texto, str) or not texto.strip() or len(texto) > 2000:
            continue
        texto = texto.strip()
        normalizado = re.sub(r"\s+", " ", normalizar_texto(texto)).strip()
        if "?" in texto or re.match(
            r"^(?:qual|quais|quem|quando|onde|como|por que|voce lembra|voce recorda|"
            r"lembra|recorda|recupere|lembre|me diga|me conte|diga|confira|verifique)\b",
            normalizado
        ):
            continue
        comuns = termos & extrair_palavras(texto)
        if not comuns or normalizado in vistos:
            continue
        vistos.add(normalizado)
        candidatos.append((len(comuns) / len(termos), indice, texto))
    candidatos.sort(key=lambda item: (item[0], item[1]), reverse=True)
    selecionados = []
    tamanho = 0
    for _, indice, texto in candidatos:
        if tamanho + len(texto) > 5000:
            continue
        selecionados.append((indice, texto)); tamanho += len(texto)
        if len(selecionados) >= limite:
            break
    selecionados.sort(key=lambda item: item[0])
    return [{"remetente": "usuario", "mensagem": texto, "posicao_historico": indice}
            for indice, texto in selecionados]


def recuperar_contexto_conversa(limite=12):
    """
    Recupera as mensagens recentes em ordem cronológica,
    preservando a identificação de quem falou.
    """

    if isinstance(limite, bool) or not isinstance(limite, int):
        raise ValueError("O limite deve ser um número inteiro.")

    if not 1 <= limite <= 50:
        raise ValueError("O limite deve estar entre 1 e 50.")

    registros = recuperar_historico(limite)

    mensagens = []

    for registro in registros:
        if not isinstance(registro, dict):
            continue

        remetente = registro.get("remetente")
        mensagem = registro.get("mensagem")

        if remetente not in ("usuario", "luci"):
            continue

        if not isinstance(mensagem, str) or not mensagem.strip():
            continue

        mensagens.append({
            "remetente": remetente,
            "mensagem": mensagem.strip()
        })

    return mensagens


if __name__ == "__main__":
    print("TESTE DA MEMÓRIA INTELIGENTE")

    print("\nInformações já existentes:")
    exibir_memoria()

    print("\nTeste de busca:")
    consulta = input("Digite um assunto para pesquisar: ")

    resultados = buscar_memorias(consulta)

    for resultado in resultados:
        print(
            f"\n{resultado['tipo']}: "
            f"{resultado['mensagem']}"
        )

    print("\nTeste de contexto:")

    print(montar_contexto_memoria(consulta))


def caminho_arquivo_conversas():
    """Local do backend configurado; consulta do arquivo abre conexao somente-leitura."""
    return _persistencia.caminho if _persistencia is not None else None
