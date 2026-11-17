
from pathlib import Path
import json
if __package__:
    from . import memoria_longa
else:
    # Preserva o inicializador historico por caminho direto.
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from cerebro import memoria_longa

PASTA_PROJETO = Path(__file__).resolve().parent.parent
ARQUIVO_MEMORIA = PASTA_PROJETO / "dados" / "memoria.json"


def carregar_memoria():
    if memoria_longa._persistencia is not None:
        return memoria_longa.carregar_memoria()
    if not ARQUIVO_MEMORIA.exists():
        return {
            "informacoes_usuario": {},
            "historico": []
        }

    with open(ARQUIVO_MEMORIA, "r", encoding="utf-8") as arquivo:
        return json.load(arquivo)


def salvar_memoria(memoria):
    if memoria_longa._persistencia is not None:
        return memoria_longa.salvar_memoria(memoria)
    ARQUIVO_MEMORIA.parent.mkdir(parents=True, exist_ok=True)

    with open(ARQUIVO_MEMORIA, "w", encoding="utf-8") as arquivo:
        json.dump(memoria, arquivo, ensure_ascii=False, indent=4)


def guardar_informacao(chave, valor):
    if memoria_longa._persistencia is not None:
        def alterar(memoria):
            memoria['informacoes_usuario'][chave] = valor
            return True
        return memoria_longa._atualizar_memoria(alterar, 'legado_guardar_informacao')
    memoria = carregar_memoria()
    memoria["informacoes_usuario"][chave] = valor
    salvar_memoria(memoria)
    return True


def recuperar_informacao(chave):
    memoria = carregar_memoria()
    return memoria["informacoes_usuario"].get(chave)


def guardar_historico(remetente, mensagem):
    if memoria_longa._persistencia is not None:
        def alterar(memoria):
            memoria['historico'].append({'remetente': remetente, 'mensagem': mensagem})
            memoria['historico'] = memoria['historico'][-100:]
        return memoria_longa._atualizar_memoria(alterar, 'legado_guardar_historico')
    memoria = carregar_memoria()

    memoria["historico"].append({
        "remetente": remetente,
        "mensagem": mensagem
    })

    memoria["historico"] = memoria["historico"][-100:]

    salvar_memoria(memoria)


if __name__ == "__main__":
    print("Iniciando teste da memória...")

    guardar_informacao("assunto_estudado", "Python")

    print("Informação salva!")

    assunto = recuperar_informacao("assunto_estudado")

    print("Assunto estudado:", assunto)
