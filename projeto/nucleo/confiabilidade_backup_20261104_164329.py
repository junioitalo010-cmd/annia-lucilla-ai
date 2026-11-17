 
import unicodedata
from datetime import datetime


ESTADOS_VALIDOS = {
    "pendente",
    "verificado",
    "contestado"
}


def normalizar(texto):
    texto = str(texto or "").lower()
    texto = unicodedata.normalize("NFD", texto)

    return "".join(
        caractere
        for caractere in texto
        if unicodedata.category(caractere) != "Mn"
    )


def classificar_origem(origem):
    origem_normalizada = normalizar(origem)

    if (
        "usuario" in origem_normalizada
        or "fornecida" in origem_normalizada
    ):
        return "informacao_fornecida_pelo_usuario"

    if (
        "modelo" in origem_normalizada
        or "ollama" in origem_normalizada
    ):
        return "informacao_gerada_por_modelo"

    if (
        "fonte" in origem_normalizada
        or "pesquisa" in origem_normalizada
    ):
        return "informacao_com_referencia_de_fonte"

    if "identidade oficial" in origem_normalizada:
        return "identidade_oficial"

    return "origem_nao_classificada"


def analisar_confiabilidade(
    pergunta,
    resposta,
    conhecimentos=None,
    verificacao=None,
    origem_resposta="modelo_de_linguagem_local"
):
    conhecimentos = conhecimentos or []

    if isinstance(verificacao, dict):
        return consolidar_verificacao(
            pergunta,
            resposta,
            conhecimentos,
            verificacao,
            origem_resposta
        )

    return analisar_confiabilidade_lexical(
        pergunta,
        resposta,
        conhecimentos,
        origem_resposta
    )


