
from cerebro.conhecimento import buscar_conhecimentos_verificados
from cerebro.avaliador_conhecimentos import avaliar_candidatos

print("\nRECUPERANDO MEMORIA VERIFICADA...")

conhecimentos = buscar_conhecimentos_verificados("Python")

print("Conhecimentos encontrados:", len(conhecimentos))

candidato = {
    "id_candidato": 999,
    "assunto": "O que é Python?",
    "fonte": "https://www.python.org/",
    "conteudo_original": (
        "Python é uma linguagem de programação de alto nível, "
        "interpretada e de propósito geral. "
        "Foi criada por Guido van Rossum no CWI, na Holanda. "
        "Sua primeira versão pública, Python 0.9.0, "
        "foi lançada em 20 de fevereiro de 1991."
    )
}

selecao = {
    "candidatos": [candidato]
}

print("\nEXECUTANDO COMPARACAO...")

relatorio = avaliar_candidatos(
    selecao,
    conhecimentos
)

print("\nRESULTADO:")

print(
    "Comparações com memória:",
    relatorio["quantidade_comparacoes_memoria"]
)

print(
    "Possíveis divergências:",
    relatorio["quantidade_possiveis_divergencias"]
)

for item in relatorio["comparacoes_com_memoria_verificada"]:
    for comparacao in item["comparacoes"]:
        print("\nAssunto:", comparacao["assunto_existente"])
        print("Afirmação pesquisada:", comparacao["afirmacao_pesquisada"])
        print("Afirmação na memória:", comparacao["afirmacao_memoria"])
        print("Resultado:", comparacao["comparacao"]["estado"])
        print("Sinais:", comparacao["comparacao"]["sinais"])

print("\nCONHECIMENTO SALVO:", False)
print("CONHECIMENTO APROVADO:", False)
