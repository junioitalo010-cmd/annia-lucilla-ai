import re
import unicodedata
from collections import Counter, defaultdict
from itertools import combinations


PALAVRAS_IGNORADAS = {
    "a", "o", "as", "os", "um", "uma", "uns", "umas",
    "de", "do", "da", "dos", "das", "em", "no", "na",
    "nos", "nas", "por", "para", "com", "sem", "sobre",
    "entre", "que", "se", "e", "ou", "mas", "como",
    "quando", "onde", "qual", "quais", "quem", "porque",
    "ser", "estar", "ter", "foi", "sao", "era", "sendo",
    "tem", "tinha", "pode", "podem", "seu", "sua",
    "seus", "suas", "mais", "menos", "muito", "tambem",
    "isso", "essa", "esse", "esta", "este", "aquela",
    "aquele", "cada", "todo", "toda", "todos", "todas",
    "ele", "ela", "eles", "elas", "ao", "aos", "pela",
    "pelo", "pelas", "pelos", "the", "and", "for",
    "with", "from", "this", "that", "are", "was"
}


def normalizar(texto):
    """Remove acentos e normaliza o texto."""

    texto = str(texto).lower().strip()

    texto = unicodedata.normalize("NFD", texto)

    texto = "".join(
        caractere
        for caractere in texto
        if unicodedata.category(caractere) != "Mn"
    )

    return texto


def extrair_termos(texto):
    """Extrai termos relevantes de um texto."""

    texto = normalizar(texto)

    palavras = re.findall(r"\b[a-z0-9]{3,}\b", texto)

    return {
        palavra
        for palavra in palavras
        if palavra not in PALAVRAS_IGNORADAS
    }


def calcular_similaridade(termos_a, termos_b):
    """Calcula a similaridade lexical entre dois conjuntos."""

    if not termos_a or not termos_b:
        return 0.0

    intersecao = termos_a.intersection(termos_b)
    uniao = termos_a.union(termos_b)

    return round(len(intersecao) / len(uniao), 3)


def preparar_fontes(analise):
    """Organiza os resultados por domínio."""

    resultados = analise.get("resultados", [])

    fontes = []

    for indice, resultado in enumerate(resultados, start=1):

        titulo = resultado.get("titulo", "")
        url = resultado.get("url", "")
        dominio = resultado.get("dominio", "")
        conteudo = resultado.get("conteudo", "")

        if not dominio:
            dominio = "dominio_desconhecido"

        texto_completo = f"{titulo} {conteudo}"

        termos = extrair_termos(texto_completo)

        fontes.append({
            "id": indice,
            "titulo": titulo,
            "url": url,
            "dominio": dominio,
            "termos": termos,
            "numeros": resultado.get("numeros", []),
            "conteudo_disponivel": bool(conteudo.strip())
        })

    return fontes


def identificar_termos_compartilhados(fontes):
    """
    Identifica termos presentes em diferentes domínios.

    Cada domínio conta apenas uma vez.
    Isso evita dar peso adicional a várias páginas
    do mesmo site.
    """

    termos_por_dominio = defaultdict(set)

    for fonte in fontes:
        termos_por_dominio[fonte["dominio"]].update(
            fonte["termos"]
        )

    frequencia = Counter()

    for termos in termos_por_dominio.values():
        frequencia.update(termos)

    quantidade_dominios = len(termos_por_dominio)

    compartilhados = []

    for termo, quantidade in frequencia.items():

        if quantidade >= 2:
            compartilhados.append({
                "termo": termo,
                "quantidade_dominios": quantidade,
                "proporcao_dominios": round(
                    quantidade / quantidade_dominios, 3
                ) if quantidade_dominios else 0
            })

    compartilhados.sort(
        key=lambda item: (
            item["quantidade_dominios"],
            item["termo"]
        ),
        reverse=True
    )

    return compartilhados


def comparar_pares_de_fontes(fontes):
    """Compara fontes de domínios diferentes."""

    comparacoes = []

    for fonte_a, fonte_b in combinations(fontes, 2):

        if fonte_a["dominio"] == fonte_b["dominio"]:
            continue

        similaridade = calcular_similaridade(
            fonte_a["termos"],
            fonte_b["termos"]
        )

        termos_comuns = sorted(
            fonte_a["termos"].intersection(fonte_b["termos"])
        )

        comparacoes.append({
            "fonte_a": fonte_a["titulo"],
            "dominio_a": fonte_a["dominio"],
            "fonte_b": fonte_b["titulo"],
            "dominio_b": fonte_b["dominio"],
            "similaridade_lexical": similaridade,
            "termos_compartilhados": termos_comuns
        })

    comparacoes.sort(
        key=lambda item: item["similaridade_lexical"],
        reverse=True
    )

    return comparacoes


def organizar_sinais_numericos(fontes):
    """
    Reúne números identificados pelo analisador anterior.

    Os números são apresentados como sinais que exigem
    contexto. Não são tratados como evidências de concordância
    ou contradição.
    """

    sinais = []

    for fonte in fontes:

        numeros = fonte["numeros"]

        if not numeros:
            continue

        sinais.append({
            "titulo": fonte["titulo"],
            "dominio": fonte["dominio"],
            "numeros_identificados": numeros,
            "observacao": (
                "Os números precisam ser associados ao trecho "
                "e ao contexto original."
            )
        })

    return sinais