def consolidar_verificacao(
    pergunta,
    resposta,
    conhecimentos,
    verificacao,
    origem_resposta="modelo_de_linguagem_local"
):
    afirmacoes = verificacao.get(
        "afirmacoes_analisadas",
        []
    )

    if not isinstance(afirmacoes, list):
        afirmacoes = []

    contagens = {
        "apoio_identidade_oficial": 0,
        "apoio_marcado_verificado": 0,
         "apoio_declaracao_usuario": 0,
        "apoio_pendente": 0,
        "apoio_misto": 0,
        "apoio_contestado": 0,
        "sem_evidencia_local": 0,
        "contradicao_com_verificado": 0,
        "possivel_contradicao": 0
    }

    contagem_estados = {
        "pendente": 0,
        "verificado": 0,
        "contestado": 0
    }

    registros = {}
    registros_identidade = []
    termos_totais = set()

    for afirmacao in afirmacoes:
        if not isinstance(afirmacao, dict):
            continue

        classificacao = afirmacao.get(
            "classificacao",
            "sem_apoio_local"
        )

        if classificacao in contagens:
            contagens[classificacao] += 1
        else:
            contagens["sem_evidencia_local"] += 1

        evidencias = afirmacao.get("evidencias", [])

        if not isinstance(evidencias, list):
            evidencias = []

        for evidencia in evidencias:
            if not isinstance(evidencia, dict):
                continue

            origem_evidencia = evidencia.get(
                "origem",
                ""
            )

            if (
                origem_evidencia == "identidade_oficial"
                or evidencia.get("estado") == "confirmado_no_arquivo"
            ):
                registros_identidade.append({
                    "campo": evidencia.get("campo"),
                    "valor": evidencia.get("valor"),
                    "origem": "identidade_oficial",
                    "estado": "confirmado_no_arquivo"
                })
                continue

            estado = evidencia.get("estado", "pendente")

            if estado not in ESTADOS_VALIDOS:
                estado = "pendente"

            identificador = evidencia.get(
                "id_conhecimento"
            )

            chave = (
                identificador
                if identificador is not None
                else (
                    evidencia.get("assunto"),
                    origem_evidencia
                )
            )

            if chave not in registros:
                registros[chave] = {
                    "id": identificador,
                    "assunto": evidencia.get("assunto"),
                    "origem": origem_evidencia,
                    "classificacao_origem": classificar_origem(
                        origem_evidencia
                    ),
                    "estado_verificacao": estado,
                    "fonte": evidencia.get("fonte"),
                    "termos_compartilhados": set()
                }

            termos = evidencia.get(
                "termos_compartilhados",
                []
            )

            if not isinstance(termos, (list, tuple, set)):
                termos = []

            registros[chave]["termos_compartilhados"].update(
                termos
            )

            contagem_estados[estado] += 1
            termos_totais.update(termos)

    registros_relacionados = []

    for registro in registros.values():
        registro["termos_compartilhados"] = sorted(
            registro["termos_compartilhados"]
        )

        registros_relacionados.append(registro)

    quantidade = len(afirmacoes)

    if quantidade == 0:
        nivel = "sem_afirmacoes_factuais"
        descricao = (
            "Não foram identificadas afirmações factuais "
            "que exijam comparação com a memória local."
        )
        tipo_resposta = "sem_afirmacoes_factuais"

    elif contagens["contradicao_com_verificado"] > 0:
        nivel = "contradicao_com_conhecimento_verificado"
        descricao = (
            "Uma ou mais afirmações contradizem conhecimentos "
            "marcados como verificados na memória local."
        )
        tipo_resposta = "com_afirmacoes_factuais"

    elif contagens["possivel_contradicao"] > 0:
        nivel = "possivel_contradicao"
        descricao = (
            "Uma ou mais afirmações apresentam possíveis "
            "contradições com registros da memória local."
        )
        tipo_resposta = "com_afirmacoes_factuais"

    elif contagens["apoio_contestado"] > 0:
        nivel = "possui_conhecimento_contestado"
        descricao = (
            "Uma ou mais afirmações possuem evidências "
            "associadas a conhecimentos contestados."
        )
        tipo_resposta = "com_afirmacoes_factuais"

    elif (
        contagens["apoio_pendente"] > 0
        or contagens["apoio_misto"] > 0
    ):
        nivel = "possui_evidencia_pendente"
        descricao = (
            "Uma ou mais afirmações possuem conhecimentos "
            "relacionados ainda pendentes de verificação."
        )
        tipo_resposta = "com_afirmacoes_factuais"

    elif contagens["sem_evidencia_local"] == quantidade:
        nivel = "sem_apoio_local"
        descricao = (
            "Nenhuma afirmação encontrou evidência "
            "suficiente na memória local ou na identidade oficial."
        )
        tipo_resposta = "com_afirmacoes_factuais"

    elif contagens["sem_evidencia_local"] > 0:
        nivel = "possui_afirmacoes_sem_evidencia"
        descricao = (
            "Parte das afirmações não encontrou evidência "
            "suficiente na memória local."
        )
        tipo_resposta = "com_afirmacoes_factuais"

    elif (
        contagens["apoio_identidade_oficial"]
        + contagens["apoio_marcado_verificado"]
        + contagens["apoio_declaracao_usuario"]
        == quantidade

    ):
        nivel = "afirmacoes_com_suporte_local"
        descricao = (
            "Todas as afirmações analisadas possuem suporte "
            "na identidade oficial ou em conhecimentos "
            "marcados como verificados."
        )
        tipo_resposta = "com_afirmacoes_factuais"

    else:
        nivel = "apoio_local_sem_classificacao"
        descricao = (
            "A análise encontrou registros, mas não conseguiu "
            "classificar todo o suporte disponível."
        )
        tipo_resposta = "com_afirmacoes_factuais"

    bloquear = (
        verificacao.get("bloquear_resposta") is not False
    )

    return {
        "data_analise": datetime.now().isoformat(
            timespec="seconds"
        ),
        "origem_resposta": origem_resposta,
        "tipo_resposta": tipo_resposta,
        "nivel": nivel,
        "descricao": descricao,
        "registros_relacionados": registros_relacionados,
        "registros_identidade": registros_identidade,
        "contagem_estados": contagem_estados,
        "termos_relevantes_compartilhados": sorted(
            termos_totais
        ),
        "quantidade_afirmacoes": quantidade,
        "contagens_afirmacoes": contagens,
        "bloquear_resposta": bloquear,
        "verificacao_independente": False,
        "observacao": (
            "Esta análise consolida as evidências encontradas "
            "pelo verificador. A identidade é consultada no arquivo "
            "oficial da Luci, enquanto os demais conhecimentos são "
            "comparados com a memória local. A correspondência "
            "textual não comprova automaticamente a verdade das "
            "afirmações. Um registro marcado como verificado "
            "representa apenas o estado cadastrado na base."
        )
    }


