import re
import unicodedata
from urllib.parse import urlparse
from itertools import combinations

from cerebro.conhecimento import buscar_conhecimentos_verificados


# ============================================================
# LIMITES DE SEGURANCA
# ============================================================

LIMITE_AFIRMACOES_POR_CONTEUDO = 100
TAMANHO_MINIMO_AFIRMACAO = 20


# ============================================================
# NORMALIZACAO
# ============================================================

def normalizar(texto):
    if not isinstance(texto, str):
        return ""

    texto = texto.lower().strip()
    texto = unicodedata.normalize("NFKD", texto)

    texto = "".join(
        caractere
        for caractere in texto
        if not unicodedata.combining(caractere)
    )

    texto = re.sub(r"[^\w\s.-]", " ", texto)
    texto = re.sub(r"\s+", " ", texto)

    return texto.strip()


def extrair_termos(texto):
    texto = normalizar(texto)

    palavras_vazias = {
        "a", "o", "as", "os", "um", "uma", "uns", "umas",
        "de", "da", "do", "das", "dos", "em", "no", "na",
        "nos", "nas", "por", "para", "com", "sem", "que",
        "e", "ou", "ao", "aos", "se", "sua", "seu",
        "suas", "seus", "foi", "ser", "sao", "era",
        "como", "mais", "menos", "tambem", "sobre",
        "este", "esta"
    }

    return {
        palavra
        for palavra in texto.split()
        if len(palavra) > 2 and palavra not in palavras_vazias
    }


def extrair_numeros(texto):
    """
    Extrai números usados em afirmações, ignorando
    números que fazem parte de versões de software.
    """

    if not isinstance(texto, str):
        return []

    texto_sem_versoes = re.sub(
        r"\bpython\s*\d+(?:\.\d+)+\b",
        " ",
        texto,
        flags=re.IGNORECASE
    )

    texto_sem_versoes = re.sub(
        r"\b(?:vers[aã]o|version)\s*\d+(?:\.\d+)+\b",
        " ",
        texto_sem_versoes,
        flags=re.IGNORECASE
    )

    return re.findall(
        r"\b\d+(?:[.,]\d+)?\b",
        texto_sem_versoes
    )


def extrair_dominio(url):
    if not isinstance(url, str) or not url.strip():
        return ""

    try:
        dominio = urlparse(url).netloc.lower()
        return dominio.removeprefix("www.")
    except Exception:
        return ""


def dominio_raiz_simples(dominio):
    if not dominio:
        return ""

    partes = dominio.split(".")

    if len(partes) >= 2:
        return ".".join(partes[-2:])

    return dominio


def similaridade_jaccard(texto_a, texto_b):
    termos_a = extrair_termos(texto_a)
    termos_b = extrair_termos(texto_b)

    if not termos_a or not termos_b:
        return 0.0

    intersecao = termos_a.intersection(termos_b)
    uniao = termos_a.union(termos_b)

    return len(intersecao) / len(uniao)


# ============================================================
# EXTRAÇÃO DE AFIRMAÇÕES
# ============================================================

def extrair_afirmacoes(texto):
    """
    Divide o conteúdo em frases aproximadas.

    Não realiza compreensão semântica.
    Limita a quantidade de frases para evitar
    comparações excessivamente grandes.
    """

    if not isinstance(texto, str):
        return []

    partes = re.split(r"(?<=[.!?])\s+|\n+", texto)

    afirmacoes = []

    for parte in partes:
        parte = parte.strip()

        if len(parte) < TAMANHO_MINIMO_AFIRMACAO:
            continue

        afirmacoes.append(parte)

        if len(afirmacoes) >= LIMITE_AFIRMACOES_POR_CONTEUDO:
            break

    return afirmacoes


# ============================================================
# IDENTIFICACAO DE ENTIDADES E CONTEXTO
# ============================================================