def comparar_evidencias(analise):
    """Executa a comparação entre as fontes analisadas."""

    if not isinstance(analise, dict):
        raise ValueError("A análise recebida precisa ser um dicionário.")

    if not isinstance(analise.get("resultados"), list):
        raise ValueError(
            "A análise não contém uma lista válida de resultados."
        )

    fontes = preparar_fontes(analise)

    dominios = sorted({
        fonte["dominio"]
        for fonte in fontes
    })

    termos_compartilhados = identificar_termos_compartilhados(
        fontes
    )

    comparacoes = comparar_pares_de_fontes(fontes)

    sinais_numericos = organizar_sinais_numericos(fontes)

    observacoes = []

    if len(fontes) < 2:
        observacoes.append(
            "Não existem fontes suficientes para uma comparação."
        )

    if len(dominios) < 2:
        observacoes.append(
            "Os resultados não apresentam dois domínios distintos."
        )

    if termos_compartilhados:
        observacoes.append(
            "Foram encontrados termos presentes em mais de um domínio."
        )
        observacoes.append(
            "A repetição de termos indica proximidade temática, "
            "não confirmação factual."
        )
    else:
        observacoes.append(
            "Nenhum termo compartilhado foi identificado pelo método lexical."
        )
        observacoes.append(
            "A ausência de termos compartilhados não prova que as fontes "
            "discordam."
        )

    observacoes.append(
        "A comparação lexical não determina se uma informação é verdadeira."
    )

    observacoes.append(
        "Números identificados precisam ser examinados dentro de seus "
        "trechos originais."
    )

    return {
        "estado": "comparacao_concluida",
        "quantidade_fontes": len(fontes),
        "quantidade_dominios": len(dominios),
        "dominios": dominios,
        "termos_compartilhados": termos_compartilhados,
        "comparacoes_entre_fontes": comparacoes,
        "sinais_numericos": sinais_numericos,
        "observacoes": observacoes,
        "concordancia_factual": False,
        "contradicao_factual_confirmada": False,
        "verificacao_independente": False,
        "conhecimento_verificado": False
    }


def exibir_comparacao(comparacao):
    """Exibe o relatório da comparação."""

    print("\n" + "=" * 55)
    print("ANNIA LUCILLA - COMPARADOR DE EVIDÊNCIAS")
    print("=" * 55)

    print(
        f"\nFontes comparadas: "
        f"{comparacao['quantidade_fontes']}"
    )

    print(
        f"Domínios diferentes: "
        f"{comparacao['quantidade_dominios']}"
    )

    print("\nDOMÍNIOS ENCONTRADOS:")

    for dominio in comparacao["dominios"]:
        print(f"- {dominio}")

    print("\nTERMOS COMPARTILHADOS:")

    termos = comparacao["termos_compartilhados"]

    if termos:
        for item in termos[:20]:
            print(
                f"- {item['termo']} "
                f"({item['quantidade_dominios']} domínios)"
            )
    else:
        print("- Nenhum termo compartilhado identificado.")

    print("\nCOMPARAÇÃO ENTRE FONTES:")

    comparacoes = comparacao["comparacoes_entre_fontes"]

    if comparacoes:
        for item in comparacoes[:10]:
            print(
                f"\n{item['dominio_a']} x {item['dominio_b']}"
            )

            print(
                f"Similaridade lexical: "
                f"{item['similaridade_lexical']}"
            )

            if item["termos_compartilhados"]:
                print(
                    "Termos em comum: "
                    + ", ".join(item["termos_compartilhados"][:10])
                )
            else:
                print("Termos em comum: nenhum identificado.")
    else:
        print("- Não foi possível comparar pares de fontes.")

    print("\nSINAIS NUMÉRICOS:")

    sinais = comparacao["sinais_numericos"]

    if sinais:
        for sinal in sinais:
            print(f"\nFonte: {sinal['dominio']}")
            print(
                f"Números: {sinal['numeros_identificados']}"
            )
            print(sinal["observacao"])
    else:
        print("- Nenhum número foi identificado.")

    print("\nOBSERVAÇÕES:")

    for observacao in comparacao["observacoes"]:
        print(f"- {observacao}")

    print("\n" + "-" * 55)
    print("Comparação concluída.")
    print("Nenhuma informação foi automaticamente verificada.")
    print("=" * 55)


if __name__ == "__main__":

    from cerebro.pesquisa_web import (
        pesquisar_web,
        ErroPesquisaWeb
    )

    from cerebro.analisador_fontes import analisar_resultados

    try:
        print("Pesquisando informações para comparação...")

        pesquisa = pesquisar_web(
            "Como funciona uma geladeira?",
            quantidade=5
        )

        print("\nAnalisando fontes...")

        analise = analisar_resultados(pesquisa)

        print("\nComparando evidências...")

        comparacao = comparar_evidencias(analise)

        exibir_comparacao(comparacao)

    except ErroPesquisaWeb as erro:
        print(f"\nErro na pesquisa: {erro}")

    except (ValueError, TypeError, KeyError) as erro:
        print(f"\nErro na comparação: {erro}")