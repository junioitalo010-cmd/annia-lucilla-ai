
import re
import unicodedata
from collections import Counter
from urllib.parse import urlparse
from datetime import datetime


PALAVRAS_IGNORADAS = {
    "para", "com", "uma", "uns", "umas", "que", "como",
    "dos", "das", "por", "pelo", "pela", "nos", "nas",
    "isso", "essa", "esse", "este", "esta", "sua", "seu",
    "sobre", "entre", "quando", "onde", "qual", "quais",
    "ser", "ter", "foi", "sao", "são", "tem", "mais",
    "muito", "tambem", "também", "depois", "antes"
}

TERMOS_DESATUALIZACAO = {
    "obsoleto",
    "descontinuado",
    "antigo",
    "antiga",
    "substituido",
    "substituida",
    "proibido",
    "proibida",
    "descontinuada"
}


def normalizar(texto):
    """Remove acentos e padroniza o texto."""

    texto = str(texto or "").lower()

    texto = unicodedata.normalize(
        "NFD",
        texto
    )

    texto = "".join(
        caractere
        for caractere in texto
        if unicodedata.category(caractere) != "Mn"
    )

    return texto


def extrair_termos(texto):
    """Extrai palavras relevantes para comparação."""

    texto = normalizar(texto)

    termos = re.findall(r"\b[a-z0-9]+\b", texto)

    return {
        termo
        for termo in termos
        if len(termo) > 2
        and termo not in PALAVRAS_IGNORADAS
    }


def extrair_numeros(texto):
    """Identifica números, anos e valores presentes no conteúdo."""

    return re.findall(
        r"\b\d+(?:[.,]\d+)?\b",
        str(texto or "")
    )


def identificar_dominio(url):
    """Extrai o domínio de uma URL."""

    try:
        dominio = urlparse(url).netloc.lower()

        if dominio.startswith("www."):
            dominio = dominio[4:]

        return dominio or None

    except Exception:
        return None


def similaridade_textual(texto_a, texto_b):
    """Calcula similaridade lexical entre dois textos."""

    termos_a = extrair_termos(texto_a)
    termos_b = extrair_termos(texto_b)

    if not termos_a or not termos_b:
        return 0.0

    intersecao = termos_a.intersection(termos_b)
    uniao = termos_a.union(termos_b)

    return round(len(intersecao) / len(uniao), 3)


def identificar_repeticoes(resultados):
    """Identifica URLs e conteúdos muito semelhantes."""

    urls = []
    pares_semelhantes = []

    for resultado in resultados:
        url = resultado.get("url", "").strip()

        if url:
            urls.append(url.rstrip("/").lower())

    contagem_urls = Counter(urls)

    urls_repetidas = [
        url
        for url, quantidade in contagem_urls.items()
        if quantidade > 1
    ]

    for i in range(len(resultados)):
        for j in range(i + 1, len(resultados)):

            texto_a = (
                resultados[i].get("titulo", "")
                + " "
                + resultados[i].get("conteudo", "")
            )

            texto_b = (
                resultados[j].get("titulo", "")
                + " "
                + resultados[j].get("conteudo", "")
            )

            semelhanca = similaridade_textual(
                texto_a,
                texto_b
            )

            if semelhanca >= 0.65:
                pares_semelhantes.append({
                    "resultado_1": i + 1,
                    "resultado_2": j + 1,
                    "similaridade": semelhanca,
                    "observacao": (
                        "Conteúdos lexicalmente semelhantes. "
                        "Verificar se são independentes."
                    )
                })

    return {
        "urls_repetidas": urls_repetidas,
        "conteudos_semelhantes": pares_semelhantes
    }


def analisar_atualidade(resultados):
    """Identifica sinais textuais de possível desatualização."""

    analises = []

    for indice, resultado in enumerate(resultados, start=1):

        texto = normalizar(
            resultado.get("titulo", "")
            + " "
            + resultado.get("conteudo", "")
        )

        sinais = []

        for termo in TERMOS_DESATUALIZACAO:
            if termo in texto:
                sinais.append(
                    f"Termo relacionado a desatualização: {termo}"
                )

        data_publicacao = resultado.get("data_publicacao")

        ano = None

        if data_publicacao:
            correspondencia = re.search(
                r"\b(19\d{2}|20\d{2})\b",
                str(data_publicacao)
            )

            if correspondencia:
                ano = int(correspondencia.group(1))

        if ano and ano < datetime.now().year - 5:
            sinais.append(
                f"Publicação antiga identificada: {ano}"
            )

        analises.append({
            "resultado": indice,
            "data_publicacao": data_publicacao,
            "sinais": sinais,
            "necessita_revisao": bool(sinais)
        })

    return analises


