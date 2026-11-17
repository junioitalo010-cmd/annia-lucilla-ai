"""Entrada opt-in da candidata. Nao altera a inicializacao do original."""
from contextlib import asynccontextmanager
from pathlib import Path
import os
import sys


def criar_app():
    if 'plataforma.app' in sys.modules:
        raise RuntimeError('Inicie em processo novo; nao alternar armazenamento em uso.')
    raiz = Path(__file__).resolve().parent.parent
    configured = os.environ.get('LUCI_CANDIDATA_SQLITE')
    if not configured:
        raise RuntimeError('Defina explicitamente LUCI_CANDIDATA_SQLITE.')
    banco = Path(configured).resolve()
    if not banco.is_relative_to(raiz / 'dados'):
        raise ValueError('Banco deve ficar nos dados desta candidata.')
    from cerebro import memoria_longa
    # Falha fecha a inicializacao. Nunca cria banco ou retorna ao JSON em silencio.
    memoria_longa.configurar_persistencia_sqlite(banco)
    from .app import app, nucleo

    @asynccontextmanager
    async def ciclo_vida_sqlite(app):
        if not nucleo.iniciar():
            nucleo.encerrar()
            raise RuntimeError('Nucleo da candidata nao inicializado.')
        try:
            yield
        finally:
            nucleo.encerrar()

    app.router.lifespan_context = ciclo_vida_sqlite
    return app
