
from pathlib import Path
import ast
import shutil
from datetime import datetime

arquivo = Path(__file__).resolve().parent / "nucleo" / "verificador.py"

if not arquivo.exists():
    raise SystemExit(f"Arquivo nao encontrado: {arquivo}")

texto = arquivo.read_text(encoding="utf-8")

inicio = texto.find("def verificar_declaracao_pessoal(")
fim = texto.find("\ndef analisar_afirmacao(", inicio)

if inicio < 0 or fim < 0:
    raise SystemExit(
        "Funcoes esperadas nao encontradas. Nenhum arquivo foi alterado."
    )

nova_funcao = '''
def verificar_declaracao_pessoal(afirmacao):
    """
    Reconhece somente uma declaracao pessoal completa e sustentada.

    Nao valida frases compostas nem afirmacoes externas.
    """
    texto = normalizar(afirmacao).strip().rstrip(".!? ")
    texto = re.sub(r"\\s+", " ", texto)

    if re.search(r"\\b(?:nao|nunca|jamais)\\b", texto):
        return None

    if re.search(
        r"[,;:]|\\b(?:mas|porem|entretanto|alem disso|porque|pois)\\b",
        texto
    ):
        return None

    prefixo = (
        r"(?:ate o momento,? )?"
        r"(?:voce (?:mencionou|disse|informou) que |"
        r"voce me contou que |"
        r"pelo que voce (?:disse|contou),? )?"
    )

    padrao = (
        prefixo
        + r"(?:seu|o seu) projeto favorito "
        + r"(?:e|consiste em) (?P<valor>.+)"
    )

    resultado = re.fullmatch(padrao, texto)

    if resultado is None:
        return None

    valor_resposta = resultado.group("valor").strip()

    if not valor_resposta or len(valor_resposta) < 3:
        return None

    try:
        historico = recuperar_historico(limite=50)
    except (OSError, ValueError, TypeError, KeyError):
        return None

    if not isinstance(historico, list):
        return None

    padrao_usuario = re.compile(
        r"(?:o )?meu projeto favorito e (?P<valor>.+)"
    )

    for registro in reversed(historico):
        if not isinstance(registro, dict):
            continue

        if registro.get("remetente") != "usuario":
            continue

        mensagem = registro.get("mensagem")

        if not isinstance(mensagem, str):
            continue

        mensagem = re.sub(
            r"\\s+",
            " ",
            normalizar(mensagem).strip().rstrip(".!? ")
        )

        encontrado = padrao_usuario.fullmatch(mensagem)

        if encontrado is None:
            continue

        valor_memoria = encontrado.group("valor").strip()

        if valor_resposta != valor_memoria:
            return None

        return {
            "origem": "historico_usuario",
            "estado": "declaracao_registrada",
            "campo": "projeto_favorito",
            "valor": valor_memoria,
            "observacao": (
                "Confirma apenas o que o usuario declarou."
            ),
        }

    return None


'''

novo_texto = texto[:inicio] + nova_funcao + texto[fim:]

# Verifica a sintaxe antes de alterar o arquivo.
ast.parse(novo_texto, filename=str(arquivo))

backup = arquivo.with_name(
    f"verificador_backup_memoria_{datetime.now():%Y%m%d_%H%M%S}.py"
)

shutil.copy2(arquivo, backup)

arquivo.write_text(novo_texto, encoding="utf-8")

print("Backup:", backup.name)
print("Verificador atualizado. Sintaxe validada.")
print("Agora execute: python -m py_compile nucleo/verificador.py")
