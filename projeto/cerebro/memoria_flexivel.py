"""Memoria flexivel experimental: comandos explicitos, chaves limitadas e sem LLM."""
import re
import threading
import uuid
import unicodedata
from datetime import datetime, timezone
from .memoria_longa import guardar_informacao, recuperar_informacao, recuperar_todas_informacoes, esquecer_informacao

PREFIXO = 'mf02_registro_'
AUDITORIA = 'mf04_auditoria'
PENDENTES = {}
TRAVA = threading.RLock()
ATUALIZAR = re.compile(r'^Luci, atualize a informa[cç][aã]o de teste ([\w-]{2,40}):\s*(.{1,200})\.$', re.I | re.S)
EXCLUIR = re.compile(r'^Luci, exclua a informa[cç][aã]o de teste ([\w-]{2,40})\.$', re.I)
CONFIRMAR = re.compile(r'^Luci, confirme a opera[cç][aã]o ([a-f0-9]{8})\.$', re.I)
CANCELAR = re.compile(r'^Luci, cancele a opera[cç][aã]o ([a-f0-9]{8})\.$', re.I)

def _auditar(tipo, nome):
    # Auditoria minima: nao conserva o valor excluido ou substituido.
    registros = recuperar_informacao(AUDITORIA) or []
    if not isinstance(registros, list):
        return False
    novos = (registros + [{'operacao': tipo, 'registro': nome,
                            'data': datetime.now(timezone.utc).isoformat()}])[-100:]
    return bool(guardar_informacao(AUDITORIA, novos))

def _valor_seguro(nome, valor):
    if not isinstance(valor, str) or not 1 <= len(valor) <= 200 or any(c in valor for c in ('\x00', '\r', '\n')):
        return False
    bloqueios = ('senha', 'password', 'token', 'chave privada', 'identidade oficial', 'regra de seguranca', 'autenticacao')
    texto = _normalizar(nome + ' ' + valor)
    return not any(x in texto for x in bloqueios)

CHAVE_NOME = re.compile(r'^[a-z][a-z0-9_]{1,39}$')
GRAVAR = re.compile(r'^Luci, guarde a informa[cç][aã]o de teste ([\w-]{2,40}):\s*(.{1,200})\.$', re.I | re.S)
LER = re.compile(r'^Luci, consulte a informa[cç][aã]o de teste ([\w-]{2,40})\.$', re.I)

def _chave(nome):
    normal = unicodedata.normalize('NFKD', nome)
    normal = ''.join(c for c in normal if not unicodedata.combining(c)).lower().replace('-', '_')
    if not CHAVE_NOME.fullmatch(normal):
        return None
    return PREFIXO + normal

def _normalizar(texto):
    texto = unicodedata.normalize('NFKD', texto)
    return ''.join(c for c in texto if not unicodedata.combining(c)).lower()


def _consultar_contexto(texto):
    """MF-03 inicial: correspondencia conservadora por termos da chave.

    Nao usa LLM nem faz busca aproximada. So responde quando ha uma unica
    chave cujos termos aparecem na pergunta e ha indicio de consulta.
    """
    pergunta = _normalizar(texto).strip()
    if not pergunta.endswith('?'):
        return None
    if not re.search(r'\b(qual|quais|quanto|quanta|lembra|recorda)\b', pergunta):
        return None
    # Evita confundir perguntas sobre salvar/alterar com consultas.
    if re.search(r'\b(guarde|salve|altere|apague|esqueca|exclua)\b', pergunta):
        return None
    palavras = set(re.findall(r'[a-z0-9]+', pergunta))
    encontrados = []
    for chave, registro in recuperar_todas_informacoes().items():
        if not chave.startswith(PREFIXO) or not isinstance(registro, dict):
            continue
        if registro.get('origem') != 'declaracao_explicita_usuario':
            continue
        nome = chave[len(PREFIXO):]
        termos = [t for t in nome.split('_') if len(t) > 2]
        if len(termos) < 2 or not all(t in palavras for t in termos):
            continue
        encontrados.append((nome, registro))
    if len(encontrados) != 1:
        return None if not encontrados else 'Encontrei mais de um registro possivel. Consulte pelo nome exato.'
    nome, registro = encontrados[0]
    return (f'Voce me informou que {nome.replace("_", " ")} e {registro["valor"]}. '
            'Essa informacao esta registrada como declaracao sua, nao verificada externamente.')