def extrair_versao(texto):
    """
    Identifica versões numéricas, como:
    Python 0.9.0
    Python 3.0
    Versão 2.1.5
    """

    if not isinstance(texto, str):
        return None

    padroes = [
        r"\bpython\s*(\d+(?:\.\d+)+)\b",
        r"\bvers[aã]o\s*(\d+(?:\.\d+)+)\b",
        r"\bversion\s*(\d+(?:\.\d+)+)\b"
    ]

    for padrao in padroes:
        resultado = re.search(
            padrao,
            texto,
            flags=re.IGNORECASE
        )

        if resultado:
            return resultado.group(1)

    return None


def extrair_entidade(texto, assunto=""):
    """
    Identifica a entidade principal.

    Uma referencia inicial explicita ao Python com versao tem
    prioridade sobre o titulo editorial. Nos demais casos, usa o assunto.

    A versão continua disponível separadamente no contexto.
    """

    # Uma referencia explicita ao software e mais especifica que
    # o titulo editorial da pagina. Versoes continuam comparadas
    # separadamente por comparar_afirmacoes.
    if isinstance(texto, str) and re.match(
        r"\s*python\s*\d+(?:\.\d+)+\b", texto, flags=re.IGNORECASE
    ):
        return "software:python"

    assunto_normalizado = normalizar(assunto)

    if assunto_normalizado:
        return f"assunto:{assunto_normalizado}"

    versao = extrair_versao(texto)

    if versao:
        return f"versao:{versao}"

    return "entidade:indeterminada"


def extrair_relacao(texto):
    """
    Identifica a relação pela primeira ocorrência
    encontrada no texto.

    A classificação é baseada em palavras-chave
    e não representa compreensão semântica completa.
    """

    texto = normalizar(texto)

    relacoes = {
        "lancamento": [
            "lancado", "lancada", "lancamento",
            "publicado", "publicada", "publica",
            "disponibilizado", "disponibilizada",
            "release", "released"
        ],

        "criacao": [
            "criado", "criada", "criou",
            "desenvolvido", "desenvolvida",
            "desenvolveu"
        ],

        "fundacao": [
            "fundado", "fundada", "fundacao",
            "fundou"
        ],

        "autoria": [
            "autor", "autora", "escrito",
            "escrita", "escreveu"
        ],

        "localizacao": [
            "localizado", "localizada",
            "situado", "situada",
            "fica em", "sediado"
        ],

        "preco": [
            "preco", "custa", "custava",
            "valor", "cobrado"
        ],

        "quantidade": [
            "quantidade", "total", "numero de",
            "possui", "conta com"
        ]
    }

    ocorrencias = []

    for relacao, palavras in relacoes.items():
        for palavra in palavras:
            posicao = texto.find(palavra)

            if posicao >= 0:
                ocorrencias.append((posicao, relacao))

    if not ocorrencias:
        return "indeterminada"

    ocorrencias.sort(key=lambda item: item[0])

    return ocorrencias[0][1]


def extrair_responsavel(texto):
    """
    Identifica a pessoa ou entidade apresentada
    como responsável por uma ação.

    Remove informações adicionais de localização,
    período e contexto após o nome identificado.
    """

    if not isinstance(texto, str):
        return None

    texto_normalizado = normalizar(texto)

    padroes = [
        r"\b(?:criado|criada|desenvolvido|desenvolvida)\s+por\s+([a-z][a-z\s.-]{2,60})",
        r"\b(?:criou|desenvolveu|fundou)\s+([a-z][a-z\s.-]{2,60})",
        r"\b(?:fundado|fundada)\s+por\s+([a-z][a-z\s.-]{2,60})",
        r"\b(?:escrito|escrita)\s+por\s+([a-z][a-z\s.-]{2,60})"
    ]

    marcadores_contexto = [
        " no ",
        " na ",
        " nos ",
        " nas ",
        " em ",
        " durante ",
        " quando ",
        " porque "
    ]

    for padrao in padroes:
        resultado = re.search(
            padrao,
            texto_normalizado
        )

        if not resultado:
            continue

        responsavel = resultado.group(1).strip()

        for marcador in marcadores_contexto:
            posicao = responsavel.find(marcador)

            if posicao >= 0:
                responsavel = responsavel[:posicao]

        responsavel = responsavel.rstrip(" .,;:!?").strip()

        if responsavel:
            return responsavel

    return None


