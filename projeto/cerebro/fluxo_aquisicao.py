 
from datetime import datetime

from cerebro.pesquisa_web import pesquisar_web, ErroPesquisaWeb
from cerebro.analisador_fontes import analisar_resultados
from cerebro.comparador_evidencias import comparar_evidencias
from cerebro.selecao_conhecimentos import selecionar_conhecimentos
from cerebro.avaliador_conhecimentos import avaliar_candidatos
from cerebro.conhecimento import buscar_conhecimentos_verificados


def carregar_conhecimentos_confiaveis(consulta, conhecimentos=None):
    """
    Recupera somente conhecimentos verificados.

    Se uma lista for fornecida externamente, também filtra
    os registros para impedir o uso de conhecimentos pendentes
    ou contestados como evidência confiável.
    """

    if conhecimentos is None:
        conhecimentos = buscar_conhecimentos_verificados(consulta)

    if not isinstance(conhecimentos, list):
        raise ValueError(
            "A recuperação dos conhecimentos locais retornou "
            "uma estrutura inválida."
        )

    return [
        conhecimento
        for conhecimento in conhecimentos
        if isinstance(conhecimento, dict)
        and conhecimento.get("estado_verificacao") == "verificado"
    ]


def executar_fluxo_aquisicao(
    consulta,
    quantidade=5,
    limite=10,
    conhecimentos=None
):
    """
    Executa o fluxo de aquisição de conhecimento da ANNIA LUCILLA.

    Etapas:
    1. Pesquisa na web.
    2. Análise das fontes.
    3. Comparação das evidências.
    4. Seleção de conhecimentos candidatos.
    5. Recuperação da memória confiável.
    6. Avaliação dos candidatos.

    Nenhum conhecimento é salvo automaticamente.
    Nenhum candidato é marcado como verificado automaticamente.
    """

    if not isinstance(consulta, str) or not consulta.strip():
        raise ValueError("A consulta precisa ser um texto válido.")

    try:
        quantidade = max(1, min(int(quantidade), 10))
        limite = max(1, min(int(limite), 20))
    except (ValueError, TypeError):
        raise ValueError(
            "Quantidade e limite precisam ser números inteiros."
        )

    consulta = consulta.strip()

    relatorio = {
        "consulta": consulta,
        "data_execucao": datetime.now().isoformat(timespec="seconds"),
        "estado": "iniciado",
        "etapas": {},
        "pesquisa": None,
        "analise": None,
        "comparacao": None,
        "selecao": None,
        "conhecimentos_locais": {
            "quantidade": 0,
            "estado": "nao_carregados"
        },
        "avaliacao": None,
        "conhecimento_salvo": False,
        "conhecimento_verificado": False,
        "erros": []
    }

    # ETAPA 1 — PESQUISA WEB
    try:
        print("\n[1/6] Pesquisando na web...")

        pesquisa = pesquisar_web(
            consulta=consulta,
            quantidade=quantidade
        )

        relatorio["pesquisa"] = pesquisa
        relatorio["etapas"]["pesquisa"] = "concluida"

        print(
            "Pesquisa concluída:",
            pesquisa.get("quantidade_resultados", 0),
            "resultados encontrados."
        )

    except (ErroPesquisaWeb, ValueError, TypeError) as erro:
        relatorio["estado"] = "falha_na_pesquisa"
        relatorio["etapas"]["pesquisa"] = "falhou"
        relatorio["erros"].append(str(erro))
        return relatorio

    except Exception as erro:
        relatorio["estado"] = "falha_na_pesquisa"
        relatorio["etapas"]["pesquisa"] = "falhou"
        relatorio["erros"].append(
            f"Erro inesperado na pesquisa: {erro}"
        )
        return relatorio

    # ETAPA 2 — ANÁLISE DAS FONTES
    try:
        print("\n[2/6] Analisando as fontes...")

        analise = analisar_resultados(pesquisa)

        relatorio["analise"] = analise
        relatorio["etapas"]["analise"] = "concluida"

        print("Análise das fontes concluída.")

    except Exception as erro:
        relatorio["estado"] = "falha_na_analise"
        relatorio["etapas"]["analise"] = "falhou"
        relatorio["erros"].append(
            f"Erro na análise das fontes: {erro}"
        )
        return relatorio

    # ETAPA 3 — COMPARAÇÃO DAS EVIDÊNCIAS
    try:
        print("\n[3/6] Comparando evidências...")

        comparacao = comparar_evidencias(analise)

        relatorio["comparacao"] = comparacao
        relatorio["etapas"]["comparacao"] = "concluida"

        print("Comparação das evidências concluída.")

    except Exception as erro:
        relatorio["estado"] = "falha_na_comparacao"
        relatorio["etapas"]["comparacao"] = "falhou"
        relatorio["erros"].append(
            f"Erro na comparação das evidências: {erro}"
        )
        return relatorio

    # ETAPA 4 — SELEÇÃO DOS CANDIDATOS
    try:
        print("\n[4/6] Selecionando conhecimentos candidatos...")

        selecao = selecionar_conhecimentos(
            analise=analise,
            comparacao=comparacao,
            limite=limite
        )

        relatorio["selecao"] = selecao
        relatorio["etapas"]["selecao"] = "concluida"

        print("Seleção de candidatos concluída.")

    except Exception as erro:
        relatorio["estado"] = "falha_na_selecao"
        relatorio["etapas"]["selecao"] = "falhou"
        relatorio["erros"].append(
            f"Erro na seleção dos candidatos: {erro}"
        )
        return relatorio

    # ETAPA 5 — RECUPERAÇÃO DA MEMÓRIA CONFIÁVEL
    try:
        print("\n[5/6] Recuperando conhecimentos verificados...")

        conhecimentos_confiaveis = (
            carregar_conhecimentos_confiaveis(
                consulta,
                conhecimentos
            )
        )

        relatorio["conhecimentos_locais"] = {
            "quantidade": len(conhecimentos_confiaveis),
            "estado": "carregados"
        }

        relatorio["etapas"]["memoria_local"] = "concluida"

        print(
            "Conhecimentos verificados recuperados:",
            len(conhecimentos_confiaveis)
        )

    except Exception as erro:
        relatorio["estado"] = "falha_na_memoria_local"
        relatorio["etapas"]["memoria_local"] = "falhou"
        relatorio["erros"].append(
            f"Erro na recuperação da memória local: {erro}"
        )
        return relatorio

    # ETAPA 6 — AVALIAÇÃO DOS CANDIDATOS
    try:
        print("\n[6/6] Avaliando conhecimentos candidatos...")

        avaliacao = avaliar_candidatos(
            selecao=selecao,
            conhecimentos=conhecimentos_confiaveis
        )

        relatorio["avaliacao"] = avaliacao
        relatorio["etapas"]["avaliacao"] = "concluida"

        print("Avaliação concluída.")

    except Exception as erro:
        relatorio["estado"] = "falha_na_avaliacao"
        relatorio["etapas"]["avaliacao"] = "falhou"
        relatorio["erros"].append(
            f"Erro na avaliação dos candidatos: {erro}"
        )
        return relatorio

    # RESULTADO FINAL
    relatorio["estado"] = "fluxo_concluido"

    return relatorio


