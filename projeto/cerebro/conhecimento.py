 
from pathlib import Path
from datetime import datetime
import json
import unicodedata
import re


# ==========================================
# ANNIA LUCILLA AI
# Sistema de armazenamento de conhecimentos
# Versão da estrutura: 2
# ==========================================

PASTA_PROJETO = Path(__file__).resolve().parent.parent
ARQUIVO_CONHECIMENTOS = (
    PASTA_PROJETO / "dados" / "conhecimentos.json"
)

ESTADOS_VERIFICACAO = {
    "pendente",
    "verificado",
    "contestado"
}


def data_atual():
    return datetime.now().isoformat(timespec="seconds")


def estrutura_padrao():
    return {
        "versao": 2,
        "conhecimentos": []
    }


def normalizar(texto):
    texto = str(texto).lower().strip()
    texto = unicodedata.normalize("NFD", texto)

    return "".join(
        caractere
        for caractere in texto
        if unicodedata.category(caractere) != "Mn"
    )


def proximo_id(conhecimentos):
    ids = [
        registro.get("id", 0)
        for registro in conhecimentos
        if isinstance(registro.get("id"), int)
    ]

    return max(ids, default=0) + 1


# ==========================================
# MIGRAÇÃO E VALIDAÇÃO
# ==========================================

def migrar_registro(registro):
    if not isinstance(registro, dict):
        raise ValueError("Registro de conhecimento inválido.")

    obrigatorios = ("id", "assunto", "conteudo")

    for campo in obrigatorios:
        if campo not in registro:
            raise ValueError(
                f"Registro sem o campo obrigatório: {campo}"
            )

    registro.setdefault("origem", "Origem não informada")
    registro.setdefault("data_registro", data_atual())
    registro.setdefault("atualizacoes", 0)
    registro.setdefault("ultima_atualizacao", None)

    # Campos novos: registros antigos começam pendentes.
    registro.setdefault("fonte", None)
    registro.setdefault("estado_verificacao", "pendente")
    registro.setdefault("data_verificacao", None)
    registro.setdefault("justificativa_verificacao", None)
    registro.setdefault("historico_alteracoes", [])

    if registro["estado_verificacao"] not in ESTADOS_VERIFICACAO:
        registro["estado_verificacao"] = "pendente"

    if not isinstance(registro["historico_alteracoes"], list):
        registro["historico_alteracoes"] = []

    if not isinstance(registro["atualizacoes"], int):
        registro["atualizacoes"] = 0

    return registro


def validar_estrutura(dados):
    if not isinstance(dados, dict):
        raise ValueError("A base precisa ser um objeto JSON.")

    if not isinstance(dados.get("conhecimentos"), list):
        raise ValueError("Lista de conhecimentos inválida.")

    ids = set()

    for registro in dados["conhecimentos"]:
        migrar_registro(registro)

        identificador = registro["id"]

        if identificador in ids:
            raise ValueError("Existem identificadores duplicados.")

        ids.add(identificador)

        if not isinstance(registro["assunto"], str):
            raise ValueError("Assunto de conhecimento inválido.")

        if not isinstance(registro["conteudo"], str):
            raise ValueError("Conteúdo de conhecimento inválido.")

    dados["versao"] = 2

    return dados


# ==========================================
# CARREGAMENTO
# ==========================================

def carregar_conhecimentos():

    ARQUIVO_CONHECIMENTOS.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    if not ARQUIVO_CONHECIMENTOS.exists():
        dados = estrutura_padrao()
        salvar_conhecimentos(dados)
        return dados

    try:
        with open(
            ARQUIVO_CONHECIMENTOS,
            "r",
            encoding="utf-8"
        ) as arquivo:

            dados = json.load(arquivo)

        versao_anterior = dados.get("versao", 1)
        dados = validar_estrutura(dados)

        # Persiste a migração da estrutura antiga.
        if versao_anterior < 2:
            salvar_conhecimentos(dados)

        return dados

    except (json.JSONDecodeError, ValueError, TypeError) as erro:
        # Não substitui automaticamente uma base corrompida.
        raise RuntimeError(
            "A base de conhecimentos está inválida. "
            "O arquivo original foi preservado. "
            f"Detalhes: {erro}"
        ) from erro


# ==========================================
# SALVAMENTO
# ==========================================