def extrair_contexto_afirmacao(texto, assunto=""):
    """
    Extrai uma representação contextual simplificada.

    Inclui:
    - entidade;
    - relação;
    - responsável;
    - números;
    - ano;
    - versão.

    Não confirma a veracidade da informação.
    """

    texto_normalizado = normalizar(texto)

    entidade = extrair_entidade(texto, assunto)
    relacao = extrair_relacao(texto)
    responsavel = extrair_responsavel(texto)

    numeros = extrair_numeros(texto)
    versao = extrair_versao(texto)

    anos = re.findall(
        r"\b(?:19|20)\d{2}\b",
        texto_normalizado
    )

    return {
        "entidade": entidade,
        "relacao": relacao,
        "responsavel": responsavel,
        "numeros": numeros,
        "anos": anos,
        "versao": versao,
        "contexto_identificavel": (
            entidade != "entidade:indeterminada"
            and relacao != "indeterminada"
        )
    }


def comparar_contextos(contexto_a, contexto_b):
    """
    Verifica se duas afirmações parecem tratar
    da mesma entidade e da mesma característica.
    """

    entidade_a = contexto_a.get("entidade")
    entidade_b = contexto_b.get("entidade")

    relacao_a = contexto_a.get("relacao")
    relacao_b = contexto_b.get("relacao")

    mesma_entidade = (
        entidade_a == entidade_b
        and entidade_a != "entidade:indeterminada"
    )

    mesma_relacao = (
        relacao_a == relacao_b
        and relacao_a != "indeterminada"
    )

    contexto_comparavel = mesma_entidade and mesma_relacao

    motivos = []

    if not mesma_entidade:
        motivos.append("entidades_diferentes_ou_indeterminadas")

    if not mesma_relacao:
        motivos.append("relacoes_diferentes_ou_indeterminadas")

    return {
        "mesma_entidade": mesma_entidade,
        "mesma_relacao": mesma_relacao,
        "contexto_comparavel": contexto_comparavel,
        "motivos": motivos
    }


# ============================================================
# AVALIACAO INDIVIDUAL DOS CANDIDATOS
# ============================================================

def avaliar_conteudo(candidato):
    if not isinstance(candidato, dict):
        return {
            "estado": "candidato_invalido",
            "problemas": ["O candidato não é um dicionário."],
            "quantidade_afirmacoes": 0,
            "afirmacoes": []
        }

    assunto = candidato.get("assunto", "")
    fonte = candidato.get("fonte", "")
    conteudo = candidato.get("conteudo_original", "")

    problemas = []
    alertas = []

    if not isinstance(assunto, str) or not assunto.strip():
        problemas.append("Assunto ausente.")

    if not isinstance(fonte, str) or not fonte.strip():
        problemas.append("Fonte ausente.")

    if not isinstance(conteudo, str) or not conteudo.strip():
        problemas.append("Conteúdo ausente.")

    if (
        isinstance(fonte, str)
        and fonte
        and not fonte.startswith(("http://", "https://"))
    ):
        alertas.append("A fonte não parece ser uma URL.")

    if isinstance(conteudo, str) and len(conteudo.strip()) < 80:
        alertas.append("Conteúdo muito curto para avaliação.")

    afirmacoes = extrair_afirmacoes(conteudo)
    dominio = extrair_dominio(fonte)

    if not dominio:
        alertas.append("Não foi possível identificar o domínio.")

    estado = (
        "candidato_invalido"
        if problemas
        else "aguardando_verificacao"
    )

    return {
        "estado": estado,
        "assunto": assunto,
        "fonte": fonte,
        "dominio": dominio,
        "problemas": problemas,
        "alertas": alertas,
        "quantidade_afirmacoes": len(afirmacoes),
        "afirmacoes": afirmacoes
    }


