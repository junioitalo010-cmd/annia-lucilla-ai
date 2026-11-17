 
import json
import re
import unicodedata

from pathlib import Path
from datetime import datetime


# ==================================================
# CONFIGURAÇÕES
# ==================================================

PASTA_DADOS = Path(__file__).resolve().parent.parent / "dados"
ARQUIVO_DECISOES = PASTA_DADOS / "decisoes.json"

LIMITE_DECISOES = 500
LIMITE_HISTORICO_RESULTADOS = 100
VERSAO_MEMORIA = 2

RESULTADOS_CONHECIDOS = (
    "pendente",
    "sucesso",
    "falha",
    "inconclusivo"
)


def data_atual():
    return datetime.now().astimezone().isoformat(
        timespec="seconds"
    )


# ==================================================
# ESTRUTURA PADRÃO
# ==================================================

def memoria_padrao():
    return {
        "versao": VERSAO_MEMORIA,
        "proximo_id": 1,
        "decisoes": []
    }


# ==================================================
# NORMALIZAÇÃO E VALIDAÇÃO
# ==================================================

def normalizar_texto(texto):
    texto = unicodedata.normalize("NFKD", texto.lower())

    return "".join(
        caractere
        for caractere in texto
        if not unicodedata.combining(caractere)
    )


def validar_confianca(confianca):
    if confianca is None:
        return

    if (
        isinstance(confianca, bool)
        or not isinstance(confianca, (int, float))
        or not 0 <= confianca <= 1
    ):
        raise ValueError(
            "A confiança deve ser um número entre 0 e 1."
        )


def normalizar_decisao(decisao):
    decisao.setdefault("justificativa", "")
    decisao.setdefault("resultado", "pendente")
    decisao.setdefault("confianca", None)
    decisao.setdefault("historico_resultados", [])

    if not isinstance(decisao["historico_resultados"], list):
        decisao["historico_resultados"] = []

    return decisao


# ==================================================
# VALIDAÇÃO E CARREGAMENTO
# ==================================================

def carregar_memoria_decisoes():
    PASTA_DADOS.mkdir(parents=True, exist_ok=True)

    if not ARQUIVO_DECISOES.exists():
        memoria = memoria_padrao()
        salvar_memoria_decisoes(memoria)
        return memoria

    try:
        with open(
            ARQUIVO_DECISOES,
            "r",
            encoding="utf-8"
        ) as arquivo:
            memoria = json.load(arquivo)

        if not isinstance(memoria, dict):
            raise ValueError("Estrutura da memória inválida.")

        if not isinstance(memoria.get("decisoes"), list):
            raise ValueError("Lista de decisões inválida.")

        memoria.setdefault("versao", 1)
        memoria.setdefault("proximo_id", 1)

        if (
            isinstance(memoria["proximo_id"], bool)
            or not isinstance(memoria["proximo_id"], int)
            or memoria["proximo_id"] < 1
        ):
            memoria["proximo_id"] = 1

        decisoes_validas = []

        for item in memoria["decisoes"]:
            if (
                isinstance(item, dict)
                and isinstance(item.get("id"), int)
                and not isinstance(item.get("id"), bool)
            ):
                decisoes_validas.append(
                    normalizar_decisao(item)
                )

        memoria["decisoes"] = decisoes_validas

        maior_id = max(
            (item["id"] for item in decisoes_validas),
            default=0
        )

        memoria["proximo_id"] = max(
            memoria["proximo_id"],
            maior_id + 1
        )

        memoria["versao"] = VERSAO_MEMORIA

        return memoria

    except (json.JSONDecodeError, OSError, ValueError) as erro:
        raise RuntimeError(
            f"Não foi possível carregar a memória de decisões: {erro}"
        ) from erro


# ==================================================
# SALVAMENTO PROTEGIDO
# ==================================================

def salvar_memoria_decisoes(memoria):
    PASTA_DADOS.mkdir(parents=True, exist_ok=True)

    arquivo_temporario = ARQUIVO_DECISOES.with_suffix(".tmp")

    try:
        with open(
            arquivo_temporario,
            "w",
            encoding="utf-8"
        ) as arquivo:

            json.dump(
                memoria,
                arquivo,
                ensure_ascii=False,
                indent=4
            )

            arquivo.flush()

        arquivo_temporario.replace(ARQUIVO_DECISOES)

        return True

    except (OSError, TypeError, ValueError):
        if arquivo_temporario.exists():
            arquivo_temporario.unlink()

        raise


# ==================================================
# REGISTRAR DECISÃO
# ==================================================

def registrar_decisao(
    objetivo,
    acao,
    justificativa="",
    resultado="pendente",
    confianca=None
):
    if not isinstance(objetivo, str) or not objetivo.strip():
        raise ValueError("O objetivo precisa ser informado.")

    if not isinstance(acao, str) or not acao.strip():
        raise ValueError("A ação precisa ser informada.")

    if not isinstance(justificativa, str):
        raise ValueError("A justificativa precisa ser um texto.")

    if not isinstance(resultado, str) or not resultado.strip():
        raise ValueError("O resultado precisa ser informado.")

    validar_confianca(confianca)

    memoria = carregar_memoria_decisoes()

    identificador = memoria["proximo_id"]

    decisao = {
        "id": identificador,
        "data": data_atual(),
        "objetivo": objetivo.strip(),
        "acao": acao.strip(),
        "justificativa": justificativa.strip(),
        "resultado": resultado.strip(),
        "confianca": confianca,
        "historico_resultados": []
    }

    if len(memoria["decisoes"]) >= LIMITE_DECISOES:
        memoria["decisoes"].pop(0)

    memoria["decisoes"].append(decisao)
    memoria["proximo_id"] += 1

    salvar_memoria_decisoes(memoria)

    return decisao