def salvar_conhecimentos(dados):

    ARQUIVO_CONHECIMENTOS.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    dados = validar_estrutura(dados)

    arquivo_temporario = ARQUIVO_CONHECIMENTOS.with_suffix(".tmp")

    try:
        with open(
            arquivo_temporario,
            "w",
            encoding="utf-8"
        ) as arquivo:

            json.dump(
                dados,
                arquivo,
                ensure_ascii=False,
                indent=4
            )

            arquivo.flush()

        arquivo_temporario.replace(ARQUIVO_CONHECIMENTOS)

    except Exception:
        if arquivo_temporario.exists():
            arquivo_temporario.unlink()

        raise


# ==========================================
# REGISTRAR CONHECIMENTO
# ==========================================

def registrar_conhecimento(
    assunto,
    conteudo,
    origem="Conversa com o usuário",
    fonte=None,
    estado_verificacao="pendente"
):

    assunto = str(assunto).strip()
    conteudo = str(conteudo).strip()

    if not assunto or not conteudo:
        return False, "Assunto e conteúdo são obrigatórios."

    if estado_verificacao not in ESTADOS_VERIFICACAO:
        return False, "Estado de verificação inválido."

    dados = carregar_conhecimentos()

    for conhecimento in dados["conhecimentos"]:

        if normalizar(conhecimento["assunto"]) == normalizar(assunto):
            return False, "Esse assunto já está registrado."

    novo_conhecimento = {
        "id": proximo_id(dados["conhecimentos"]),
        "assunto": assunto,
        "conteudo": conteudo,
        "origem": origem,
        "fonte": fonte,
        "estado_verificacao": estado_verificacao,
        "data_registro": data_atual(),
        "data_verificacao": None,
        "justificativa_verificacao": None,
        "atualizacoes": 0,
        "ultima_atualizacao": None,
        "historico_alteracoes": []
    }

    dados["conhecimentos"].append(novo_conhecimento)

    salvar_conhecimentos(dados)

    return True, "Conhecimento registrado com sucesso!"


# ==========================================
# BUSCAR CONHECIMENTOS
# ==========================================

def buscar_conhecimentos(consulta):

    dados = carregar_conhecimentos()

    consulta_normalizada = normalizar(consulta)

    palavras_consulta = set(
        re.findall(r"[a-z0-9]+", consulta_normalizada)
    )

    if not palavras_consulta:
        return []

    resultados = []

    for conhecimento in dados["conhecimentos"]:

        assunto = normalizar(conhecimento["assunto"])
        conteudo = normalizar(conhecimento["conteudo"])

        texto_completo = assunto + " " + conteudo

        palavras_conhecimento = set(
            re.findall(r"[a-z0-9]+", texto_completo)
        )

        correspondencias = (
            palavras_consulta & palavras_conhecimento
        )

        if correspondencias:

            pontuacao = len(correspondencias)

            palavras_assunto = set(
                re.findall(r"[a-z0-9]+", assunto)
            )

            if palavras_consulta & palavras_assunto:
                pontuacao += 3

            resultados.append({
                "pontuacao": pontuacao,
                "conhecimento": conhecimento
            })

    resultados.sort(
        key=lambda item: item["pontuacao"],
        reverse=True
    )

    return [
        item["conhecimento"]
        for item in resultados
    ]


# ==========================================
# LISTAR CONHECIMENTOS
# ==========================================

def listar_conhecimentos():

    dados = carregar_conhecimentos()

    return dados["conhecimentos"]


# ==========================================
# ATUALIZAR CONHECIMENTO
# ==========================================

def atualizar_conhecimento(assunto, novo_conteudo):

    novo_conteudo = str(novo_conteudo).strip()

    if not novo_conteudo:
        return False, "O novo conteúdo não pode ficar vazio."

    dados = carregar_conhecimentos()

    for conhecimento in dados["conhecimentos"]:

        if normalizar(conhecimento["assunto"]) == normalizar(assunto):

            conhecimento["historico_alteracoes"].append({
                "conteudo_anterior": conhecimento["conteudo"],
                "data_alteracao": data_atual(),
                "estado_anterior": conhecimento["estado_verificacao"]
            })

            conhecimento["conteudo"] = novo_conteudo
            conhecimento["atualizacoes"] += 1
            conhecimento["ultima_atualizacao"] = data_atual()

            # Uma alteração exige nova verificação.
            conhecimento["estado_verificacao"] = "pendente"
            conhecimento["data_verificacao"] = None
            conhecimento["justificativa_verificacao"] = None

            salvar_conhecimentos(dados)

            return True, (
                "Conhecimento atualizado. "
                "Estado de verificação voltou para pendente."
            )

    return False, "Assunto não encontrado."