def analisar_confiabilidade_lexical(
    pergunta,
    resposta,
    conhecimentos,
    origem_resposta="modelo_de_linguagem_local"
):
    palavras_pergunta = set(normalizar(pergunta).split())
    palavras_resposta = set(normalizar(resposta).split())

    registros_relacionados = []
    termos_compartilhados_totais = set()

    contagem_estados = {
        "pendente": 0,
        "verificado": 0,
        "contestado": 0
    }

    for conhecimento in conhecimentos:
        if not isinstance(conhecimento, dict):
            continue

        assunto = conhecimento.get("assunto", "")
        conteudo = conhecimento.get("conteudo", "")

        texto_registro = normalizar(
            f"{assunto} {conteudo}"
        )

        palavras_registro = set(texto_registro.split())

        if not (palavras_pergunta & palavras_registro):
            continue

        relacao_resposta = (
            palavras_resposta & palavras_registro
        )

        estado = conhecimento.get(
            "estado_verificacao",
            "pendente"
        )

        if estado not in ESTADOS_VALIDOS:
            estado = "pendente"

        contagem_estados[estado] += 1

        termos_compartilhados_totais.update(
            relacao_resposta
        )

        registros_relacionados.append({
            "id": conhecimento.get("id"),
            "assunto": assunto,
            "origem": conhecimento.get("origem"),
            "classificacao_origem": classificar_origem(
                conhecimento.get("origem", "")
            ),
            "estado_verificacao": estado,
            "fonte": conhecimento.get("fonte"),
            "termos_compartilhados": sorted(
                relacao_resposta
            )
        })

    if not registros_relacionados:
        nivel = "sem_apoio_local"
        descricao = (
            "Nenhum conhecimento relacionado foi encontrado "
            "na memória local."
        )

    elif contagem_estados["contestado"] > 0:
        nivel = "possui_conhecimento_contestado"
        descricao = (
            "Existem conhecimentos relacionados marcados "
            "como contestados."
        )

    elif contagem_estados["pendente"] > 0:
        nivel = "apoio_em_conhecimento_pendente"
        descricao = (
            "Existem conhecimentos relacionados pendentes."
        )

    elif contagem_estados["verificado"] > 0:
        nivel = "apoio_em_conhecimento_marcado_verificado"
        descricao = (
            "Existem conhecimentos relacionados marcados "
            "como verificados."
        )

    else:
        nivel = "apoio_local_sem_classificacao"
        descricao = (
            "Existem registros relacionados na memória."
        )

    return {
        "data_analise": datetime.now().isoformat(
            timespec="seconds"
        ),
        "origem_resposta": origem_resposta,
        "nivel": nivel,
        "descricao": descricao,
        "registros_relacionados": registros_relacionados,
        "contagem_estados": contagem_estados,
        "termos_relevantes_compartilhados": sorted(
            termos_compartilhados_totais
        ),
        "verificacao_independente": False,
        "observacao": (
            "Análise lexical de compatibilidade. "
            "Não comprova a veracidade das informações."
        )
    }
