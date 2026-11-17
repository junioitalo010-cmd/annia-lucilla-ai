 
from cerebro.conhecimento import buscar_conhecimentos_verificados
from cerebro.avaliador_conhecimentos import avaliar_candidatos


# ============================================================
# TESTE DE POSSÍVEL CONTRADIÇÃO COM A MEMÓRIA
# ANNIA LUCILLA — VERSÃO 1.0
# ============================================================

print("\nTESTE DE POSSIVEL CONTRADICAO")
print("=" * 50)


# ------------------------------------------------------------
# 1. RECUPERAR CONHECIMENTO VERIFICADO
# ------------------------------------------------------------

consulta = "Python"

conhecimentos = buscar_conhecimentos_verificados(consulta)

print(f"Conhecimentos verificados recuperados: {len(conhecimentos)}")

if not conhecimentos:
    print("\nNenhum conhecimento verificado foi encontrado.")
    print("Cadastre e verifique o conhecimento antes de executar o teste.")
    raise SystemExit


# ------------------------------------------------------------
# 2. CRIAR CANDIDATO COM UMA INFORMAÇÃO DIFERENTE
# ------------------------------------------------------------

candidato = {
    "id_candidato": 1000,
    "assunto": "Python",
    "fonte": "https://www.python.org/",
    "conteudo_original": (
        "A primeira versão pública da linguagem Python, "
        "Python 0.9.0, foi lançada em 20 de fevereiro de 1995."
    )
}


# ------------------------------------------------------------
# 3. PREPARAR A SELEÇÃO
# ------------------------------------------------------------

selecao = {
    "consulta": consulta,
    "candidatos": [candidato]
}


# ------------------------------------------------------------
# 4. EXECUTAR A AVALIAÇÃO
# ------------------------------------------------------------

relatorio = avaliar_candidatos(
    selecao,
    conhecimentos
)


# ------------------------------------------------------------
# 5. EXIBIR O RESUMO
# ------------------------------------------------------------

print("\nRESULTADO DO TESTE")
print("=" * 50)

print(
    "Comparações com memória:",
    relatorio["quantidade_comparacoes_com_memoria"]
)

print(
    "Possíveis divergências:",
    relatorio.get("quantidade_possiveis_divergencias", 0)
)

print(
    "Divergências entre fontes:",
    relatorio.get("divergencias_entre_fontes", 0)
)

print(
    "Divergências com memória:",
    relatorio.get("divergencias_com_memoria", 0)
)


# ------------------------------------------------------------
# 6. EXIBIR DETALHES DAS COMPARAÇÕES COM A MEMÓRIA
# ------------------------------------------------------------

print("\nDETALHES DAS COMPARAÇÕES")
print("=" * 50)

comparacoes_encontradas = 0

for resultado in relatorio.get("resultados", []):

    comparacoes = resultado.get(
        "comparacoes_com_base_local", []
    )

    for item in comparacoes:

        comparacoes_encontradas += 1

        comparacao = item.get("comparacao", {})

        print("\nAssunto da memória:")
        print(item.get("assunto_existente", "Não informado"))

        print("\nAfirmação pesquisada:")
        print(item.get("afirmacao_pesquisada", ""))

        print("\nAfirmação na memória:")
        print(item.get("afirmacao_memoria", ""))

        print("\nEstado da comparação:")
        print(comparacao.get("estado", "Não identificado"))

        print("\nSimilaridade lexical:")
        print(comparacao.get("similaridade", 0))

        print("\nSinais identificados:")
        print(comparacao.get("sinais", []))

        print("\nContradição confirmada:")
        print(
            "Sim" if comparacao.get("contradicao_confirmada")
            else "Não"
        )

        print("-" * 50)


if comparacoes_encontradas == 0:
    print("Nenhuma comparação relevante foi encontrada.")


# ------------------------------------------------------------
# 7. VERIFICAR PROTEÇÃO DA MEMÓRIA
# ------------------------------------------------------------

print("\nSEGURANÇA DA MEMÓRIA")
print("=" * 50)

print(
    "Conhecimento aprovado automaticamente:",
    "Sim" if relatorio.get("conhecimento_aprovado") else "Não"
)

print(
    "Conhecimento salvo automaticamente:",
    "Sim" if relatorio.get("conhecimento_salvo") else "Não"
)

print(
    "Conhecimento verificado automaticamente:",
    "Sim" if relatorio.get("conhecimento_verificado") else "Não"
)

print("\nO avaliador não modifica a memória durante este teste.")

print("\nTESTE FINALIZADO")
print("=" * 50)
