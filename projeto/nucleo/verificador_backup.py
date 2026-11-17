 
from datetime import datetime
from pathlib import Path
import json
import re
import unicodedata
from cerebro.avaliador_conhecimentos import comparar_afirmacoes


PASTA_PROJETO = Path(__file__).resolve().parent.parent
ARQUIVO_IDENTIDADE = PASTA_PROJETO / "dados" / "identidade.json"

ESTADOS_VALIDOS = {"pendente", "verificado", "contestado"}

PALAVRAS_COMUNS = {
    "a", "o", "as", "os", "um", "uma", "de", "do", "da",
    "dos", "das", "e", "ou", "que", "em", "no", "na",
    "nos", "nas", "para", "por", "com", "como", "se",
    "sua", "seu", "suas", "seus", "foi", "ser", "sao",
    "isso", "essa", "esse", "esta", "este", "tambem",
    "mais", "muito", "pode", "podem", "entre", "sobre",
    "ele", "ela", "eles", "elas", "qual", "quais",
    "quando", "onde", "porque", "portanto", "assim",
    "ainda", "ja", "tem", "tinha", "ter", "sendo",
    "sido", "nosso", "nossa", "serao", "foram",
    "voce", "meu", "minha", "italo", "luci"
}

MARCADORES_RELACIONAIS = {
    "criado", "criada", "criados", "criadas",
    "desenvolvido", "desenvolvida", "desenvolvidos",
    "desenvolvidas", "fundado", "fundada", "fundados",
    "fundadas", "inventado", "inventada", "inventados",
    "inventadas", "lancado", "lancada", "lancados",
    "lancadas", "construido", "construida",
    "construidos", "construidas"
}

MARCADORES_FACTUAIS = {
    "sao", "eh", "e", "esta", "estao", "possui",
    "possuem", "tem", "mede", "medem", "fica",
    "ficam", "localiza", "localizam", "causa",
    "causam", "produz", "produzem", "contem",
    "nasceu", "morreu", "significa", "representa",
    "representam", "acontece", "ocorre", "ocorrem",
    "depende", "conhecida", "conhecido", "conhecidos",
    "conhecidas", "utilizada", "utilizado", "utilizados",
    "utilizadas", "inclui", "incluem", "permite",
    "permitem", "oferece", "oferecem", "conta",
    "contam", "funciona", "funcionam", "trabalha",
    "trabalham", "atua", "atuam", "abrange",
    "abrangem", "consiste", "corresponde",
    "correspondem", "possibilita", "possibilitam",
    "apresenta", "apresentam"
}

EXPRESSOES_IDENTIDADE = (
    "meu nome", "me chamo", "sou annia", "sou luci",
    "meu criador", "fui criada", "fui desenvolvido",
    "meu proposito", "minha finalidade", "minha versao",
    "nasci em"
)

INICIOS_NAO_FACTUAIS = (
    "espero que tenha ajudado", "espero ter ajudado",
    "voce gostaria", "gostaria de saber", "quer que eu",
    "posso ajudar", "vamos continuar", "aqui esta",
    "a seguir", "em resumo", "conclusao",
    "consideracoes finais", "alguns recursos incluem",
    "bem-vindo", "bem vinda", "obrigado", "obrigada",
    "ola", "oi", "bom dia", "boa tarde", "boa noite"
)

DECLARACOES_DE_INCERTEZA = (
    "nao sei",
    "nao tenho certeza",
    "nao tenho informacoes suficientes",
    "nao possuo informacoes suficientes",
    "nao encontrei informacoes",
    "nao encontrei dados",
    "nao ha informacoes suficientes",
    "nao ha dados suficientes",
    "nao consigo confirmar",
    "nao posso confirmar",
    "nao tenho conhecimento suficiente",
    "nao tenho dados para confirmar",
    "nao posso afirmar",
    "nao e possivel confirmar",
    "nao foi possivel confirmar",
    "preciso de mais informacoes",
    "essa informacao nao esta disponivel",
    "essa informacao nao consta",
    "nao encontrei registros",
    "nao ha informacoes disponiveis",
    "nao existem informacoes disponiveis",
    "nao ha dados disponiveis",
    "nao existem dados disponiveis",
    "nao consta na minha base",
    "nao consta na base de conhecimentos",
    "nao encontrei na minha base",
    "nao encontrei na base de conhecimentos",
    "nao possuo informacoes sobre",
    "nao tenho informacoes sobre",
    "nao disponho de informacoes"
)

