 
def normalizar_texto(valor):
    if valor is None:
        return ""

    return str(valor).strip()


def analisar_experiencias(objetivo, experiencias):
    objetivo_palavras = set(objetivo.lower().split())
    relevantes = []

    if not isinstance(experiencias, list):
        return relevantes

    for experiencia in experiencias:
        if not isinstance(experiencia, dict):
            continue

        texto = " ".join([
            normalizar_texto(experiencia.get("situacao")),
            normalizar_texto(experiencia.get("acao_realizada")),
            normalizar_texto(experiencia.get("resultado")),
            normalizar_texto(experiencia.get("aprendizado"))
        ]).lower()

        palavras_experiencia = set(texto.split())
        correspondencias = objetivo_palavras.intersection(
            palavras_experiencia
        )

        if correspondencias:
            relevantes.append({
                "experiencia_id": experiencia.get("id"),
                "situacao": normalizar_texto(
                    experiencia.get("situacao")
                ),
                "acao_realizada": normalizar_texto(
                    experiencia.get("acao_realizada")
                ),
                "resultado": normalizar_texto(
                    experiencia.get("resultado")
                ),
                "aprendizado": normalizar_texto(
                    experiencia.get("aprendizado")
                ),
                "classificacao": normalizar_texto(
                    experiencia.get("classificacao_resultado")
                ),
                "correspondencias": len(correspondencias)
            })

    relevantes.sort(
        key=lambda item: item["correspondencias"],
        reverse=True
    )

    return relevantes[:5]


def criar_etapas(objetivo, experiencias_relevantes):
    etapas = [
        "Analisar o objetivo e identificar o resultado esperado.",
        "Identificar os recursos, conhecimentos e informações necessários.",
        "Consultar experiências anteriores relacionadas ao objetivo.",
        "Avaliar os aprendizados e resultados dessas experiências.",
        "Definir uma estratégia considerando os recursos disponíveis.",
        "Dividir o objetivo em tarefas menores e organizadas.",
        "Verificar riscos, limitações e permissões necessárias.",
        "Apresentar o plano para avaliação antes da execução."
    ]

    if not experiencias_relevantes:
        etapas[2] = (
            "Verificar se existem experiências anteriores relacionadas."
        )
        etapas[3] = (
            "Identificar conhecimentos e informações disponíveis."
        )

    return [
        {
            "numero": indice,
            "descricao": descricao,
            "status": "pendente"
        }
        for indice, descricao in enumerate(etapas, start=1)
    ]


def criar_plano(objetivo, experiencias=None, padroes=None):
    objetivo = normalizar_texto(objetivo)

    if not objetivo:
        return {
            "objetivo": "",
            "etapas": [],
            "experiencias_consultadas": [],
            "quantidade_experiencias": 0,
            "padroes_consultados": padroes or {},
            "status": "objetivo_vazio"
        }

    experiencias_relevantes = analisar_experiencias(
        objetivo,
        experiencias or []
    )

    etapas = criar_etapas(
        objetivo,
        experiencias_relevantes
    )

    return {
        "objetivo": objetivo,
        "etapas": etapas,
        "experiencias_consultadas": experiencias_relevantes,
        "quantidade_experiencias": len(experiencias_relevantes),
        "padroes_consultados": padroes or {},
        "status": "planejado"
    }


def exibir_plano(plano):
    print("\n===== PLANEJAMENTO DA LUCI =====")
    print("Objetivo:", plano.get("objetivo", ""))

    print("\nETAPAS:")

    for etapa in plano.get("etapas", []):
        print(
            f'{etapa["numero"]}. {etapa["descricao"]} '
            f'[{etapa["status"]}]'
        )

    experiencias = plano.get("experiencias_consultadas", [])

    print("\nEXPERIÊNCIAS CONSULTADAS:", len(experiencias))

    for experiencia in experiencias:
        print("\nExperiência:", experiencia.get("experiencia_id"))
        print("Situação:", experiencia.get("situacao"))
        print("Resultado:", experiencia.get("resultado"))
        print("Aprendizado:", experiencia.get("aprendizado"))
        print("Classificação:", experiencia.get("classificacao"))

    print("\nStatus:", plano.get("status"))