def exibir_relatorio(relatorio):
    """Exibe um resumo do processo de aquisição."""

    print("\n" + "=" * 60)
    print("RELATÓRIO DE AQUISIÇÃO — ANNIA LUCILLA")
    print("=" * 60)

    print("Consulta:", relatorio.get("consulta"))
    print("Data:", relatorio.get("data_execucao"))
    print("Estado:", relatorio.get("estado"))

    print("\nETAPAS:")

    for etapa, estado in relatorio.get("etapas", {}).items():
        print(f"- {etapa}: {estado}")

    memoria = relatorio.get("conhecimentos_locais", {})

    print("\nMEMÓRIA LOCAL:")
    print(
        "Conhecimentos verificados recuperados:",
        memoria.get("quantidade", 0)
    )
    print("Estado:", memoria.get("estado", "não informado"))

    if relatorio.get("avaliacao"):
        avaliacao = relatorio["avaliacao"]

        print("\nRESULTADO DA AVALIAÇÃO:")

        if isinstance(avaliacao, dict):
            print(
                "Estado:",
                avaliacao.get("estado", "não informado")
            )
            print(
                "Candidatos avaliados:",
                avaliacao.get("quantidade_candidatos", 0)
            )
            print(
                "Possíveis divergências:",
                avaliacao.get(
                    "quantidade_possiveis_divergencias",
                    0
                )
            )

    print("\nSEGURANÇA:")

    print(
        "Conhecimento salvo:",
        "Sim" if relatorio.get("conhecimento_salvo") else "Não"
    )

    print(
        "Conhecimento verificado:",
        "Sim" if relatorio.get("conhecimento_verificado") else "Não"
    )

    if relatorio.get("erros"):
        print("\nERROS:")

        for erro in relatorio["erros"]:
            print("-", erro)

    print("\nNenhuma informação externa foi salva automaticamente.")
    print("Nenhuma informação foi aprovada automaticamente.")

    print("=" * 60)


if __name__ == "__main__":

    consulta = input(
        "\nANNIA LUCILLA — O que deseja pesquisar?\n> "
    ).strip()

    if not consulta:
        print("Digite uma consulta para iniciar.")

    else:
        try:
            relatorio = executar_fluxo_aquisicao(
                consulta=consulta,
                quantidade=5,
                limite=10
            )

            exibir_relatorio(relatorio)

        except Exception as erro:
            print("\nNão foi possível executar o fluxo:", erro)