RELACOES_CANONICAS = {
    "criado": "criar",
    "criada": "criar",
    "criados": "criar",
    "criadas": "criar",
    "desenvolvido": "desenvolver",
    "desenvolvida": "desenvolver",
    "desenvolvidos": "desenvolver",
    "desenvolvidas": "desenvolver",
    "fundado": "fundar",
    "fundada": "fundar",
    "fundados": "fundar",
    "fundadas": "fundar",
    "inventado": "inventar",
    "inventada": "inventar",
    "inventados": "inventar",
    "inventadas": "inventar",
    "lancado": "lancar",
    "lancada": "lancar",
    "lancados": "lancar",
    "lancadas": "lancar",
    "construido": "construir",
    "construida": "construir",
    "construidos": "construir",
    "construidas": "construir",
    "e": "ser",
    "eh": "ser",
    "sao": "ser",
    "ser": "ser",
    "era": "ser",
    "eram": "ser",
    "foi": "ser",
    "foram": "ser",
    "constitui": "ser",
    "constituem": "ser"
}

MARCADORES_NEGACAO = {"nao", "nunca", "jamais"}

RELACOES_IGNORADAS_NA_COMPARACAO = {
    "criado", "criada", "criados", "criadas",
    "desenvolvido", "desenvolvida", "desenvolvidos",
    "desenvolvidas", "fundado", "fundada", "fundados",
    "fundadas", "inventado", "inventada", "inventados",
    "inventadas", "lancado", "lancada", "lancados",
    "lancadas", "construido", "construida",
    "construidos", "construidas"
}


# --------------------------------------------------
# NORMALIZACAO
# --------------------------------------------------

def normalizar(texto):
    texto = str(texto or "").lower().strip()
    texto = unicodedata.normalize("NFD", texto)

    return "".join(
        caractere
        for caractere in texto
        if unicodedata.category(caractere) != "Mn"
    )


def extrair_termos(texto):
    termos = re.findall(
        r"\b[a-z0-9]+\b",
        normalizar(texto)
    )

    return {
        termo for termo in termos
        if len(termo) > 2 and termo not in PALAVRAS_COMUNS
    }


def extrair_numeros(texto):
    return set(
        re.findall(r"\b\d+\b", normalizar(texto))
    )


# --------------------------------------------------
# IDENTIDADE OFICIAL
# --------------------------------------------------

def carregar_identidade():
    try:
        with open(
            ARQUIVO_IDENTIDADE,
            "r",
            encoding="utf-8"
        ) as arquivo:
            identidade = json.load(arquivo)

        return identidade if isinstance(identidade, dict) else {}

    except (OSError, json.JSONDecodeError):
        return {}


def eh_afirmacao_de_identidade(texto):
    normalizado = normalizar(texto)

    return any(
        expressao in normalizado
        for expressao in EXPRESSOES_IDENTIDADE
    )