# ============================================================
# FILTRO DA MEMORIA VERIFICADA
# ============================================================

def filtrar_conhecimentos_verificados(conhecimentos):
    if not isinstance(conhecimentos, list):
        return []

    confiaveis = []

    for conhecimento in conhecimentos:
        if not isinstance(conhecimento, dict):
            continue

        if conhecimento.get("estado_verificacao") == "verificado":
            confiaveis.append(conhecimento)

    return confiaveis


def carregar_memoria_verificada(consulta):
    try:
        conhecimentos = buscar_conhecimentos_verificados(consulta)

    except Exception as erro:
        return {
            "estado": "erro",
            "conhecimentos": [],
            "erro": str(erro)
        }

    conhecimentos = filtrar_conhecimentos_verificados(
        conhecimentos
    )

    return {
        "estado": "concluido",
        "quantidade": len(conhecimentos),
        "conhecimentos": conhecimentos
    }


# ============================================================
# NEGACAO
# ============================================================

def possui_negacao(texto):
    termos_negacao = {
        "nao", "nunca", "jamais", "nenhum",
        "nenhuma", "inexistente", "impossivel"
    }

    termos = extrair_termos(texto)

    return bool(termos.intersection(termos_negacao))


# ============================================================
# COMPARACAO CONTEXTUAL DE AFIRMACOES
# ============================================================

def comparar_afirmacoes(
    afirmacao_a,
    afirmacao_b,
    assunto_a="",
    assunto_b=""
):
    """
    Compara afirmações considerando:
    - similaridade lexical;
    - entidade;
    - relação;
    - responsável;
    - números;
    - negação;
    - versão do objeto.

    Quando o segundo texto contém várias frases,
    procura a frase mais adequada para comparação.

    O resultado não confirma uma contradição.
    """

    def comparar_unico(texto_a, texto_b):
        similaridade = similaridade_jaccard(
            texto_a,
            texto_b
        )

        contexto_a = extrair_contexto_afirmacao(
            texto_a,
            assunto_a
        )

        contexto_b = extrair_contexto_afirmacao(
            texto_b,
            assunto_b
        )

        comparacao_contexto = comparar_contextos(
            contexto_a,
            contexto_b
        )

        sinais = []

        numeros_a = contexto_a["numeros"]
        numeros_b = contexto_b["numeros"]

        anos_a = contexto_a["anos"]
        anos_b = contexto_b["anos"]

        versao_a = contexto_a["versao"]
        versao_b = contexto_b["versao"]

        responsavel_a = contexto_a["responsavel"]
        responsavel_b = contexto_b["responsavel"]

        negacao_a = possui_negacao(texto_a)
        negacao_b = possui_negacao(texto_b)

        mesma_entidade = comparacao_contexto["mesma_entidade"]
        mesma_relacao = comparacao_contexto["mesma_relacao"]

        mesmas_versoes = versao_a == versao_b

        if mesma_entidade and mesma_relacao:

            # Quando ambas as afirmações contêm anos,
            # compara os anos e ignora dias e meses.
            if mesmas_versoes:

                if anos_a and anos_b:
                    valores_diferentes = anos_a != anos_b

                else:
                    valores_diferentes = (
                        bool(numeros_a)
                        and bool(numeros_b)
                        and numeros_a != numeros_b
                    )

                if valores_diferentes:
                    sinais.append("valores_numericos_diferentes")

            if negacao_a != negacao_b:
                sinais.append("possivel_diferenca_de_negacao")

            if (
                responsavel_a
                and responsavel_b
                and responsavel_a != responsavel_b
            ):
                sinais.append("responsaveis_diferentes")

        if sinais and comparacao_contexto["contexto_comparavel"]:
            estado = "possivel_divergencia"

        elif not comparacao_contexto["contexto_comparavel"]:
            estado = "contexto_insuficiente_ou_diferente"

        elif similaridade < 0.20:
            estado = "sem_relacao_lexical_suficiente"

        else:
            estado = "proximidade_tematica"

        return {
            "estado": estado,
            "similaridade": round(similaridade, 4),
            "sinais": sinais,
            "contexto_a": contexto_a,
            "contexto_b": contexto_b,
            "comparacao_contexto": comparacao_contexto,
            "verificacao_semantica": False,
            "contradicao_confirmada": False
        }

    # Separa o segundo texto em frases.
    frases = re.split(
        r"(?<=[.!?])\s+",
        afirmacao_b.strip()
    )

    frases = [
        frase.strip()
        for frase in frases
        if frase.strip()
    ]

    # Texto com apenas uma frase: comparação normal.
    if len(frases) <= 1:
        return comparar_unico(
            afirmacao_a,
            afirmacao_b
        )

    # Compara a afirmação com cada frase individualmente.
    resultados = [
        comparar_unico(afirmacao_a, frase)
        for frase in frases
    ]

    # Prioriza correspondência de entidade e relação.
    resultados_compativeis = [
        resultado
        for resultado in resultados
        if resultado["comparacao_contexto"]["contexto_comparavel"]
    ]

    if resultados_compativeis:
        melhor_resultado = max(
            resultados_compativeis,
            key=lambda resultado: resultado["similaridade"]
        )

        return melhor_resultado

    # Sem correspondência contextual, preserva
    # a comparação com o texto completo.
    return comparar_unico(
        afirmacao_a,
        afirmacao_b
    )