def processar_comando(mensagem):
    texto = mensagem.strip()
    confirmar = CONFIRMAR.fullmatch(texto)
    cancelar = CANCELAR.fullmatch(texto)
    if confirmar or cancelar:
        codigo = (confirmar or cancelar).group(1).lower()
        with TRAVA:
            pendente = PENDENTES.pop(codigo, None)
            if not pendente:
                return 'Operacao inexistente ou ja encerrada. Nenhuma alteracao foi feita.'
            if cancelar:
                return 'Operacao cancelada. Nenhuma alteracao foi feita.'
            tipo, nome, anterior, novo = pendente
            chave = _chave(nome)
            atual = recuperar_informacao(chave)
            if atual != anterior:
                return 'O registro mudou desde a solicitacao. Nenhuma alteracao foi feita.'
            if tipo == 'atualizar':
                atualizado = dict(anterior)
                atualizado['valor'] = novo
                atualizado['atualizado_em'] = datetime.now(timezone.utc).isoformat()
                if not guardar_informacao(chave, atualizado) or recuperar_informacao(chave) != atualizado:
                    return 'Nao foi possivel confirmar a atualizacao.'
                auditado = _auditar('atualizacao', nome)
                return f'Informacao {nome} atualizada e conferida na memoria local.' + ('' if auditado else ' Aviso: auditoria nao confirmada.')
            if not esquecer_informacao(chave) or recuperar_informacao(chave) is not None:
                return 'Nao foi possivel confirmar a exclusao.'
            auditado = _auditar('exclusao', nome)
            return f'Informacao {nome} excluida e ausencia conferida na memoria local.' + ('' if auditado else ' Aviso: auditoria nao confirmada.')
    atualizar = ATUALIZAR.fullmatch(texto)
    excluir = EXCLUIR.fullmatch(texto)
    if atualizar or excluir:
        nome = (atualizar or excluir).group(1)
        chave = _chave(nome)
        if chave is None:
            return 'Nome de registro invalido.'
        anterior = recuperar_informacao(chave)
        if not isinstance(anterior, dict) or anterior.get('origem') != 'declaracao_explicita_usuario':
            return f'Nao encontrei a informacao de teste {nome}.'
        novo = atualizar.group(2).strip() if atualizar else None
        if atualizar and not _valor_seguro(nome, novo):
            return 'Essa informacao nao pode ser armazenada pelo comando de teste.'
        with TRAVA:
            codigo = uuid.uuid4().hex[:8]
            while codigo in PENDENTES:
                codigo = uuid.uuid4().hex[:8]
            PENDENTES[codigo] = ('atualizar' if atualizar else 'excluir', nome, anterior, novo)
        acao = 'atualizar' if atualizar else 'excluir'
        return (f'Pedido para {acao} {nome} recebido. Nenhuma alteracao foi feita. '
                f'Para confirmar, diga: Luci, confirme a operacao {codigo}. '
                f'Para cancelar, diga: Luci, cancele a operacao {codigo}.')
    gravar = GRAVAR.fullmatch(texto)
    if gravar:
        nome, valor = gravar.groups()
        chave = _chave(nome)
        if chave is None:
            return 'Nome de registro invalido.'
        valor = valor.strip()
        if any(c in valor for c in ('\x00', '\r', '\n')):
            return 'O registro deve ter uma unica linha.'
        # Dados sensiveis e mudancas de regras nao pertencem a este fluxo.
        bloqueios = ('senha', 'password', 'token', 'chave privada', 'identidade oficial', 'regra de seguranca', 'autenticacao')
        texto_seguro = unicodedata.normalize('NFKD', nome + ' ' + valor)
        texto_seguro = ''.join(c for c in texto_seguro if not unicodedata.combining(c)).lower()
        if any(x in texto_seguro for x in bloqueios):
            return 'Esse tipo de informacao nao pode ser salvo pelo comando de teste.'
        if recuperar_informacao(chave) is not None:
            return 'Ja existe um registro com esse nome. Nenhuma alteracao foi feita.'
        registro = {'valor': valor, 'origem': 'declaracao_explicita_usuario',
                    'estado': 'nao_verificado', 'registrado_em': datetime.now(timezone.utc).isoformat()}
        if not guardar_informacao(chave, registro):
            return 'Nao foi possivel confirmar a gravacao.'
        if recuperar_informacao(chave) != registro:
            return 'Nao foi possivel confirmar a leitura apos a gravacao.'
        return f'Informacao de teste {nome} salva e conferida na memoria local (declaracao nao verificada).'
    ler = LER.fullmatch(texto)
    if ler:
        nome = ler.group(1)
        chave = _chave(nome)
        if chave is None:
            return 'Nome de registro invalido.'
        registro = recuperar_informacao(chave)
        if not isinstance(registro, dict) or registro.get('origem') != 'declaracao_explicita_usuario':
            return f'Nao encontrei a informacao de teste {nome}.'
        return f'Informacao de teste {nome}: {registro["valor"]} (declaracao do usuario, nao verificada).'
    return _consultar_contexto(texto)