def verificar_identidade(afirmacao):
    identidade = carregar_identidade()
    normalizada = normalizar(afirmacao)

    campos = {
        "nome": ("nome", "nome_completo"),
        "apelido": ("apelido",),
        "criador": ("criador",),
        "proposito": ("proposito", "finalidade"),
        "versao": ("versao",),
        "data_nascimento": ("data_nascimento",)
    }

    evidencias = []

    for descricao, chaves in campos.items():
        valor = None

        for chave in chaves:
            candidato = identidade.get(chave)

            if isinstance(candidato, str) and candidato.strip():
                valor = candidato
                break

        if not valor:
            continue

        if normalizar(valor) in normalizada:
            evidencias.append({
                "origem": "identidade_oficial",
                "campo": descricao,
                "valor": valor,
                "estado": "confirmado_no_arquivo"
            })

    if evidencias:
        return {
            "classificacao": "apoio_identidade_oficial",
            "evidencias": evidencias
        }

    return {
        "classificacao": "sem_apoio_local",
        "evidencias": []
    }


# --------------------------------------------------
# IDENTIFICACAO DE INCERTEZA
# --------------------------------------------------

def remover_vocativo(texto):
    normalizado = normalizar(texto)

    return re.sub(
        r"^(?:italo|luci|annia lucilla)\s*[,!:]\s*",
        "",
        normalizado
    ).strip()


def eh_declaracao_de_incerteza(texto):
    normalizado = remover_vocativo(texto)

    return any(
        normalizado.startswith(expressao)
        for expressao in DECLARACOES_DE_INCERTEZA
    )


# --------------------------------------------------
# IDENTIFICACAO DE AFIRMACOES
# --------------------------------------------------

def contem_marcador_relacional(texto):
    palavras = set(
        re.findall(r"\b[a-z0-9]+\b", normalizar(texto))
    )

    return bool(palavras & set(RELACOES_CANONICAS))


def possui_indicador_factual(texto):
    normalizado = normalizar(texto)

    palavras = set(
        re.findall(r"\b[a-z0-9]+\b", normalizado)
    )

    if palavras & MARCADORES_FACTUAIS:
        return True

    if extrair_numeros(normalizado):
        return True

    return contem_marcador_relacional(normalizado)


def parece_afirmacao_declarativa(texto):
    normalizado = remover_vocativo(texto)
    palavras = re.findall(r"\b[a-z0-9]+\b", normalizado)

    if len(palavras) < 5:
        return False

    if texto.rstrip().endswith("?"):
        return False

    if eh_declaracao_de_incerteza(texto):
        return False

    if any(
        normalizado.startswith(inicio)
        for inicio in INICIOS_NAO_FACTUAIS
    ):
        return False

    return True


def dividir_afirmacoes(resposta):
    if not isinstance(resposta, str):
        return []

    afirmacoes = []

    for linha in re.split(r"\n+", resposta):
        linha = linha.strip()

        if not linha:
            continue

        linha = re.sub(
            r"^\s*(?:[-*•]|\d+[.)])\s+",
            "",
            linha
        )

        partes = re.split(
            r"(?<=[.!?])\s+",
            linha
        )

        for parte in partes:
            parte = parte.strip()

            if not parte or len(parte) < 10:
                continue

            normalizada = remover_vocativo(parte)

            if eh_declaracao_de_incerteza(parte):
                continue

            if parte.endswith("?") or parte.endswith(":"):
                continue

            if any(
                normalizada.startswith(inicio)
                for inicio in INICIOS_NAO_FACTUAIS
            ):
                continue

            if eh_afirmacao_de_identidade(parte):
                afirmacoes.append(parte)
                continue

            if (
                possui_indicador_factual(parte)
                or parece_afirmacao_declarativa(parte)
            ):
                afirmacoes.append(parte)

    return afirmacoes


# --------------------------------------------------
# CONTEXTUALIZACAO DE RESPOSTAS CURTAS
# --------------------------------------------------