# ============================================================
# COMPARACAO COM A MEMORIA LOCAL
# ============================================================

def comparar_com_base_local(candidato, conhecimentos):
    if not isinstance(candidato, dict):
        return []

    conhecimentos = filtrar_conhecimentos_verificados(
        conhecimentos
    )

    comparacoes = []

    conteudo = candidato.get("conteudo_original", "")
    assunto_candidato = candidato.get("assunto", "")

    afirmacoes_candidato = extrair_afirmacoes(conteudo)

    for conhecimento in conhecimentos:

        assunto_memoria = conhecimento.get("assunto", "")
        conteudo_memoria = conhecimento.get("conteudo", "")

        afirmacoes_memoria = extrair_afirmacoes(
            conteudo_memoria
        )

        for afirmacao_pesquisada in afirmacoes_candidato:

            for afirmacao_memoria in afirmacoes_memoria:

                comparacao = comparar_afirmacoes(
                    afirmacao_pesquisada,
                    afirmacao_memoria,
                    assunto_candidato,
                    assunto_memoria
                )

                if comparacao["estado"] == "sem_relacao_lexical_suficiente":
                    continue

                comparacoes.append({
                    "assunto_existente": assunto_memoria,
                    "afirmacao_pesquisada": afirmacao_pesquisada,
                    "afirmacao_memoria": afirmacao_memoria,
                    "estado_memoria": "verificado",
                    "comparacao": comparacao
                })

    return comparacoes


# ============================================================
# IDENTIFICACAO DE REPETICOES
# ============================================================

def identificar_repeticoes(candidatos):
    repeticoes = []

    for candidato_a, candidato_b in combinations(candidatos, 2):

        fonte_a = candidato_a.get("fonte", "")
        fonte_b = candidato_b.get("fonte", "")

        conteudo_a = candidato_a.get("conteudo_original", "")
        conteudo_b = candidato_b.get("conteudo_original", "")

        mesma_url = (
            isinstance(fonte_a, str)
            and isinstance(fonte_b, str)
            and fonte_a.rstrip("/") == fonte_b.rstrip("/")
            and bool(fonte_a)
        )

        similaridade = similaridade_jaccard(
            conteudo_a,
            conteudo_b
        )

        if mesma_url or similaridade >= 0.45:
            repeticoes.append({
                "candidato_a": candidato_a.get("id_candidato"),
                "candidato_b": candidato_b.get("id_candidato"),
                "mesma_url": mesma_url,
                "similaridade": round(similaridade, 4)
            })

    return repeticoes


