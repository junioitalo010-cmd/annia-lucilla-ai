"""Adaptador transacional experimental. Importacao explicita, sem escrita dupla.

Esquema de transicao: documento v3 integral e revisoes, nao indice semantico.
Cada operacao abre sua conexao; BEGIN IMMEDIATE serializa read-modify-write.
"""
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import sqlite3


class ConflitoMemoria(RuntimeError):
    """Snapshot desatualizado; o chamador deve reler e refazer a operacao."""


class Snapshot(dict):
    def __init__(self, dados, revisao, banco):
        super().__init__(dados)
        self.revisao = revisao
        self.banco = banco


def validar(dados):
    if not isinstance(dados, dict):
        raise ValueError('Memoria deve ser objeto JSON.')
    result = dict(dados)
    result.setdefault('versao', 3)
    if type(result['versao']) is not int or result['versao'] != 3:
        raise ValueError('Versao de memoria nao suportada; nenhuma conversao automatica.')
    for key, kind, default in [('informacoes_usuario', dict, {}),
                                ('historico', list, []), ('resumos', list, [])]:
        result.setdefault(key, default)
        if not isinstance(result[key], kind):
            raise ValueError('Tipo invalido em ' + key + '; importacao interrompida.')
    # Rejeita valores fora de JSON estrito; nao altera textos/campos desconhecidos.
    return json.loads(json.dumps(result, ensure_ascii=False, allow_nan=False))


def agora():
    return datetime.now(timezone.utc).isoformat()