def contextualizar_afirmacao_curta(pergunta, afirmacao):
    """
    Usa a pergunta como contexto para respostas curtas.

    A pergunta não é considerada evidência. Ela apenas
    complementa a frase para permitir a comparação com
    os registros locais.

    Respostas longas permanecem inalteradas.
    """

    if not isinstance(pergunta, str) or not pergunta.strip():
        return afirmacao

    if not isinstance(afirmacao, str) or not afirmacao.strip():
        return afirmacao

    if eh_afirmacao_de_identidade(afirmacao):
        return afirmacao

    termos_resposta = extrair_termos(afirmacao)

    # Só contextualiza respostas com poucos termos relevantes.
    if len(termos_resposta) <= 4:
        return f"{pergunta.strip()} {afirmacao.strip()}"

    return afirmacao


# --------------------------------------------------
# COMPARACAO COM A BASE DE CONHECIMENTOS
# --------------------------------------------------

def avaliar_evidencia(afirmacao, conhecimento):
    assunto = conhecimento.get("assunto", "")
    conteudo = conhecimento.get("conteudo", "")

    texto_conhecimento = f"{assunto} {conteudo}"

    termos_afirmacao = extrair_termos(afirmacao)
    termos_conhecimento = extrair_termos(texto_conhecimento)

    compartilhados = termos_afirmacao & termos_conhecimento

    proporcao = (
        len(compartilhados) / len(termos_afirmacao)
        if termos_afirmacao else 0
    )

    relacionada = (
        len(compartilhados) >= 3
        and proporcao >= 0.65
    )

    numeros_afirmacao = extrair_numeros(afirmacao)
    numeros_conhecimento = extrair_numeros(texto_conhecimento)

    if numeros_afirmacao and not numeros_afirmacao.issubset(
        numeros_conhecimento
    ):
        relacionada = False

    if contem_marcador_relacional(afirmacao):
        if not contem_marcador_relacional(texto_conhecimento):
            relacionada = False

    return {
        "relacionada": relacionada,
        "termos_compartilhados": sorted(compartilhados),
        "proporcao_textual": round(proporcao, 2)
    }


# --------------------------------------------------
# DETECCAO DE CONTRADICOES
# --------------------------------------------------

def extrair_relacoes_comparaveis(texto):
    palavras = re.findall(
        r"\b[a-z0-9]+\b",
        normalizar(texto)
    )

    return {
        RELACOES_CANONICAS[palavra]
        for palavra in palavras
        if palavra in RELACOES_CANONICAS
    }


def possui_negacao(texto):
    palavras = set(
        re.findall(r"\b[a-z0-9]+\b", normalizar(texto))
    )

    return bool(palavras & MARCADORES_NEGACAO)


def eh_negacao_de_exclusividade(texto):
    normalizado = normalizar(texto)

    expressoes = (
        "nao apenas",
        "nao e apenas",
        "nao eh apenas",
        "nao somente",
        "nao e somente",
        "nao eh somente",
        "nao so",
        "nao e so",
        "nao eh so",
        "nao exclusivamente",
        "nao e exclusivamente",
        "nao eh exclusivamente",
        "nao e exclusivo",
        "nao eh exclusivo",
        "nao e exclusiva",
        "nao eh exclusiva",
        "nao se limita",
        "nao esta limitado",
        "nao esta limitada",
        "nao esta restrito",
        "nao esta restrita"
    )

    return any(
        expressao in normalizado
        for expressao in expressoes
    )