# ============================================================
# COMPARACAO ENTRE FONTES EXTERNAS
# ============================================================

def comparar_candidatos(candidatos, avaliacoes):
    comparacoes = []

    pares = zip(candidatos, avaliacoes)

    candidatos_validos = [
        (candidato, avaliacao)
        for candidato, avaliacao in pares
        if (
            isinstance(candidato, dict)
            and isinstance(avaliacao, dict)
            and avaliacao.get("estado") != "candidato_invalido"
        )
    ]

    for (candidato_a, avaliacao_a), (
        candidato_b,
        avaliacao_b
    ) in combinations(candidatos_validos, 2):

        dominio_a = dominio_raiz_simples(
            avaliacao_a.get("dominio", "")
        )

        dominio_b = dominio_raiz_simples(
            avaliacao_b.get("dominio", "")
        )

        if not dominio_a or not dominio_b or dominio_a == dominio_b:
            continue

        afirmacoes_a = avaliacao_a.get("afirmacoes", [])
        afirmacoes_b = avaliacao_b.get("afirmacoes", [])

        for afirmacao_a in afirmacoes_a:

            for afirmacao_b in afirmacoes_b:

                resultado = comparar_afirmacoes(
                    afirmacao_a,
                    afirmacao_b,
                    candidato_a.get("assunto", ""),
                    candidato_b.get("assunto", "")
                )

                if resultado["estado"] == "sem_relacao_lexical_suficiente":
                    continue

                comparacoes.append({
                    "candidato_a": candidato_a.get("id_candidato"),
                    "candidato_b": candidato_b.get("id_candidato"),
                    "dominio_a": dominio_a,
                    "dominio_b": dominio_b,
                    "afirmacao_a": afirmacao_a,
                    "afirmacao_b": afirmacao_b,
                    "comparacao": resultado
                })

    return comparacoes


# ============================================================
# AVALIACAO COMPLETA
# ============================================================