class MemoriaSQLite:
    def __init__(self, caminho):
        self.caminho = Path(caminho).resolve()
        if not self.caminho.is_file():
            raise FileNotFoundError('Banco nao existe; importe explicitamente um JSON.')
        with self._conexao() as conn:
            if conn.execute('PRAGMA user_version').fetchone()[0] != 1:
                raise ValueError('Esquema SQLite nao suportado.')
            row = conn.execute('SELECT payload FROM memoria WHERE id=1').fetchone()
            if row is None:
                raise ValueError('Memoria ausente no banco.')
            validar(json.loads(row[0]))

    @contextmanager
    def _conexao(self):
        # mode=rw nao cria banco vazio caso arquivo desapareca.
        conn = sqlite3.connect(self.caminho.as_uri() + '?mode=rw', uri=True,
                               timeout=10, isolation_level=None)
        try:
            conn.execute('PRAGMA synchronous=FULL')
            yield conn
        finally:
            conn.close()

    @classmethod
    def importar_json(cls, origem, destino):
        origem, destino = Path(origem).resolve(), Path(destino).resolve()
        raw = origem.read_bytes()
        dados = validar(json.loads(raw.decode('utf-8-sig')))
        payload = json.dumps(dados, ensure_ascii=False, allow_nan=False)
        destino.parent.mkdir(parents=True, exist_ok=True)
        # Reserva exclusiva: nunca sobrescrever banco, JSON ou outra candidata.
        with destino.open('xb'):
            pass
        conn = sqlite3.connect(destino, isolation_level=None)
        try:
            conn.execute('BEGIN IMMEDIATE')
            conn.execute('CREATE TABLE memoria (id INTEGER PRIMARY KEY CHECK(id=1), revisao INTEGER NOT NULL, payload TEXT NOT NULL)')
            conn.execute('CREATE TABLE revisoes (revisao INTEGER PRIMARY KEY, operacao TEXT NOT NULL, observado_em TEXT NOT NULL, payload TEXT NOT NULL)')
            conn.execute('CREATE TABLE origem (sha256 TEXT NOT NULL, formato TEXT NOT NULL)')
            conn.execute('INSERT INTO memoria VALUES (1,0,?)', (payload,))
            conn.execute('INSERT INTO revisoes VALUES (0,?,?,?)', ('importacao', agora(), payload))
            conn.execute('INSERT INTO origem VALUES (?,?)', (hashlib.sha256(raw).hexdigest(), 'json-v3'))
            conn.execute('PRAGMA user_version=1')
            conn.execute('COMMIT')
        except Exception:
            if conn.in_transaction:
                conn.execute('ROLLBACK')
            # Preserva artefato com falha para diagnostico; nunca tenta recriar.
            raise
        finally:
            conn.close()
        return cls(destino)

    def ler(self):
        with self._conexao() as conn:
            rev, raw = conn.execute('SELECT revisao,payload FROM memoria WHERE id=1').fetchone()
            return Snapshot(validar(json.loads(raw)), rev, str(self.caminho))

    def _gravar(self, conn, dados, revisao, operacao):
        payload = json.dumps(validar(dados), ensure_ascii=False, allow_nan=False)
        conn.execute('UPDATE memoria SET revisao=?,payload=? WHERE id=1', (revisao, payload))
        conn.execute('INSERT INTO revisoes VALUES (?,?,?,?)',
                     (revisao, operacao, agora(), payload))

    def atualizar(self, mutacao, operacao):
        """Callback interno sem I/O externo; qualquer excecao desfaz tudo."""
        with self._conexao() as conn:
            conn.execute('BEGIN IMMEDIATE')
            try:
                rev, raw = conn.execute('SELECT revisao,payload FROM memoria WHERE id=1').fetchone()
                dados = validar(json.loads(raw))
                resultado = mutacao(dados)
                self._gravar(conn, dados, rev + 1, operacao)
                conn.execute('COMMIT')
                return resultado
            except Exception:
                conn.execute('ROLLBACK')
                raise

    def salvar(self, snapshot):
        if not isinstance(snapshot, Snapshot) or snapshot.banco != str(self.caminho):
            raise ConflitoMemoria('Gravacao integral exige snapshot deste banco.')
        with self._conexao() as conn:
            conn.execute('BEGIN IMMEDIATE')
            try:
                rev = conn.execute('SELECT revisao FROM memoria WHERE id=1').fetchone()[0]
                if rev != snapshot.revisao:
                    raise ConflitoMemoria('Memoria mudou; releia antes de salvar.')
                self._gravar(conn, snapshot, rev + 1, 'salvar_snapshot')
                conn.execute('COMMIT')
            except Exception:
                conn.execute('ROLLBACK')
                raise
        return True

    def exportar_json(self, destino):
        # Snapshot consistente; destino novo, nao substitui JSON de origem.
        dados = self.ler()
        with Path(destino).open('x', encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False, indent=4, allow_nan=False)

    @staticmethod
    def _plano_retencao(conn, banco, manter):
        if type(manter) is not int or not 1 <= manter <= 10000:
            raise ValueError('Quantidade de revisoes deve estar entre 1 e 10000.')
        rev = conn.execute('SELECT revisao FROM memoria WHERE id=1').fetchone()[0]
        antigas = [r[0] for r in conn.execute(
            'SELECT revisao FROM revisoes ORDER BY revisao DESC LIMIT -1 OFFSET ?', (manter,))]
        if rev in antigas:
            raise ValueError('Historico inconsistente: revisao atual seria removida.')
        return {'banco': banco, 'revisao_atual': rev, 'manter': manter,
                'revisoes_a_remover': antigas}

    def planejar_retencao(self, manter):
        """Somente leitura. Nao define politica automatica nem concede permissao."""
        with self._conexao() as conn:
            conn.execute('BEGIN')
            try:
                plano = self._plano_retencao(conn, str(self.caminho), manter)
                conn.execute('COMMIT')
                return plano
            except Exception:
                conn.execute('ROLLBACK')
                raise

    def aplicar_retencao(self, plano):
        """Manutencao interna, a chamar apenas apos autorizacao externa.

        Plano nao e credencial. Nenhum endpoint/chat chama este metodo.
        Remove revisoes logicamente; nao promete apagar disco ou backups.
        """
        if not isinstance(plano, dict):
            raise ValueError('Plano de retencao invalido.')
        with self._conexao() as conn:
            conn.execute('BEGIN IMMEDIATE')
            try:
                atual = self._plano_retencao(conn, str(self.caminho), plano.get('manter'))
                if atual != plano:
                    raise ConflitoMemoria('Plano mudou; gere e revise um novo plano.')
                conn.executemany('DELETE FROM revisoes WHERE revisao=?',
                                 [(rev,) for rev in atual['revisoes_a_remover']])
                # Registro de manutencao sem copiar conteudo pessoal eliminado.
                conn.execute('CREATE TABLE IF NOT EXISTS manutencoes ('
                             'id INTEGER PRIMARY KEY, observado_em TEXT NOT NULL, '
                             'operacao TEXT NOT NULL, revisao_atual INTEGER NOT NULL, '
                             'removidas INTEGER NOT NULL, manter INTEGER NOT NULL)')
                conn.execute('INSERT INTO manutencoes '
                             '(observado_em,operacao,revisao_atual,removidas,manter) '
                             'VALUES (?,?,?,?,?)',
                             (agora(), 'retencao_logica', atual['revisao_atual'],
                              len(atual['revisoes_a_remover']), atual['manter']))
                conn.execute('COMMIT')
                return len(atual['revisoes_a_remover'])
            except Exception:
                conn.execute('ROLLBACK')
                raise