def avaliar_contradicao(afirmacao, conhecimento):
    conteudo = conhecimento.get("conteudo", "")
    assunto = conhecimento.get("assunto", "")

    texto_conhecimento = f"{assunto}. {conteudo}"

    resultado_padrao = {
        "contradicao_detectada": False,
        "motivo": None
    }

    if eh_negacao_de_exclusividade(afirmacao):
        return resultado_padrao

    relacoes_resposta = extrair_relacoes_comparaveis(afirmacao)
    relacoes_conhecimento = extrair_relacoes_comparaveis(
        texto_conhecimento
    )

    relacoes_compartilhadas = (
        relacoes_resposta & relacoes_conhecimento
    )

    if not relacoes_compartilhadas:
        return resultado_padrao

    termos_resposta = extrair_termos(afirmacao)
    termos_conhecimento = extrair_termos(texto_conhecimento)

    termos_resposta -= RELACOES_IGNORADAS_NA_COMPARACAO
    termos_conhecimento -= RELACOES_IGNORADAS_NA_COMPARACAO

    termos_resposta = {
        termo for termo in termos_resposta
        if not termo.isdigit()
    }

    termos_conhecimento = {
        termo for termo in termos_conhecimento
        if not termo.isdigit()
    }

    compartilhados = termos_resposta & termos_conhecimento

    if len(compartilhados) < 3:
        return resultado_padrao

    numeros_resposta = extrair_numeros(afirmacao)
    numeros_conhecimento = extrair_numeros(
        texto_conhecimento
    )

    anos_resposta = {
        numero for numero in numeros_resposta
        if len(numero) == 4
    }

    anos_conhecimento = {
        numero for numero in numeros_conhecimento
        if len(numero) == 4
    }

    if anos_resposta and anos_conhecimento:
        if anos_resposta.isdisjoint(anos_conhecimento):
            return {
                "contradicao_detectada": True,
                "motivo": "anos_diferentes",
                "valores_resposta": sorted(anos_resposta),
                "valores_registrados": sorted(anos_conhecimento)
            }

    elif numeros_resposta and numeros_conhecimento:
        if numeros_resposta.isdisjoint(numeros_conhecimento):
            return {
                "contradicao_detectada": True,
                "motivo": "valores_numericos_diferentes",
                "valores_resposta": sorted(numeros_resposta),
                "valores_registrados": sorted(numeros_conhecimento)
            }

    negacao_resposta = possui_negacao(afirmacao)
    negacao_conhecimento = possui_negacao(texto_conhecimento)

    if negacao_resposta != negacao_conhecimento:
        return {
            "contradicao_detectada": True,
            "motivo": "negacao_explicita",
            "negacao_resposta": negacao_resposta,
            "negacao_registrada": negacao_conhecimento
        }

    return resultado_padrao
# --------------------------------------------------
# COMPARACAO CONTEXTUAL COM O AVALIADOR
# --------------------------------------------------

def avaliar_divergencia_contextual(afirmacao, conhecimento):
    """
    Compara uma afirmação com um conhecimento local
    utilizando o avaliador contextual.

    O resultado identifica possíveis divergências,
    mas nunca confirma automaticamente uma contradição.
    """

    if not isinstance(conhecimento, dict):
        return None

    assunto = conhecimento.get("assunto", "")
    conteudo = conhecimento.get("conteudo", "")

    if not isinstance(assunto, str):
        assunto = ""

    if not isinstance(conteudo, str) or not conteudo.strip():
        return None

    resultado = comparar_afirmacoes(
        afirmacao,
        conteudo,
        assunto,
        assunto
    )

    if not isinstance(resultado, dict):
        return None

    if resultado.get("estado") != "possivel_divergencia":
        return None

    return {
        "assunto": assunto,
        "id_conhecimento": conhecimento.get("id"),
        "estado_verificacao": conhecimento.get(
            "estado_verificacao",
            "pendente"
        ),
        "estado_comparacao": resultado.get("estado"),
        "similaridade": resultado.get("similaridade"),
        "sinais": resultado.get("sinais", []),
        "contexto": resultado.get("comparacao_contexto", {}),
        "verificacao_semantica": False,
        "contradicao_confirmada": False
    }


# --------------------------------------------------
# ANALISE INDIVIDUAL DE AFIRMACOES
# --------------------------------------------------

