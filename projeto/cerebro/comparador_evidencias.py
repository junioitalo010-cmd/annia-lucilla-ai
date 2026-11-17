import re
from itertools import combinations

from cerebro.avaliador_conhecimentos import (
    extrair_afirmacoes,
    extrair_dominio,
    dominio_raiz_simples,
    comparar_afirmacoes,
)


LIMITE_AFIRMACOES_POR_FONTE = 20


def obter_texto(valor):
    """Converte valores em texto com segurança."""
    if valor is None:
        return ""

    if isinstance(valor, str):
        return valor.strip()

    return str(valor).strip()


def obter_dominio(resultado):
    """Obtém o domínio da fonte a partir dos dados disponíveis."""

    dominio = obter_texto(resultado.get("dominio"))

    if not dominio:
        dominio = extrair_dominio(
            obter_texto(resultado.get("url"))
        )

    dominio = dominio.lower().strip()

    if dominio.startswith("www."):
        dominio = dominio[4:]

    return dominio or None


def obter_dominio_raiz(dominio):
    """
    Identifica o domínio principal para evitar contar
    subdomínios do mesmo site como fontes independentes.
    """

    if not dominio:
        return None

    dominio = dominio.lower().strip()

    if dominio.startswith("www."):
        dominio = dominio[4:]

    return dominio_raiz_simples(dominio)


def preparar_fontes(analise):
    """Organiza os resultados recebidos do analisador."""

    resultados = analise.get("resultados", [])

    if not isinstance(resultados, list):
        raise ValueError(
            "O campo resultados precisa ser uma lista."
        )

    fontes = []

    for indice, resultado in enumerate(resultados, start=1):

        if not isinstance(resultado, dict):
            continue

        titulo = obter_texto(
            resultado.get("titulo")
        )

        url = obter_texto(
            resultado.get("url")
        )

        conteudo = obter_texto(
            resultado.get("conteudo")
        )

        dominio = obter_dominio(resultado)
        dominio_raiz = obter_dominio_raiz(dominio)

        texto_completo = f"{titulo}. {conteudo}".strip()

        afirmacoes = []

        if texto_completo:
            afirmacoes = extrair_afirmacoes(
                texto_completo
            )

        afirmacoes = [
            obter_texto(afirmacao)
            for afirmacao in afirmacoes
            if obter_texto(afirmacao)
        ]

        quantidade_original = len(afirmacoes)

        afirmacoes = afirmacoes[
            :LIMITE_AFIRMACOES_POR_FONTE
        ]

        fontes.append({
            "id": indice,
            "titulo": titulo,
            "url": url,
            "dominio": dominio,
            "dominio_raiz": dominio_raiz,
            "conteudo": conteudo,
            "afirmacoes": afirmacoes,
            "quantidade_afirmacoes": len(afirmacoes),
            "afirmacoes_limitadas": (
                quantidade_original > LIMITE_AFIRMACOES_POR_FONTE
            ),
            "pontuacao": resultado.get("pontuacao"),
            "data_publicacao": resultado.get(
                "data_publicacao"
            )
        })

    return fontes


def identificar_termos_compartilhados(fontes):
    """
    Identifica termos presentes em diferentes domínios.

    Isso representa proximidade textual, não confirmação factual.
    """

    ocorrencias = {}

    for fonte in fontes:

        dominio = fonte.get("dominio_raiz")

        if not dominio:
            continue

        texto = (
            fonte.get("titulo", "")
            + " "
            + fonte.get("conteudo", "")
        ).lower()

        termos = set(
            re.findall(r"\b[a-zA-ZÀ-ÿ0-9]{4,}\b", texto)
        )

        for termo in termos:

            if termo not in ocorrencias:
                ocorrencias[termo] = set()

            ocorrencias[termo].add(dominio)

    compartilhados = []

    for termo, dominios in ocorrencias.items():

        if len(dominios) >= 2:
            compartilhados.append({
                "termo": termo,
                "quantidade_dominios": len(dominios),
                "dominios": sorted(dominios)
            })

    compartilhados.sort(
        key=lambda item: item["quantidade_dominios"],
        reverse=True
    )

    return compartilhados


def organizar_sinais_numericos(fontes):
    """
    Organiza números encontrados nos conteúdos.

    Diferenças numéricas não são classificadas automaticamente
    como contradições.
    """

    sinais = []

    for fonte in fontes:

        numeros = re.findall(
            r"\b\d+(?:[.,]\d+)?\b",
            fonte.get("conteudo", "")
        )

        numeros = list(dict.fromkeys(numeros))

        if numeros:
            sinais.append({
                "fonte": fonte["id"],
                "dominio": fonte.get("dominio"),
                "numeros": numeros,
                "observacao": (
                    "Números identificados. "
                    "É necessário analisar o contexto antes "
                    "de comparar seus significados."
                )
            })

    return sinais


