
from pathlib import Path
from datetime import datetime
import py_compile

PASTA = Path(__file__).resolve().parent
VERIFICADOR = PASTA / "nucleo" / "verificador.py"
CONFIABILIDADE = PASTA / "nucleo" / "confiabilidade.py"

FUNCAO_MEMORIA = '''
def verificar_declaracao_pessoal(afirmacao):
    """
    Verifica se a resposta reproduz uma declaracao
    explicita do usuario sobre seu projeto favorito.

    Nao comprova a verdade externa da declaracao.
    """
    texto = normalizar(afirmacao).strip().rstrip(".!? ")

    padroes = (
        r"(?:voce (?:mencionou|disse|informou) que |voce me contou que )?"
        r"(?:seu|o seu|meu|o meu) projeto favorito e (?P<valor>.+)",
        r"(?:pelo que voce (?:disse|contou),? )?"
        r"(?:seu|o seu) projeto favorito (?:e|consiste em) (?P<valor>.+)",
    )

    valor_resposta = None

    for padrao in padroes:
        resultado = re.fullmatch(padrao, texto)
        if resultado:
            valor_resposta = resultado.group("valor").strip()
            break

    if not valor_resposta or len(valor_resposta) < 3:
        return None

    if re.search(r"\\b(?:nao|nunca|jamais)\\b", texto):
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

        encontrado = padrao_usuario.fullmatch(
            normalizar(mensagem).strip().rstrip(".!? ")
        )

        if not encontrado:
            continue

        valor_memoria = encontrado.group("valor").strip()

        if valor_resposta == valor_memoria:
            return {
                "origem": "historico_usuario",
                "estado": "declaracao_registrada",
                "campo": "projeto_favorito",
                "valor": valor_memoria,
                "observacao": (
                    "Comprova somente a declaracao do usuario."
                ),
            }

        return None

    return None


'''


def substituir_uma_vez(texto, antigo, novo, descricao):
    quantidade = texto.count(antigo)

    if quantidade != 1:
        raise RuntimeError(
            f"{descricao}: esperado 1 trecho, encontrado {quantidade}."
        )

    return texto.replace(antigo, novo, 1)


def preparar_verificador(texto):
    if "def verificar_declaracao_pessoal(" in texto:
        raise RuntimeError(
            "O verificador ja possui a correcao de memoria."
        )

    texto = substituir_uma_vez(
        texto,
        "from cerebro.avaliador_conhecimentos import comparar_afirmacoes",
        "from cerebro.avaliador_conhecimentos import comparar_afirmacoes\n"
        "from cerebro.memoria_longa import recuperar_historico",
        "Importacao da memoria"
    )

    texto = substituir_uma_vez(
        texto,
        "def analisar_afirmacao(",
        FUNCAO_MEMORIA + "def analisar_afirmacao(",
        "Funcao de verificacao pessoal"
    )

    marcador = (
        "    afirmacao_com_contexto = contextualizar_afirmacao_curta("
    )

    verificacao = '''    evidencia_pessoal = verificar_declaracao_pessoal(afirmacao)

    if evidencia_pessoal is not None:
        return {
            "id_afirmacao": indice,
            "texto": afirmacao,
            "classificacao": "apoio_declaracao_usuario",
            "quantidade_evidencias": 1,
            "evidencias": [evidencia_pessoal],
            "contradicoes": [],
            "divergencias_contextuais": [],
        }

'''

    texto = substituir_uma_vez(
        texto,
        marcador,
        verificacao + marcador,
        "Integracao da memoria"
    )

    texto = substituir_uma_vez(
        texto,
        '        "apoio_marcado_verificado": 0,',
        '        "apoio_marcado_verificado": 0,\n'
        '        "apoio_declaracao_usuario": 0,',
        "Classificacao da memoria"
    )

    return texto



def preparar_confiabilidade(texto):
    """
    Atualiza a confiabilidade somente quando necessario.
    Permite executar o instalador mesmo que a classificacao
    ja tenha sido adicionada anteriormente.
    """

    # Adiciona a classificacao somente se ainda nao existir.
    if '"apoio_declaracao_usuario": 0' not in texto:

        texto = substituir_uma_vez(
            texto,
            '        "apoio_marcado_verificado": 0,',
            '        "apoio_marcado_verificado": 0,\n'
            '        "apoio_declaracao_usuario": 0,',
            "Contagem de declaracoes"
        )

    # Verifica se a classificacao participa da decisao final.
    trecho_antigo = (
        '        + contagens["apoio_marcado_verificado"]\n'
        '        == quantidade'
    )

    trecho_corrigido = (
        '        + contagens["apoio_marcado_verificado"]\n'
        '        + contagens["apoio_declaracao_usuario"]\n'
        '        == quantidade'
    )

    if trecho_corrigido not in texto:

        texto = substituir_uma_vez(
            texto,
            trecho_antigo,
            trecho_corrigido,
            "Reconhecimento da declaracao"
        )

    return texto



def main():
    arquivos = {
        VERIFICADOR: preparar_verificador,
        CONFIABILIDADE: preparar_confiabilidade,
    }

    originais = {}
    corrigidos = {}

    for caminho, funcao in arquivos.items():
        if not caminho.is_file():
            raise FileNotFoundError(
                f"Arquivo nao encontrado: {caminho}"
            )

        original = caminho.read_text(encoding="utf-8")
        corrigido = funcao(original)

        compile(corrigido, str(caminho), "exec")

        originais[caminho] = original
        corrigidos[caminho] = corrigido

    identificador = datetime.now().strftime("%Y%m%d_%H%M%S")

    for caminho, original in originais.items():
        backup = caminho.with_name(
            caminho.stem + "_backup_" + identificador + ".py"
        )

        backup.write_text(original, encoding="utf-8")
        print(f"Backup criado: {backup.name}")

    for caminho, corrigido in corrigidos.items():
        caminho.write_text(corrigido, encoding="utf-8")
        print(f"Arquivo atualizado: {caminho.name}")

    for caminho in arquivos:
        py_compile.compile(str(caminho), doraise=True)

    print()
    print("CORRECAO APLICADA COM SUCESSO!")
    print("Os dois arquivos passaram na compilacao.")


if __name__ == "__main__":
    try:
        main()
    except Exception as erro:
        print(f"CORRECAO NAO CONCLUIDA: {erro}")
        raise