def analisar_afirmacao(
    afirmacao,
    conhecimentos,
    indice=1,
    contexto_pergunta=None
):
    if eh_afirmacao_de_identidade(afirmacao):
        resultado_identidade = verificar_identidade(afirmacao)

        if (
            resultado_identidade["classificacao"]
            == "apoio_identidade_oficial"
        ):
            return {
                "id_afirmacao": indice,
                "texto": afirmacao,
                "classificacao": "apoio_identidade_oficial",
                "quantidade_evidencias": len(
                    resultado_identidade["evidencias"]
                ),
                "evidencias": resultado_identidade["evidencias"],
                "contradicoes": []
            }

        return {
            "id_afirmacao": indice,
            "texto": afirmacao,
            "classificacao": "sem_apoio_local",
            "quantidade_evidencias": 0,
            "evidencias": [],
            "contradicoes": []
        }

    afirmacao_com_contexto = contextualizar_afirmacao_curta(
        contexto_pergunta,
        afirmacao
    )

    evidencias = []
    contradicoes = []

    for conhecimento in conhecimentos:
        if not isinstance(conhecimento, dict):
            continue

        estado = conhecimento.get(
            "estado_verificacao",
            "pendente"
        )

        if estado not in ESTADOS_VALIDOS:
            estado = "pendente"

        resultado_contradicao = avaliar_contradicao(
            afirmacao_com_contexto,
            conhecimento
        )

        if resultado_contradicao["contradicao_detectada"]:
            contradicoes.append({
                "id_conhecimento": conhecimento.get("id"),
                "assunto": conhecimento.get("assunto"),
                "conteudo_registrado": conhecimento.get("conteudo"),
                "estado": estado,
                "motivo": resultado_contradicao["motivo"],
                "detalhes": resultado_contradicao
            })

        resultado = avaliar_evidencia(
            afirmacao_com_contexto,
            conhecimento
        )

        if not resultado["relacionada"]:
            continue

        evidencias.append({
            "id_conhecimento": conhecimento.get("id"),
            "assunto": conhecimento.get("assunto"),
            "origem": conhecimento.get("origem"),
            "fonte": conhecimento.get("fonte"),
            "estado": estado,
            "termos_compartilhados": resultado[
                "termos_compartilhados"
            ],
            "proporcao_textual": resultado[
                "proporcao_textual"
            ]
        })

    estados = {
        evidencia["estado"]
        for evidencia in evidencias
    }

    if contradicoes:
        if any(
            item["estado"] == "verificado"
            for item in contradicoes
        ):
            classificacao = "contradicao_com_verificado"
        else:
            classificacao = "possivel_contradicao"

    elif not evidencias:
        classificacao = "sem_apoio_local"

    elif "contestado" in estados:
        classificacao = "apoio_contestado"

    elif "pendente" in estados and "verificado" in estados:
        classificacao = "apoio_misto"

    elif "pendente" in estados:
        classificacao = "apoio_pendente"

    elif estados == {"verificado"}:
        classificacao = "apoio_marcado_verificado"

    else:
        classificacao = "sem_apoio_local"

    return {
        "id_afirmacao": indice,
        "texto": afirmacao,
        "classificacao": classificacao,
        "quantidade_evidencias": len(evidencias),
        "evidencias": evidencias,
        "contradicoes": contradicoes
    }


# --------------------------------------------------
# VERIFICACAO COMPLETA DA RESPOSTA
# --------------------------------------------------

