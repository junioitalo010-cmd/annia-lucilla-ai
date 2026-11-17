
import json
import os
import urllib.error
import urllib.request


URL_API = "https://api.tavily.com/search"


class ErroPesquisaWeb(Exception):
    """Erro durante a comunicação com a API de pesquisa."""


def pesquisar_web(consulta, quantidade=5):
    """
    Pesquisa na internet utilizando a API da Tavily.

    Retorna resultados organizados, sem registrá-los
    automaticamente como conhecimentos verificados.
    """

    chave_api = os.getenv("TAVILY_API_KEY")

    if not chave_api:
        raise ErroPesquisaWeb(
            "Chave da Tavily não encontrada. "
            "Configure TAVILY_API_KEY no ambiente."
        )

    if not isinstance(consulta, str) or not consulta.strip():
        raise ValueError("A consulta não pode estar vazia.")

    quantidade = max(1, min(int(quantidade), 10))

    dados = {
        "query": consulta.strip(),
        "topic": "general",
        "search_depth": "basic",
        "max_results": quantidade,
        "include_answer": False
    }

    corpo = json.dumps(dados).encode("utf-8")

    requisicao = urllib.request.Request(
        URL_API,
        data=corpo,
        headers={
            "Authorization": f"Bearer {chave_api}",
            "Content-Type": "application/json"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(
            requisicao,
            timeout=30
        ) as resposta:

            conteudo = resposta.read().decode("utf-8")
            resultado_api = json.loads(conteudo)

    except urllib.error.HTTPError as erro:
        detalhes = erro.read().decode(
            "utf-8",
            errors="replace"
        )

        raise ErroPesquisaWeb(
            f"Erro HTTP {erro.code} na Tavily: {detalhes[:500]}"
        ) from erro

    except urllib.error.URLError as erro:
        raise ErroPesquisaWeb(
            f"Não foi possível conectar à Tavily: {erro.reason}"
        ) from erro

    except TimeoutError as erro:
        raise ErroPesquisaWeb(
            "A pesquisa excedeu o tempo limite."
        ) from erro

    except json.JSONDecodeError as erro:
        raise ErroPesquisaWeb(
            "A API retornou uma resposta inválida."
        ) from erro

    resultados = []

    for item in resultado_api.get("results", []):
        resultados.append({
            "titulo": item.get("title", ""),
            "url": item.get("url", ""),
            "conteudo": item.get("content", ""),
            "pontuacao": item.get("score"),
            "data_publicacao": item.get("published_date")
        })

    return {
        "consulta": consulta.strip(),
        "quantidade_resultados": len(resultados),
        "resultados": resultados,
        "fonte": "Tavily",
        "estado": "pesquisa_realizada",
        "verificacao_independente": False
    }


def exibir_resultados(pesquisa):
    """Exibe os resultados de uma pesquisa."""

    print("\n========== PESQUISA DA LUCI ==========")
    print("Consulta:", pesquisa["consulta"])
    print("Resultados:", pesquisa["quantidade_resultados"])

    for indice, resultado in enumerate(
        pesquisa["resultados"], start=1
    ):
        print(f"\n--- Resultado {indice} ---")
        print("Título:", resultado["titulo"])
        print("URL:", resultado["url"])
        print("Conteúdo:", resultado["conteudo"])
        print("Pontuação:", resultado["pontuacao"])

    print("\nFonte:", pesquisa["fonte"])
    print("Estado:", pesquisa["estado"])
    print("Pesquisa não equivale a verificação.")
    print("======================================")


if __name__ == "__main__":
    try:
        pesquisa = pesquisar_web(
            "Como funciona uma geladeira?",
            quantidade=5
        )

        exibir_resultados(pesquisa)

    except (ErroPesquisaWeb, ValueError) as erro:
        print("\nERRO NA PESQUISA:")
        print(erro)