def comparar_pares_de_fontes(fontes):
    """
    Compara afirmações entre fontes de domínios diferentes.

    A comparação contextual é realizada pelo avaliador
    de conhecimentos da Luci.
    """

    comparacoes = []

    for fonte_a, fonte_b in combinations(fontes, 2):

        dominio_a = fonte_a.get("dominio_raiz")
        dominio_b = fonte_b.get("dominio_raiz")

        # Sem domínio identificável, não é possível
        # afirmar independência entre as fontes.
        if not dominio_a or not dominio_b:
            continue

        # Subdomínios e páginas do mesmo domínio
        # não são considerados fontes independentes.
        if dominio_a == dominio_b:
            continue

        afirmacoes_a = fonte_a.get("afirmacoes", [])
        afirmacoes_b = fonte_b.get("afirmacoes", [])

        comparacoes_afirmacoes = []

        for afirmacao_a in afirmacoes_a:

            for afirmacao_b in afirmacoes_b:

                resultado = comparar_afirmacoes(
                    afirmacao_a,
                    afirmacao_b,
                    assunto_a=fonte_a.get("titulo", ""),
                    assunto_b=fonte_b.get("titulo", "")
                )

                estado = resultado.get("estado")

                if estado == "sem_relacao_lexical_suficiente":
                    continue

                comparacoes_afirmacoes.append({
                    "afirmacao_fonte_1": afirmacao_a,
                    "afirmacao_fonte_2": afirmacao_b,
                    "resultado": resultado
                })

        quantidade_divergencias = sum(
            1
            for item in comparacoes_afirmacoes
            if item["resultado"].get("estado")
            == "possivel_divergencia"
        )

        quantidade_contextos_diferentes = sum(
            1
            for item in comparacoes_afirmacoes
            if item["resultado"].get("estado")
            == "contexto_insuficiente_ou_diferente"
        )

        comparacoes.append({
            "fonte_1": fonte_a["id"],
            "fonte_2": fonte_b["id"],
            "dominio_1": dominio_a,
            "dominio_2": dominio_b,
            "quantidade_afirmacoes_comparadas": len(
                comparacoes_afirmacoes
            ),
            "quantidade_possiveis_divergencias": (
                quantidade_divergencias
            ),
            "quantidade_contextos_diferentes": (
                quantidade_contextos_diferentes
            ),
            "comparacoes": comparacoes_afirmacoes
        })

    return comparacoes


def comparar_evidencias(analise):
    """
    Executa a comparação contextual das evidências.

    Esta função não confirma a verdade das informações
    e não registra conhecimentos automaticamente.
    """

    if not isinstance(analise, dict):
        raise ValueError(
            "A análise precisa ser um dicionário."
        )

    fontes = preparar_fontes(analise)

    dominios = sorted({
        fonte["dominio"]
        for fonte in fontes
        if fonte.get("dominio")
    })

    dominios_raiz = sorted({
        fonte["dominio_raiz"]
        for fonte in fontes
        if fonte.get("dominio_raiz")
    })

    termos_compartilhados = identificar_termos_compartilhados(
        fontes
    )

    comparacoes = comparar_pares_de_fontes(
        fontes
    )

    sinais_numericos = organizar_sinais_numericos(
        fontes
    )

    quantidade_comparacoes = sum(
        item["quantidade_afirmacoes_comparadas"]
        for item in comparacoes
    )

    quantidade_divergencias = sum(
        item["quantidade_possiveis_divergencias"]
        for item in comparacoes
    )

    quantidade_contextos_diferentes = sum(
        item["quantidade_contextos_diferentes"]
        for item in comparacoes
    )

    observacoes = [
        "A comparação textual não comprova a verdade das informações.",
        "Fontes do mesmo domínio não foram consideradas independentes.",
        "Diferenças numéricas precisam ser analisadas em seu contexto.",
        "Possíveis divergências exigem verificação adicional."
    ]

    if len(dominios_raiz) < 2:
        observacoes.append(
            "Não existem pelo menos dois domínios independentes "
            "identificados para comparação."
        )

    if not comparacoes:
        observacoes.append(
            "Nenhuma comparação entre domínios independentes "
            "pôde ser realizada."
        )

    return {
        "estado": "comparacao_concluida",

        "quantidade_fontes": len(fontes),

        "quantidade_dominios": len(dominios),

        "quantidade_dominios_independentes": len(
            dominios_raiz
        ),

        "dominios": dominios,

        "dominios_independentes": dominios_raiz,

        "fontes": fontes,

        "termos_compartilhados": termos_compartilhados,

        "comparacoes_entre_fontes": comparacoes,

        "quantidade_comparacoes_contextuais": (
            quantidade_comparacoes
        ),

        "quantidade_possiveis_divergencias": (
            quantidade_divergencias
        ),

        "quantidade_contextos_diferentes": (
            quantidade_contextos_diferentes
        ),

        "sinais_numericos": sinais_numericos,

        "observacoes": observacoes,

        "concordancia_factual": False,

        "contradicao_factual_confirmada": False,

        "verificacao_independente": False,

        "conhecimento_verificado": False
    }