# ==================================================
# RECUPERAR DECISÕES
# ==================================================

def recuperar_decisoes(limite=20):
    if (
        isinstance(limite, bool)
        or not isinstance(limite, int)
        or limite < 1
    ):
        raise ValueError(
            "O limite precisa ser um inteiro positivo."
        )

    memoria = carregar_memoria_decisoes()

    return list(
        reversed(memoria["decisoes"][-limite:])
    )


def recuperar_decisao_por_id(identificador):
    memoria = carregar_memoria_decisoes()

    for decisao in memoria["decisoes"]:
        if decisao["id"] == identificador:
            return decisao

    return None


# ==================================================
# PESQUISA DE DECISÕES
# ==================================================

def buscar_decisoes(consulta, limite=10):
    if not isinstance(consulta, str) or not consulta.strip():
        return []

    if (
        isinstance(limite, bool)
        or not isinstance(limite, int)
        or limite < 1
    ):
        raise ValueError(
            "O limite precisa ser um inteiro positivo."
        )

    memoria = carregar_memoria_decisoes()

    palavras = set(
        re.findall(r"\w+", normalizar_texto(consulta))
    )

    resultados = []

    for decisao in memoria["decisoes"]:
        texto = " ".join([
            str(decisao.get("objetivo", "")),
            str(decisao.get("acao", "")),
            str(decisao.get("justificativa", "")),
            str(decisao.get("resultado", ""))
        ])

        palavras_decisao = set(
            re.findall(r"\w+", normalizar_texto(texto))
        )

        correspondencias = palavras & palavras_decisao

        if correspondencias:
            resultados.append((
                len(correspondencias),
                decisao
            ))

    resultados.sort(
        key=lambda item: (
            item[0],
            item[1]["id"]
        ),
        reverse=True
    )

    return [
        decisao
        for _, decisao in resultados[:limite]
    ]


# ==================================================
# REGISTRAR FEEDBACK DE UMA DECISÃO
# ==================================================

def registrar_feedback_decisao(
    identificador,
    resultado,
    justificativa="",
    origem="usuario",
    confianca=None
):
    if not isinstance(resultado, str) or not resultado.strip():
        raise ValueError("O resultado precisa ser informado.")

    if not isinstance(justificativa, str):
        raise ValueError("A justificativa precisa ser um texto.")

    if not isinstance(origem, str) or not origem.strip():
        raise ValueError("A origem precisa ser informada.")

    validar_confianca(confianca)

    memoria = carregar_memoria_decisoes()

    for decisao in memoria["decisoes"]:
        if decisao["id"] == identificador:

            resultado_anterior = decisao.get(
                "resultado",
                "pendente"
            )

            avaliacao = {
                "data": data_atual(),
                "resultado_anterior": resultado_anterior,
                "resultado_novo": resultado.strip(),
                "justificativa": justificativa.strip(),
                "origem": origem.strip(),
                "confianca": confianca
            }

            historico = decisao["historico_resultados"]

            historico.append(avaliacao)

            if len(historico) > LIMITE_HISTORICO_RESULTADOS:
                decisao["historico_resultados"] = (
                    historico[-LIMITE_HISTORICO_RESULTADOS:]
                )

            decisao["resultado"] = resultado.strip()
            decisao["confianca"] = confianca
            decisao["data_atualizacao"] = data_atual()

            salvar_memoria_decisoes(memoria)

            return avaliacao

    return None


# ==================================================
# ATUALIZAR RESULTADO (COMPATIBILIDADE)
# ==================================================

def atualizar_resultado(
    identificador,
    resultado,
    justificativa="",
    origem="sistema",
    confianca=None
):
    avaliacao = registrar_feedback_decisao(
        identificador=identificador,
        resultado=resultado,
        justificativa=justificativa,
        origem=origem,
        confianca=confianca
    )

    return avaliacao is not None


# ==================================================
# RECUPERAR HISTÓRICO DE RESULTADOS
# ==================================================

def recuperar_historico_resultados(identificador):
    decisao = recuperar_decisao_por_id(identificador)

    if decisao is None:
        return []

    return list(
        decisao.get("historico_resultados", [])
    )


# ==================================================
# ESTATÍSTICAS
# ==================================================

def contar_decisoes():
    memoria = carregar_memoria_decisoes()

    return len(memoria["decisoes"])


def contar_resultados():
    memoria = carregar_memoria_decisoes()

    estatisticas = {
        "total": 0,
        "pendente": 0,
        "sucesso": 0,
        "falha": 0,
        "inconclusivo": 0,
        "outros": 0
    }

    for decisao in memoria["decisoes"]:
        resultado = str(
            decisao.get("resultado", "pendente")
        ).strip().lower()

        estatisticas["total"] += 1

        if resultado in RESULTADOS_CONHECIDOS:
            estatisticas[resultado] += 1
        else:
            estatisticas["outros"] += 1

    return estatisticas


# ==================================================
# EXIBIR DECISÕES
# ==================================================

def exibir_decisoes(limite=10):
    decisoes = recuperar_decisoes(limite)

    print("\n================================")
    print("     MEMÓRIA DE DECISÕES")
    print("================================")

    if not decisoes:
        print("Nenhuma decisão registrada.")
        return

    for decisao in decisoes:
        print(f"\nID: {decisao['id']}")
        print(f"Data: {decisao['data']}")
        print(f"Objetivo: {decisao['objetivo']}")
        print(f"Ação: {decisao['acao']}")
        print(f"Justificativa: {decisao['justificativa']}")
        print(f"Resultado: {decisao['resultado']}")
        print(f"Confiança: {decisao['confianca']}")
        print(
            "Avaliações registradas:",
            len(decisao.get("historico_resultados", []))
        )