def avaliar_candidatos(selecao, conhecimentos=None):

    if not isinstance(selecao, dict):
        selecao = {}

    candidatos = selecao.get("candidatos", [])

    if not isinstance(candidatos, list):
        candidatos = []

    conhecimentos = filtrar_conhecimentos_verificados(
        conhecimentos or []
    )

    resultados = []
    candidatos_validos = []
    avaliacoes_validas = []

    quantidade_por_estado = {}

    for candidato in candidatos:

        avaliacao = avaliar_conteudo(candidato)

        estado = avaliacao.get("estado", "desconhecido")

        quantidade_por_estado[estado] = (
            quantidade_por_estado.get(estado, 0) + 1
        )

        resultado = {
            "candidato": candidato,
            "avaliacao": avaliacao,
            "comparacoes_com_base_local": []
        }

        if estado != "candidato_invalido":

            candidatos_validos.append(candidato)
            avaliacoes_validas.append(avaliacao)

            resultado["comparacoes_com_base_local"] = (
                comparar_com_base_local(
                    candidato,
                    conhecimentos
                )
            )

        resultados.append(resultado)

    comparacoes_afirmacoes = comparar_candidatos(
        candidatos_validos,
        avaliacoes_validas
    )

    possiveis_repeticoes = identificar_repeticoes(
        candidatos_validos
    )

    divergencias_entre_fontes = sum(
        1
        for item in comparacoes_afirmacoes
        if item.get("comparacao", {}).get("estado")
        == "possivel_divergencia"
    )

    divergencias_com_memoria = sum(
        1
        for resultado in resultados
        for comparacao in resultado.get(
            "comparacoes_com_base_local", []
        )
        if comparacao.get("comparacao", {}).get("estado")
        == "possivel_divergencia"
    )

    quantidade_divergencias = (
        divergencias_entre_fontes
        + divergencias_com_memoria
    )

    quantidade_comparacoes_memoria = sum(
        len(resultado.get("comparacoes_com_base_local", []))
        for resultado in resultados
    )

    quantidade_contextos_diferentes = sum(
        1
        for resultado in resultados
        for comparacao in resultado.get(
            "comparacoes_com_base_local", []
        )
        if comparacao.get("comparacao", {}).get("estado")
        == "contexto_insuficiente_ou_diferente"
    )

    return {
        "estado": "avaliacao_concluida",

        "quantidade_candidatos": len(candidatos),

        "quantidade_candidatos_validos": len(candidatos_validos),

        "quantidade_conhecimentos_verificados_utilizados": len(
            conhecimentos
        ),

        "quantidade_por_estado": quantidade_por_estado,

        "resultados": resultados,

        "possiveis_repeticoes": possiveis_repeticoes,

        "comparacoes_de_afirmacoes": comparacoes_afirmacoes,

        "quantidade_comparacoes_com_memoria": (
            quantidade_comparacoes_memoria
        ),

        "divergencias_entre_fontes": divergencias_entre_fontes,

        "divergencias_com_memoria": divergencias_com_memoria,

        "quantidade_contextos_diferentes": (
            quantidade_contextos_diferentes
        ),

        "quantidade_possiveis_divergencias": quantidade_divergencias,

        "conhecimento_aprovado": False,

        "conhecimento_salvo": False,

        "conhecimento_verificado": False,

        "verificacao_independente": False
    }


# ============================================================
# EXIBICAO DO RELATORIO
# ============================================================

def exibir_avaliacao(relatorio):

    if not isinstance(relatorio, dict):
        print("Relatório inválido.")
        return

    print("\n" + "=" * 60)
    print("RELATÓRIO DE AVALIAÇÃO DE CONHECIMENTOS")
    print("=" * 60)

    print(f"Estado: {relatorio.get('estado', 'desconhecido')}")

    print(
        "Candidatos avaliados: "
        f"{relatorio.get('quantidade_candidatos', 0)}"
    )

    print(
        "Candidatos válidos: "
        f"{relatorio.get('quantidade_candidatos_validos', 0)}"
    )

    print(
        "Conhecimentos verificados utilizados: "
        f"{relatorio.get('quantidade_conhecimentos_verificados_utilizados', 0)}"
    )

    print("\nESTADOS DOS CANDIDATOS")

    for estado, quantidade in relatorio.get(
        "quantidade_por_estado", {}
    ).items():

        print(f"- {estado}: {quantidade}")

    print("\nCOMPARAÇÕES")

    print(
        "Comparações com a memória: "
        f"{relatorio.get('quantidade_comparacoes_com_memoria', 0)}"
    )

    print(
        "Divergências entre fontes: "
        f"{relatorio.get('divergencias_entre_fontes', 0)}"
    )

    print(
        "Divergências com a memória: "
        f"{relatorio.get('divergencias_com_memoria', 0)}"
    )

    print(
        "Contextos diferentes ou insuficientes: "
        f"{relatorio.get('quantidade_contextos_diferentes', 0)}"
    )

    print(
        "Total de possíveis divergências: "
        f"{relatorio.get('quantidade_possiveis_divergencias', 0)}"
    )

    print(
        "Possíveis repetições: "
        f"{len(relatorio.get('possiveis_repeticoes', []))}"
    )

    print("\nSEGURANÇA DA MEMÓRIA")

    print(
        "Conhecimento aprovado: "
        f"{'Sim' if relatorio.get('conhecimento_aprovado') else 'Não'}"
    )

    print(
        "Conhecimento salvo: "
        f"{'Sim' if relatorio.get('conhecimento_salvo') else 'Não'}"
    )

    print(
        "Conhecimento verificado: "
        f"{'Sim' if relatorio.get('conhecimento_verificado') else 'Não'}"
    )

    print("=" * 60)


