"""Consulta explícita e somente-leitura às revisões já existentes; sem modelo."""
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
import unicodedata

MAX_REVISOES = 10000
MAX_BYTES = 64 * 1024 * 1024
MAX_MENSAGENS = 100000
PREFIXO = 'consultar conversas antigas'
AJUDA = 'Use consultar conversas antigas: seguido de um termo de 2 a 80 caracteres (letras, números, espaços, hífen ou sublinhado).'
INDISPONIVEL = 'O arquivo de conversas está indisponível, incompleto ou excede o limite de consulta. Nenhuma busca completa foi confirmada.'


def normalizar(texto):
    return ''.join(c for c in unicodedata.normalize('NFD', texto.casefold()) if not unicodedata.combining(c))


def interpretar(mensagem):
    if not isinstance(mensagem, str):
        return None
    head, sep, termo = mensagem.partition(':')
    if normalizar(head.strip()) != PREFIXO or not sep:
        return None
    termo = termo.strip()
    valido = (len(mensagem) <= 140 and 2 <= len(termo) <= 80
              and all(c.isalnum() or c in ' _-' for c in termo)
              and any(c.isalnum() for c in termo))
    return termo if valido else ''


def ler_arquivo(caminho):
    """Não cria banco, índice ou tabelas; falha se a cadeia não for reconstituível."""
    if caminho is None:
        raise ValueError('Backend SQLite ausente.')
    with closing(sqlite3.connect(Path(caminho).resolve().as_uri() + '?mode=ro', uri=True, timeout=3)) as conn:
        conn.execute('PRAGMA query_only=ON')
        conn.execute('BEGIN')
        if conn.execute('PRAGMA user_version').fetchone()[0] != 1:
            raise ValueError('Esquema não suportado.')
        atual, raw_atual = conn.execute('SELECT revisao,payload FROM memoria WHERE id=1').fetchone()
        total, tamanho = conn.execute('SELECT COUNT(*),SUM(length(CAST(payload AS BLOB))) FROM revisoes').fetchone()
        if not total or total > MAX_REVISOES or tamanho > MAX_BYTES:
            raise ValueError('Limite de leitura excedido.')
        stream = []
        anterior = None
        ultima = -1
        for rev, operacao, raw in conn.execute('SELECT revisao,operacao,payload FROM revisoes ORDER BY revisao'):
            if type(rev) is not int or rev != ultima + 1:
                raise ValueError('Revisões ausentes.')
            dados = json.loads(raw)
            history = dados['historico']
            if dados.get('versao') != 3 or not isinstance(history, list) or len(history) > 200:
                raise ValueError('Histórico não suportado.')
            if any(not isinstance(r, dict) or r.get('remetente') not in {'usuario', 'luci'}
                   or not isinstance(r.get('mensagem'), str) for r in history):
                raise ValueError('Registro inválido.')
            if anterior is None:
                if operacao != 'importacao':
                    raise ValueError('Origem ausente.')
                stream = [{'registro': r, 'revisao_origem': rev} for r in history]
            elif operacao == 'guardar_historico':
                if not history or history != (anterior + [history[-1]])[-200:]:
                    raise ValueError('Acréscimo inconsistente.')
                # Preserva repetições idênticas; não deduplica por texto ou data.
                stream.append({'registro': history[-1], 'revisao_origem': rev})
            elif history != anterior:
                raise ValueError('Alteração de histórico não reconstituível.')
            if len(stream) > MAX_MENSAGENS:
                raise ValueError('Limite de mensagens excedido.')
            anterior, ultima = history, rev
        if ultima != atual or anterior != json.loads(raw_atual)['historico']:
            raise ValueError('Revisão ativa divergente.')
        conn.execute('COMMIT')
    return stream


def _trecho(texto, termo):
    normalizado = []
    indices = []
    for i, c in enumerate(texto):
        for letter in normalizar(c):
            normalizado.append(letter)
            indices.append(i)
    pos = ''.join(normalizado).find(normalizar(termo))
    if pos < 0:
        return None
    inicio = max(0, indices[pos] - 100)
    fim = min(len(texto), indices[pos + len(normalizar(termo)) - 1] + 121)
    return inicio, fim, texto[inicio:fim]


def preparar(mensagem):
    termo = interpretar(mensagem)
    if termo is None:
        return None
    if not termo:
        return {'resposta': AJUDA, 'estado': 'formato_invalido', 'registros': []}
    try:
        from cerebro.memoria_longa import caminho_arquivo_conversas
        arquivo = ler_arquivo(caminho_arquivo_conversas())
    except (OSError, sqlite3.Error, ValueError, TypeError, KeyError):
        return {'resposta': INDISPONIVEL, 'estado': 'arquivo_indisponivel', 'registros': []}
    encontrados = []
    for index in range(len(arquivo) - 1, -1, -1):
        item = arquivo[index]
        row = item['registro']
        if row['remetente'] != 'usuario' or interpretar(row['mensagem']) is not None:
            continue
        trecho = _trecho(row['mensagem'], termo)
        if trecho is None:
            continue
        inicio, fim, texto = trecho
        encontrados.append({'indice_arquivo': index, 'revisao_origem': item['revisao_origem'],
                            'inicio': inicio, 'fim': fim, 'trecho': texto,
                            'sha256_mensagem': hashlib.sha256(row['mensagem'].encode()).hexdigest()})
        if len(encontrados) == 3:
            break
    if not encontrados:
        return {'resposta': 'Não encontrei esse termo nas suas mensagens no arquivo consultado.',
                'estado': 'sem_correspondencia', 'registros': []}
    partes = ['Consulta ao arquivo de conversas — trechos de mensagens suas, dos mais recentes para os mais antigos.',
              'São registros históricos; não confirmam fatos externos, preferências atuais nem ações executadas.']
    for row in encontrados:
        partes.append('Revisão ' + str(row['revisao_origem']) + ', mensagem ' + str(row['indice_arquivo'])
                      + ', trecho: ' + json.dumps(row['trecho'], ensure_ascii=False))
    return {'resposta': '\n\n'.join(partes), 'estado': 'trechos_historicos_atribuidos', 'registros': encontrados}


def responder(mensagem):
    item = preparar(mensagem)
    return item['resposta'] if item is not None else None


def diagnostico(mensagem, resposta):
    item = preparar(mensagem)
    if item is None:
        return None
    confere = isinstance(resposta, str) and resposta == item['resposta']
    return {'nivel': 'arquivo_conversas_conferido' if confere else 'arquivo_conversas_divergente',
            'bloquear_resposta': not confere, 'verificacao_independente': False,
            'quantidade_afirmacoes': 0, 'afirmacoes_analisadas': [],
            'estado_arquivo': item['estado'], 'registros_arquivo': item['registros'] if confere else [],
            'descricao': 'Conferência exata de trechos históricos; nenhuma pesquisa, geração ou execução de comandos.'}
