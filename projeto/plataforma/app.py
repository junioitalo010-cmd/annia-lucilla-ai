
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool

from nucleo.central import NucleoCentral


DIRETORIO = Path(__file__).resolve().parent
ARQUIVO_INTERFACE = DIRETORIO / "templates" / "v25_integrada.html"

# Uma única instância do núcleo para toda a plataforma.
nucleo = NucleoCentral()


@asynccontextmanager
async def ciclo_vida(app: FastAPI):
    """
    Inicializa o núcleo quando o servidor inicia
    e o encerra quando o servidor é desligado.
    """
    nucleo.iniciar()

    yield

    nucleo.encerrar()


app = FastAPI(
    title="ANNIA LUCILLA",
    description="Plataforma local de interação com ANNIA LUCILLA.",
    version="1.1",
    lifespan=ciclo_vida
)

app.mount(
    "/static",
    StaticFiles(directory=str(DIRETORIO / "static")),
    name="static"
)


@app.get("/", include_in_schema=False)
def pagina_inicial():
    return FileResponse(ARQUIVO_INTERFACE)


@app.get("/api/estado")
def consultar_estado():
    """
    Retorna o estado atual do núcleo.
    """
    try:
        return nucleo.recuperar_estado()

    except Exception:
        return {
            "nome": "ANNIA LUCILLA",
            "versao": "1.1",
            "ativo": False,
            "estado": "erro_ao_consultar"
        }


def politica_atual():
    motor=getattr(getattr(nucleo,'coordenador',None),'raciocinio',None)
    meta=getattr(motor,'ultima_politica_resposta',None)
    return dict(meta) if isinstance(meta,dict) else None


def resumo_documental():
    resultado=nucleo.recuperar_verificacao()
    if not isinstance(resultado,dict) or 'estado_consulta' not in resultado:return None
    return {k:resultado.get(k) for k in ('estado_consulta','quantidade_registros','registros_documentais','verificacao_independente')}


@app.get("/api/diagnostico")
def consultar_diagnostico():
    """Resumo da ultima verificacao; nao inclui prompts ou dados pessoais."""
    def resumir(resultado):
        if not isinstance(resultado, dict):
            return {"disponivel": False}
        return {
            "disponivel": True,
            "nivel": resultado.get("nivel"),
            "bloquear_resposta": resultado.get("bloquear_resposta"),
            "quantidade_afirmacoes": resultado.get("quantidade_afirmacoes"),
        }

    return {
        "verificacao": resumir(nucleo.recuperar_verificacao()),
        "confiabilidade": resumir(nucleo.recuperar_confiabilidade()),
        "politica_resposta": politica_atual(),
        "consulta_documental": resumo_documental(),
    }


@app.websocket("/ws")
async def canal_conversa(websocket: WebSocket):
    """
    Canal de comunicação em tempo real com a Luci.
    """

    await websocket.accept()

    try:
        while True:
            dados = await websocket.receive_json()

            if not isinstance(dados, dict):
                await websocket.send_json({
                    "tipo": "erro",
                    "mensagem": "Formato de mensagem inválido."
                })
                continue

            mensagem = dados.get("mensagem")

            if not isinstance(mensagem, str):
                await websocket.send_json({
                    "tipo": "erro",
                    "mensagem": "A mensagem precisa ser um texto."
                })
                continue

            mensagem = mensagem.strip()

            if not mensagem:
                await websocket.send_json({
                    "tipo": "erro",
                    "mensagem": "Digite uma mensagem."
                })
                continue

            if len(mensagem) > 10000:
                await websocket.send_json({
                    "tipo": "erro",
                    "mensagem": "A mensagem ultrapassa o limite de 10.000 caracteres."
                })
                continue

            # O processamento é síncrono. Executá-lo na thread pool
            # evita bloquear o ciclo assíncrono do servidor.
            resposta = await run_in_threadpool(
                nucleo.processar,
                mensagem
            )

            await websocket.send_json({
                "tipo": "resposta",
                "mensagem": resposta,
                "politica_resposta": politica_atual()
            })

    except WebSocketDisconnect:
        pass

    except Exception:
        try:
            await websocket.send_json({
                "tipo": "erro",
                "mensagem": "Não foi possível processar a comunicação."
            })
        except Exception:
            pass