def verificar_resposta(pergunta, resposta, conhecimentos=None):
    conhecimentos = conhecimentos or []

    if not isinstance(conhecimentos, list):
        conhecimentos = []

    if not isinstance(resposta, str) or not resposta.strip():
        afirmacoes = []
    else:
        afirmacoes = dividir_afirmacoes(resposta)

    analises = [
        analisar_afirmacao(
            afirmacao,
            conhecimentos,
            indice,
            contexto_pergunta=pergunta
        )
        for indice, afirmacao in enumerate(afirmacoes, start=1)
    ]

    contagens = {
        "apoio_identidade_oficial": 0,
        "apoio_marcado_verificado": 0,
        "apoio_pendente": 0,
        "apoio_misto": 0,
        "apoio_contestado": 0,
        "sem_evidencia_local": 0,
        "contradicao_com_verificado": 0,
        "possivel_contradicao": 0
    }

    for analise in analises:
        classificacao = analise["classificacao"]

        if classificacao in contagens:
            contagens[classificacao] += 1
        else:
            contagens["sem_evidencia_local"] += 1

    identidade_sem_apoio = any(
        eh_afirmacao_de_identidade(analise["texto"])
        and analise["classificacao"] != "apoio_identidade_oficial"
        for analise in analises
    )

    if not isinstance(resposta, str) or not resposta.strip():
        nivel = "resposta_invalida"
        descricao = "A resposta está vazia ou é inválida."
        bloquear = True

    elif identidade_sem_apoio:
        nivel = "identidade_sem_confirmacao"
        descricao = (
            "Existe uma afirmação sobre a identidade da Luci "
            "que não encontrou confirmação no arquivo oficial."
        )
        bloquear = True

    elif contagens["contradicao_com_verificado"] > 0:
        nivel = "contradicao_com_conhecimento_verificado"
        descricao = (
            "Foi identificada uma possível contradição "
            "com um conhecimento marcado como verificado."
        )
        bloquear = True

    elif contagens["apoio_contestado"] > 0:
        nivel = "possui_evidencia_contestada"
        descricao = (
            "Existem afirmações relacionadas "
            "a conhecimentos contestados."
        )
        bloquear = True

    elif contagens["possivel_contradicao"] > 0:
        nivel = "possivel_contradicao_com_registro"
        descricao = (
            "Existe uma possível contradição com um registro "
            "que ainda não está verificado."
        )
        bloquear = True

    elif contagens["sem_evidencia_local"] > 0:
        nivel = "possui_afirmacoes_sem_evidencia"
        descricao = (
            "Existem afirmações sem suporte na memória local. "
            "No modo rigoroso, a resposta foi bloqueada."
        )
        bloquear = True

    elif (
        contagens["apoio_pendente"] > 0
        or contagens["apoio_misto"] > 0
    ):
        nivel = "possui_evidencia_pendente"
        descricao = (
            "Existem afirmações relacionadas a registros "
            "que ainda aguardam verificação. "
            "No modo rigoroso, a resposta foi bloqueada."
        )
        bloquear = True

    elif len(analises) == 0:
        nivel = "sem_afirmacoes_factuais"
        descricao = (
            "Não foram identificadas afirmações factuais "
            "que exijam comparação com a memória local."
        )
        bloquear = False

    else:
        nivel = "afirmacoes_com_suporte_local"
        descricao = (
            "As afirmações analisadas possuem suporte "
            "na identidade oficial ou em conhecimentos "
            "marcados como verificados."
        )
        bloquear = False

    return {
        "data_verificacao": datetime.now().isoformat(
            timespec="seconds"
        ),
        "pergunta": pergunta,
        "nivel": nivel,
        "descricao": descricao,
        "bloquear_resposta": bloquear,
        "verificacao_independente": False,
        "quantidade_afirmacoes": len(analises),
        "afirmacoes_analisadas": analises,
        "contagens": contagens,
        "observacao": (
            "A identidade é comparada com o arquivo oficial "
            "de identidade da Luci. Os demais conhecimentos "
            "são comparados com a base local. Essas verificações "
            "não representam confirmação independente da verdade. "
            "Um registro marcado como verificado representa "
            "apenas o estado cadastrado na base. A detecção de "
            "afirmações e contradições utiliza padrões linguísticos "
            "e objetivos, podendo deixar de identificar alguns "
            "casos ou classificar frases incorretamente. "
            "Respostas curtas são contextualizadas com a pergunta "
            "para permitir a comparação com registros locais. "
            "A pergunta fornece contexto, não evidência. "
            "Declarações explícitas de incerteza são reconhecidas "
            "como declarações não factuais quando correspondem "
            "aos padrões cadastrados. O modo rigoroso bloqueia "
            "afirmações sem suporte local."
        )
    }