# ============================================================
# TESTES DO CONTEXTO
# ============================================================

def testar_comparacao_contextual():

    print("\nTESTES DE COMPARAÇÃO CONTEXTUAL")
    print("=" * 60)

    testes = [
        (
            "Python 0.9.0 foi lançado em 1991.",
            "Python 0.9.0 foi lançado em 1995.",
            "Python",
            "Python",
            "Mesmo objeto e mesma relação: possível divergência.",
            "possivel_divergencia"
        ),
        (
            "Python 0.9.0 foi lançado em 1991.",
            "Python 3.0 foi lançado em 2008.",
            "Python",
            "Python",
            "Versões diferentes: não sinalizar divergência.",
            "proximidade_tematica"
        ),
        (
            "Python foi criado por Guido van Rossum.",
            "Python foi lançado em 1991.",
            "Python",
            "Python",
            "Relações diferentes: contexto não comparável.",
            "contexto_insuficiente_ou_diferente"
        ),
        (
            "Python foi criado por Guido van Rossum.",
            "Python foi criado por James Gosling.",
            "Python",
            "Python",
            "Responsáveis diferentes: possível divergência.",
            "possivel_divergencia"
        )
    ]

    sucessos = 0

    for (
        afirmacao_a,
        afirmacao_b,
        assunto_a,
        assunto_b,
        descricao,
        estado_esperado
    ) in testes:

        resultado = comparar_afirmacoes(
            afirmacao_a,
            afirmacao_b,
            assunto_a,
            assunto_b
        )

        passou = resultado["estado"] == estado_esperado

        if passou:
            sucessos += 1

        print("\nTeste:", descricao)
        print("Afirmação A:", afirmacao_a)
        print("Afirmação B:", afirmacao_b)

        print(
            "Entidade A:",
            resultado["contexto_a"]["entidade"]
        )

        print(
            "Entidade B:",
            resultado["contexto_b"]["entidade"]
        )

        print(
            "Relação A:",
            resultado["contexto_a"]["relacao"]
        )

        print(
            "Relação B:",
            resultado["contexto_b"]["relacao"]
        )

        print(
            "Responsável A:",
            resultado["contexto_a"]["responsavel"]
        )

        print(
            "Responsável B:",
            resultado["contexto_b"]["responsavel"]
        )

        print("Estado:", resultado["estado"])
        print("Esperado:", estado_esperado)
        print("Sinais:", resultado["sinais"])
        print("Teste:", "PASSOU" if passou else "FALHOU")

        print("-" * 60)

    print(f"\nResultado: {sucessos}/{len(testes)} testes passaram.")

    return sucessos == len(testes)


# ============================================================
# TESTE INDIVIDUAL DO MODULO
# ============================================================

if __name__ == "__main__":

    print("Avaliador de conhecimentos da ANNIA LUCILLA")
    print("Este teste não aprova nem salva conhecimentos.")

    testes_aprovados = testar_comparacao_contextual()

    print(
        "\nResultado dos testes:",
        "SUCESSO" if testes_aprovados else "REVISAR"
    )

    consulta = input(
        "\nDigite o assunto para consultar a memória: "
    ).strip()

    if not consulta:
        consulta = "Python"

    memoria = carregar_memoria_verificada(consulta)

    print(
        "\nConhecimentos verificados recuperados: "
        f"{len(memoria.get('conhecimentos', []))}"
    )

    print(
        "Estado da recuperação: "
        f"{memoria.get('estado')}"
    )

    if memoria.get("erro"):
        print("Erro ao consultar memória:", memoria["erro"])

    print(
        "\nPara testar a avaliação completa, execute "
        "o fluxo de aquisição pelo módulo principal."
    )