# ==========================================
# ALTERAR ESTADO DE VERIFICAÇÃO
# ==========================================

def alterar_estado_verificacao(
    assunto,
    novo_estado,
    justificativa="",
    fonte=None
):
    if novo_estado not in ESTADOS_VERIFICACAO:
        return False, "Estado de verificação inválido."

    justificativa = str(justificativa).strip()

    if novo_estado == "verificado":
        if not fonte or not str(fonte).strip():
            return False, (
                "Não é possível verificar um conhecimento "
                "sem informar uma fonte."
            )

        if not justificativa:
            return False, (
                "Informe a justificativa da verificação."
            )

    dados = carregar_conhecimentos()

    for conhecimento in dados["conhecimentos"]:

        if normalizar(conhecimento["assunto"]) == normalizar(assunto):

            estado_anterior = conhecimento["estado_verificacao"]

            conhecimento["estado_verificacao"] = novo_estado
            conhecimento["data_verificacao"] = data_atual()
            conhecimento["justificativa_verificacao"] = justificativa

            if fonte:
                conhecimento["fonte"] = fonte

            conhecimento["historico_alteracoes"].append({
                "tipo": "alteracao_verificacao",
                "estado_anterior": estado_anterior,
                "novo_estado": novo_estado,
                "justificativa": justificativa,
                "fonte": fonte,
                "data_alteracao": data_atual()
            })

            salvar_conhecimentos(dados)

            return True, "Estado de verificação atualizado."

    return False, "Assunto não encontrado."


# ==========================================
# ESTATÍSTICAS
# ==========================================

def contar_conhecimentos():

    dados = carregar_conhecimentos()

    return len(dados["conhecimentos"])


def contar_por_estado():

    dados = carregar_conhecimentos()

    resultado = {
        "pendente": 0,
        "verificado": 0,
        "contestado": 0
    }

    for conhecimento in dados["conhecimentos"]:

        estado = conhecimento["estado_verificacao"]

        if estado in resultado:
            resultado[estado] += 1

    return resultado


# ==========================================
# EXIBIR BASE DE CONHECIMENTOS
# ==========================================

def exibir_conhecimentos():

    conhecimentos = listar_conhecimentos()

    print("\n========== ANNIA LUCILLA ==========")
    print("       BASE DE CONHECIMENTOS")
    print("===================================")

    if not conhecimentos:
        print("\nNenhum conhecimento registrado.")
        return

    for conhecimento in conhecimentos:

        print(f"\nID: {conhecimento['id']}")
        print(f"Assunto: {conhecimento['assunto']}")
        print(f"Conteúdo: {conhecimento['conteudo']}")
        print(f"Origem: {conhecimento['origem']}")
        print(f"Fonte: {conhecimento['fonte']}")
        print(
            "Verificação:",
            conhecimento["estado_verificacao"]
        )
        print(f"Data: {conhecimento['data_registro']}")
        print(
            "Atualizações:",
            conhecimento["atualizacoes"]
        )

    print("\nTotal:", len(conhecimentos))


# ==========================================
# TESTE DO MÓDULO
# ==========================================

if __name__ == "__main__":

    carregar_conhecimentos()

    print("\nSistema de conhecimentos iniciado!")

    exibir_conhecimentos()

    print("\nTESTE DE RECUPERAÇÃO DA LUCI")

    consultas = [
        "O que é Python?",
        "O que você sabe sobre Python?",
        "Me explique Python.",
        "Para que serve Python?"
    ]

    for consulta in consultas:

        print("\nPergunta:", consulta)

        resultados = buscar_conhecimentos(consulta) 
        

        if resultados:

            for resultado in resultados:
                print("Encontrado:", resultado["assunto"])
                print("Conteúdo:", resultado["conteudo"])
                print(
                    "Verificação:",
                    resultado["estado_verificacao"]
                )

        else:
            print("Nenhum conhecimento encontrado.")

    print("\nESTATÍSTICAS:")
    print(contar_por_estado())
    
def buscar_conhecimentos_verificados(consulta):
    resultados = buscar_conhecimentos(consulta)

    return [
        conhecimento
        for conhecimento in resultados
        if conhecimento.get("estado_verificacao") == "verificado"
    ]