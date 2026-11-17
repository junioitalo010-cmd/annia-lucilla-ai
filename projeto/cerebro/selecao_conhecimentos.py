
import re
import unicodedata
from collections import defaultdict


class ErroSelecaoConhecimentos(Exception):
    """Erro durante a seleção de conhecimentos candidatos."""
    pass


def normalizar(texto):
    texto = str(texto).lower().strip()

    texto = unicodedata.normalize("NFD", texto)

    return "".join(
        caractere
        for caractere in texto
        if unicodedata.category(caractere) != "Mn"
    )


def extrair_termos(texto):
    texto = normalizar(texto)

    palavras = re.findall(r"\b[a-z0-9]{3,}\b", texto)

    ignoradas = {
        "que", "para", "com", "sem", "uma", "uns", "umas",
        "dos", "das", "nos", "nas", "por", "sobre", "entre",
        "como", "quando", "onde", "qual", "quais", "quem",
        "mais", "menos", "muito", "tambem", "isso", "essa",
        "esse", "esta", "este", "sua", "seu", "seus", "suas",
        "the", "and", "for", "with", "from", "this", "that",
        "read", "more", "about", "your", "you", "are", "was"
    }

    return {
        palavra
        for palavra in palavras
        if palavra not in ignoradas
    }


def obter_dominios_distintos(resultados):
    return {
        resultado.get("dominio", "")
        for resultado in resultados
        if resultado.get("dominio")
    }


def calcular_relevancia(
    resultado,
    dominios,
    termos_compartilhados
):
    """
    Calcula um indicador de interesse para avaliação.

    Não representa probabilidade de verdade nem confiabilidade.
    """

    dominio = resultado.get("dominio", "")
    conteudo = resultado.get("conteudo", "")
    titulo = resultado.get("titulo", "")

    termos = extrair_termos(f"{titulo} {conteudo}")

    pontos = 0

    if conteudo.strip():
        pontos += 1

    if len(termos) >= 8:
        pontos += 1

    if dominio:
        pontos += 1

    termos_presentes = [
        item["termo"]
        for item in termos_compartilhados
        if item["termo"] in termos
    ]

    if termos_presentes:
        pontos += 1

    quantidade_dominios = len(dominios)

    if quantidade_dominios >= 3:
        pontos += 1

    return {
        "pontuacao_interesse": pontos,
        "termos_compartilhados": termos_presentes,
        "observacao": (
            "Pontuação usada apenas para organizar a avaliação. "
            "Não representa confiabilidade ou confirmação factual."
        )
    }


def selecionar_conhecimentos(
    analise,
    comparacao=None,
    limite=10
):
    """
    Organiza resultados de pesquisa como candidatos.

    Nenhum candidato é gravado automaticamente na base
    de conhecimentos.
    """

    if not isinstance(analise, dict):
        raise ErroSelecaoConhecimentos(
            "A análise precisa ser um dicionário."
        )

    resultados = analise.get("resultados")

    if not isinstance(resultados, list):
        raise ErroSelecaoConhecimentos(
            "A análise não possui uma lista válida de resultados."
        )

    if not isinstance(limite, int) or limite < 1:
        raise ValueError("O limite precisa ser um inteiro positivo.")

    if comparacao is None:
        comparacao = {}

    if not isinstance(comparacao, dict):
        raise ErroSelecaoConhecimentos(
            "A comparação precisa ser um dicionário."
        )

    dominios = obter_dominios_distintos(resultados)

    termos_compartilhados = comparacao.get(
        "termos_compartilhados",
        []
    )

    if not isinstance(termos_compartilhados, list):
        termos_compartilhados = []

    candidatos = []

    for indice, resultado in enumerate(resultados, start=1):

        if not isinstance(resultado, dict):
            continue

        titulo = str(resultado.get("titulo", "")).strip()
        url = str(resultado.get("url", "")).strip()
        conteudo = str(resultado.get("conteudo", "")).strip()
        dominio = str(resultado.get("dominio", "")).strip()

        if not conteudo:
            continue

        if not url:
            continue

        relevancia = calcular_relevancia(
            resultado,
            dominios,
            termos_compartilhados
        )

        candidato = {
            "id_candidato": indice,
            "assunto": titulo or "Assunto não identificado",
            "conteudo_original": conteudo,
            "fonte": url,
            "dominio": dominio or "dominio_desconhecido",
            "pontuacao_interesse": relevancia[
                "pontuacao_interesse"
            ],
            "termos_compartilhados": relevancia[
                "termos_compartilhados"
            ],
            "estado": "pendente_avaliacao",
            "verificado": False,
            "aprovado_para_base": False,
            "observacao": relevancia["observacao"]
        }

        candidatos.append(candidato)

    candidatos.sort(
        key=lambda item: item["pontuacao_interesse"],
        reverse=True
    )

    candidatos = candidatos[:limite]

    return {
        "estado": "selecao_concluida",
        "quantidade_resultados_recebidos": len(resultados),
        "quantidade_candidatos": len(candidatos),
        "quantidade_dominios": len(dominios),
        "candidatos": candidatos,
        "gravacao_automatica": False,
        "conhecimentos_verificados": False,
        "observacao_geral": (
            "Os candidatos estão pendentes de avaliação. "
            "A pontuação indica apenas prioridade de análise. "
            "Nenhum conteúdo foi registrado como conhecimento "
            "verificado."
        )
    }


