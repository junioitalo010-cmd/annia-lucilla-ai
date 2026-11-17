"""MF-05: manutencao offline conservadora da memoria SQLite (sem sobrescrita)."""
import argparse
import hashlib
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from cerebro.persistencia_sqlite import validar


def verificar(path):
    path = Path(path).resolve()
    if not path.is_file():
        raise FileNotFoundError('Banco nao encontrado.')
    con = sqlite3.connect(path.as_uri() + '?mode=ro', uri=True)
    try:
        check = con.execute('PRAGMA integrity_check').fetchone()[0]
        if check != 'ok':
            raise ValueError('Falha na integridade SQLite.')
        if con.execute('PRAGMA user_version').fetchone()[0] != 1:
            raise ValueError('Esquema desconhecido.')
        rev, raw = con.execute('SELECT revisao, payload FROM memoria WHERE id=1').fetchone()
        validar(json.loads(raw))
        rows = con.execute('SELECT revisao, operacao, observado_em, payload FROM revisoes ORDER BY revisao').fetchall()
        if not rows or rows[-1][0] != rev or rows[-1][3] != raw:
            raise ValueError('Ultima revisao difere da memoria atual.')
        if [r[0] for r in rows] != list(range(rev + 1)):
            raise ValueError('Sequencia de revisoes inconsistente.')
        for _, _, _, payload in rows:
            validar(json.loads(payload))
        return {'integridade': 'ok', 'esquema': 1, 'revisao_atual': rev, 'total_revisoes': len(rows), 'auditoria_tecnica': 'revisoes integrais presentes'}
    finally:
        con.close()


def backup(origem, destino):
    origem, destino = Path(origem).resolve(), Path(destino).resolve()
    if destino.exists():
        raise FileExistsError('Destino ja existe; nao sobrescrever.')
    verificar(origem)
    destino.parent.mkdir(parents=True, exist_ok=True)
    # Reserva o nome para evitar sobrescrita acidental.
    with destino.open('xb'):
        pass
    try:
        src = sqlite3.connect(origem.as_uri() + '?mode=ro', uri=True)
        try:
            dst = sqlite3.connect(destino)
            try:
                src.backup(dst)
            finally:
                dst.close()
        finally:
            src.close()
        verificar(destino)
        digest = hashlib.sha256(destino.read_bytes()).hexdigest()
        return {'backup': 'criado_e_verificado', 'sha256': digest, 'destino': str(destino)}
    except Exception:
        destino.unlink(missing_ok=True)
        raise


def restaurar_para_candidato(origem, destino):
    # Restaura SOMENTE para novo arquivo. Nunca substitui o banco ativo.
    resultado = backup(origem, destino)
    resultado['restauracao'] = 'copia_isolada; ativacao_manual_nao_executada'
    return resultado


def main():
    p = argparse.ArgumentParser(description='MF-05: integridade, backup e restauracao isolada (servidor desligado).')
    p.add_argument('acao', choices=['verificar', 'backup', 'restaurar-copia'])
    p.add_argument('origem', help='Caminho do SQLite de origem')
    p.add_argument('destino', nargs='?', help='Novo arquivo de destino (obrigatorio para copia)')
    a = p.parse_args()
    try:
        if a.acao == 'verificar':
            r = verificar(a.origem)
        else:
            if not a.destino:
                p.error('Informe um novo caminho de destino.')
            r = backup(a.origem, a.destino) if a.acao == 'backup' else restaurar_para_candidato(a.origem, a.destino)
        print(json.dumps(r, ensure_ascii=False, indent=2))
    except (OSError, ValueError, sqlite3.Error, json.JSONDecodeError) as e:
        print(json.dumps({'estado': 'falha', 'motivo': str(e)}, ensure_ascii=False))
        raise SystemExit(1)

if __name__ == '__main__':
    main()