def exibir_comparacao(comparacao):
    """Exibe o relatório de comparação de evidências."""

    print("\n========== COMPARADOR DE EVIDENCIAS DA LUCI ==========")

    print(
        "Fontes analisadas:",
        comparacao["quantidade_fontes"]
    )

    print(
        "Domínios identificados:",
        comparacao["quantidade_dominios"]
    )

    print(
        "Domínios independentes identificados:",
        comparacao["quantidade_dominios_independentes"]
    )

    print("\nDOMINIOS:")

    for dominio in comparacao["dominios"]:
        print("-", dominio)

    print("\nAFIRMACOES COMPARADAS:")

    print(
        comparacao["quantidade_comparacoes_contextuais"]
    )

    print("\nPOSSIVEIS DIVERGENCIAS:")

    print(
        comparacao["quantidade_possiveis_divergencias"]
    )

    print("\nCONTEXTOS DIFERENTES OU INSUFICIENTES:")

    print(
        comparacao["quantidade_contextos_diferentes"]
    )

    print("\nCOMPARACOES ENTRE FONTES:")

    for item in comparacao["comparacoes_entre_fontes"]:

        print(
            f"\nFonte {item['fonte_1']} "
            f"({item['dominio_1']})"
        )

        print(
            f"Fonte {item['fonte_2']} "
            f"({item['dominio_2']})"
        )

        print(
            "Afirmações comparadas:",
            item["quantidade_afirmacoes_comparadas"]
        )

        print(
            "Possíveis divergências:",
            item["quantidade_possiveis_divergencias"]
        )

    print("\nSINAIS NUMERICOS:")

    for sinal in comparacao["sinais_numericos"]:
        print(sinal)

    print("\nOBSERVACOES:")

    for observacao in comparacao["observacoes"]:
        print("-", observacao)

    print("\nESTADO:", comparacao["estado"])

    print("Concordância factual: não confirmada.")

    print("Contradição factual: não confirmada.")

    print("Verificação independente: não realizada.")

    print("Conhecimento verificado: não.")

    print("=======================================================")


def testar_comparacao_offline():
    """
    Teste local sem internet e sem consumir créditos de API.
    """

    analise_teste = {
        "consulta": "Histórico de lançamento do Python",

        "resultados": [
            {
                "titulo": "Histórico do Python",
                "url": "https://docs.python.org/historico",
                "dominio": "docs.python.org",
                "conteudo": (
                    "Python 0.9.0 foi lançado em "
                    "20 de fevereiro de 1991."
                )
            },
            {
                "titulo": "História da linguagem Python",
                "url": "https://historia.example.com/python",
                "dominio": "historia.example.com",
                "conteudo": (
                    "Python 0.9.0 foi lançado em "
                    "20 de fevereiro de 1995."
                )
            },
            {
                "titulo": "Documentação do Python",
                "url": "https://www.python.org/documentacao",
                "dominio": "www.python.org",
                "conteudo": (
                    "Python 0.9.0 foi lançado em "
                    "20 de fevereiro de 1991."
                )
            }
        ]
    }

    comparacao = comparar_evidencias(
        analise_teste
    )

    exibir_comparacao(comparacao)

    print("\n========== RESULTADO DO TESTE ==========")

    if comparacao["quantidade_fontes"] != 3:
        print("FALHA: quantidade de fontes inesperada.")
        return

    if comparacao["quantidade_dominios_independentes"] != 2:
        print("FALHA: domínios independentes incorretos.")
        return

    if comparacao["quantidade_possiveis_divergencias"] < 1:
        print("FALHA: divergência esperada não identificada.")
        return

    if comparacao["contradicao_factual_confirmada"]:
        print("FALHA: o sistema confirmou uma contradição indevidamente.")
        return

    if comparacao["conhecimento_verificado"]:
        print("FALHA: o sistema verificou conhecimento indevidamente.")
        return

    print("SUCESSO: teste offline concluído.")
    print("========================================")


if __name__ == "__main__":
    testar_comparacao_offline()