def exibir_candidatos(selecao):
    print("\n" + "=" * 60)
    print("ANNIA LUCILLA - SELEÇÃO DE CONHECIMENTOS")
    print("=" * 60)

    print(
        "\nResultados recebidos:",
        selecao["quantidade_resultados_recebidos"]
    )

    print(
        "Candidatos selecionados:",
        selecao["quantidade_candidatos"]
    )

    print(
        "Domínios diferentes:",
        selecao["quantidade_dominios"]
    )

    for candidato in selecao["candidatos"]:

        print("\n" + "-" * 60)

        print(
            f"Candidato {candidato['id_candidato']}: "
            f"{candidato['assunto']}"
        )

        print(
            "Domínio:",
            candidato["dominio"]
        )

        print(
            "Pontuação de interesse:",
            candidato["pontuacao_interesse"]
        )

        print(
            "Estado:",
            candidato["estado"]
        )

        if candidato["termos_compartilhados"]:
            print(
                "Termos compartilhados:",
                ", ".join(candidato["termos_compartilhados"])
            )
        else:
            print("Termos compartilhados: nenhum identificado.")

        print("\nTrecho encontrado:")

        trecho = candidato["conteudo_original"]

        if len(trecho) > 350:
            trecho = trecho[:350] + "..."

        print(trecho)

        print("\nFonte:")
        print(candidato["fonte"])

        print(
            "Verificado:",
            candidato["verificado"]
        )

    print("\n" + "=" * 60)

    print(selecao["observacao_geral"])

    print("=" * 60)


if __name__ == "__main__":

    from cerebro.pesquisa_web import (
        pesquisar_web,
        ErroPesquisaWeb
    )

    from cerebro.analisador_fontes import analisar_resultados

    from cerebro.comparador_evidencias import comparar_evidencias

    try:
        print("Pesquisando informações...")

        pesquisa = pesquisar_web(
            "Como funciona uma geladeira?",
            quantidade=5
        )

        print("\nAnalisando fontes...")

        analise = analisar_resultados(pesquisa)

        print("\nComparando evidências...")

        comparacao = comparar_evidencias(analise)

        print("\nSelecionando conhecimentos candidatos...")

        selecao = selecionar_conhecimentos(
            analise,
            comparacao,
            limite=10
        )

        exibir_candidatos(selecao)

    except ErroPesquisaWeb as erro:
        print(f"\nErro na pesquisa: {erro}")

    except (ErroSelecaoConhecimentos, ValueError, TypeError) as erro:
        print(f"\nErro na seleção: {erro}")
