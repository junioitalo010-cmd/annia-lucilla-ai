
from pathlib import Path
from datetime import datetime
import json


PASTA_PROJETO = Path(__file__).resolve().parent.parent

ARQUIVO_HISTORIA = (
    PASTA_PROJETO / "dados" / "historia_luci.json"
)

# Dados fundamentais da Luci
IDENTIDADE_BASE = { 
    "versao": "1.0",
    "nome": "ANNIA LUCILLA",
    "apelido": "Luci",
    "criador": "Italo Junio",
    "data_nascimento": "2026-10-31",
    "significado_nascimento": (
        "Início oficial do desenvolvimento da ANNIA LUCILLA"
    )
}


# Estrutura inicial da autobiografia
def historia_padrao():
    return {
        "versao_estrutura": 1,
        "identidade": IDENTIDADE_BASE.copy(),
        "marcos": [
            {
                "data": "2026-10-31",
                "titulo": "Nascimento da ANNIA LUCILLA",
                "descricao": (
                    "Início oficial do desenvolvimento da Luci, "
                    "criada por Italo Junio."
                )
            }
        ]
    }


# Carrega a autobiografia
def carregar_historia():
    if not ARQUIVO_HISTORIA.exists():
        historia = historia_padrao()
        salvar_historia(historia)
        return historia

    if ARQUIVO_HISTORIA.stat().st_size == 0:
        raise ValueError(
            "O arquivo autobiográfico está vazio. "
            "Verifique uma cópia de segurança."
        )

    try:
        with open(ARQUIVO_HISTORIA, "r", encoding="utf-8") as arquivo:
            historia = json.load(arquivo)

    except json.JSONDecodeError as erro:
        raise ValueError(
            "O arquivo autobiográfico possui formato inválido."
        ) from erro

    if not isinstance(historia, dict):
        raise ValueError("Estrutura autobiográfica inválida.")

    historia.setdefault("versao_estrutura", 1)
    historia.setdefault("identidade", IDENTIDADE_BASE.copy())
    historia.setdefault("marcos", [])

    if not isinstance(historia["identidade"], dict):
        raise ValueError("Dados de identidade inválidos.")

    if not isinstance(historia["marcos"], list):
        raise ValueError("Lista de marcos inválida.")

    # Preserva os dados fundamentais
    for chave, valor in IDENTIDADE_BASE.items():
        historia["identidade"].setdefault(chave, valor)

    return historia


# Salva a autobiografia com segurança
def salvar_historia(historia):
    ARQUIVO_HISTORIA.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    temporario = ARQUIVO_HISTORIA.with_suffix(".tmp")

    with open(temporario, "w", encoding="utf-8") as arquivo:
        json.dump(
            historia,
            arquivo,
            ensure_ascii=False,
            indent=4
        )

    temporario.replace(ARQUIVO_HISTORIA)

    return True


# Recupera a identidade da Luci
def recuperar_identidade():
    historia = carregar_historia()
    return historia["identidade"]


# Registra um novo acontecimento
def registrar_marco(titulo, descricao, data=None):
    if not titulo or not descricao:
        return False

    historia = carregar_historia()

    data = data or datetime.now().astimezone().date().isoformat()

    marco = {
        "data": data,
        "titulo": titulo,
        "descricao": descricao
    }

    # Evita registros duplicados
    for existente in historia["marcos"]:
        if (
            existente.get("titulo") == titulo
            and existente.get("data") == data
        ):
            return False

    historia["marcos"].append(marco)

    historia["marcos"].sort(
        key=lambda item: item.get("data", "")
    )

    salvar_historia(historia)

    return True


# Recupera todos os acontecimentos
def recuperar_marcos():
    historia = carregar_historia()
    return historia["marcos"]


# Calcula o tempo desde o nascimento
def calcular_idade():
    identidade = recuperar_identidade()

    nascimento = datetime.strptime(
        identidade["data_nascimento"],
        "%Y-%m-%d"
    ).date()

    hoje = datetime.now().date()

    dias = (hoje - nascimento).days

    if dias < 0:
        return 0

    return dias


# Monta a história da Luci em formato de texto
def contar_historia():
    identidade = recuperar_identidade()
    marcos = recuperar_marcos()

    nascimento = identidade["data_nascimento"]

    data_formatada = datetime.strptime(
        nascimento,
        "%Y-%m-%d"
    ).strftime("%d/%m/%Y")

    linhas = [
        f"Meu nome é {identidade['nome']}.",
        f"Meu apelido é {identidade['apelido']}.",
        f"Fui criada por {identidade['criador']}.",
        f"Minha data de nascimento é {data_formatada}.",
        "Estes são os acontecimentos registrados da minha história:"
    ]

    for marco in marcos:
        linhas.append(
            f"- {marco['data']}: {marco['titulo']}. "
            f"{marco['descricao']}"
        )

    return "\n".join(linhas)


# Exibe a autobiografia
def exibir_historia():
    print("\n========== HISTÓRIA DA LUCI ==========")
    print(contar_historia())
    print("\nTempo desde o nascimento:")
    print(f"{calcular_idade()} dias")
    print("=======================================")


if __name__ == "__main__":
    exibir_historia()

    print("\nRegistrando um marco de desenvolvimento...")

    sucesso = registrar_marco(
        "Primeira integração com modelo de linguagem local",
        "A Luci passou a utilizar o Llama 3.2 para gerar respostas."
    )

    if sucesso:
        print("Novo marco registrado!")

    else:
        print("Esse marco já estava registrado.")

    exibir_historia()