def analisar_numeros(resultados):
    """
    Organiza os números encontrados em cada resultado.

    Números diferentes não são tratados automaticamente
    como contradições.
    """

    analises = []

    for indice, resultado in enumerate(resultados, start=1):

        texto = (
            resultado.get("titulo", "")
            + " "
            + resultado.get("conteudo", "")
        )

        numeros = extrair_numeros(texto)

        analises.append({
            "resultado": indice,
            "numeros_encontrados": list(dict.fromkeys(numeros))
        })

    return analises


def analisar_resultados(pesquisa):
    """
    Analisa os resultados retornados pela pesquisa web.

    Não verifica a verdade das informações e não registra
    automaticamente conhecimentos na memória da Luci.
    """

    resultados = pesquisa.get("resultados", [])

    if not isinstance(resultados, list):
        raise ValueError(
            "O campo resultados precisa ser uma lista."
        )

    resultados_validos = []

    for item in resultados:

        if not isinstance(item, dict):
            continue

        titulo = str(item.get("titulo", "")).strip()
        url = str(item.get("url", "")).strip()
        conteudo = str(item.get("conteudo", "")).strip()

        if not titulo and not url and not conteudo:
            continue

        resultados_validos.append({
            "titulo": titulo,
            "url": url,
            "conteudo": conteudo,
            "pontuacao": item.get("pontuacao"),
            "data_publicacao": item.get("data_publicacao"),
            "dominio": identificar_dominio(url)
        })

    dominios = sorted({
        resultado["dominio"]
        for resultado in resultados_validos
        if resultado["dominio"]
    })

    resultados_vazios = [
        indice
        for indice, resultado in enumerate(
            resultados_validos,
            start=1
        )
        if not resultado["conteudo"]
    ]

    repeticoes = identificar_repeticoes(
        resultados_validos
    )

    atualidade = analisar_atualidade(
        resultados_validos
    )

    numeros = analisar_numeros(
        resultados_validos
    )

    return {
        "consulta": pesquisa.get("consulta", ""),
        "fonte_pesquisa": pesquisa.get("fonte", "desconhecida"),
        "quantidade_resultados_recebidos": len(resultados),
        "quantidade_resultados_analisados": len(
            resultados_validos
        ),
        "quantidade_dominios": len(dominios),
        "dominios": dominios,
        "resultados": resultados_validos,
        "repeticoes": repeticoes,
        "atualidade": atualidade,
        "numeros": numeros,
        "resultados_sem_conteudo": resultados_vazios,
        "estado": "analise_concluida",
        "verificacao_independente": False,
        "conhecimento_verificado": False
    }


def exibir_analise(analise):
    """Exibe o relatório de análise das fontes."""

    print("\n========== ANALISE DE FONTES DA LUCI ==========")

    print("Consulta:", analise["consulta"])

    print(
        "Resultados recebidos:",
        analise["quantidade_resultados_recebidos"]
    )

    print(
        "Resultados analisados:",
        analise["quantidade_resultados_analisados"]
    )

    print(
        "Domínios diferentes:",
        analise["quantidade_dominios"]
    )

    print("\nDOMINIOS IDENTIFICADOS:")

    for dominio in analise["dominios"]:
        print("-", dominio)

    print("\nREPETICOES:")
    print(analise["repeticoes"])

    print("\nATUALIDADE:")

    for item in analise["atualidade"]:
        print(item)

    print("\nNUMEROS ENCONTRADOS:")

    for item in analise["numeros"]:
        print(item)

    print("\nRESULTADOS SEM CONTEUDO:")
    print(analise["resultados_sem_conteudo"])

    print("\nESTADO:", analise["estado"])
    print("Verificação independente: não realizada.")
    print("Conhecimento verificado: não.")
    print("===============================================")


if __name__ == "__main__":

    from cerebro.pesquisa_web import (
        pesquisar_web,
        ErroPesquisaWeb
    )

    try:
        pesquisa = pesquisar_web(
            "Como funciona uma geladeira?",
            quantidade=5
        )

        analise = analisar_resultados(pesquisa)

        exibir_analise(analise)

    except (ErroPesquisaWeb, ValueError) as erro:
        print("\nERRO:", erro)
