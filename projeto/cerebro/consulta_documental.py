"""Consulta explícita de registros locais; confere transcrição, não verdade."""
import hashlib
import json
import re
from pathlib import Path
from cerebro.foco_conversa import normalizar

ARQUIVO=Path(__file__).with_name('referencias_python.json')
SHA256_CATALOGO='2d15ad6de5162aa425a6cc22b25a48abfa21986973cd8c68586f4591b2ad59ad'
PREFIXO='consultar python:'
IDS=('PY-NOMES','PY-MUTABILIDADE','PY-CONCATENACAO')
TOPICOS={'variaveis':('PY-NOMES',),'nomes':('PY-NOMES',),'reatribuicao':('PY-NOMES',),
         'mutabilidade':('PY-MUTABILIDADE',),'tuplas':('PY-MUTABILIDADE','PY-CONCATENACAO'),
         'concatenacao':('PY-CONCATENACAO',),'todos':IDS}
AJUDA='Use consultar python: seguido de variáveis, nomes, reatribuição, mutabilidade, tuplas, concatenação ou todos. Acrescente exemplo ao final do tópico para consultar um exemplo editorial. A consulta apenas transcreve registros locais pendentes.'
INDISPONIVEL='O catálogo documental local está indisponível ou difere da versão registrada. Nenhuma referência foi apresentada.'


def carregar():
    try:
        with ARQUIVO.open('rb') as stream:raw=stream.read(20001)
        if len(raw)>20000 or hashlib.sha256(raw).hexdigest()!=SHA256_CATALOGO:return {}
        data=json.loads(raw)
        if data.get('schema_version')!=2:return {}
        rows=data['registros']
        if len(rows)!=3 or tuple(r['id'] for r in rows)!=IDS:return {}
        for row in rows:
            if (row['estado_registro']!='pendente' or not row['url'].startswith('https://docs.python.org/3.13/')
                    or len(row['trecho'].split())>25
                    or hashlib.sha256(row['trecho'].encode()).hexdigest()!=row['sha256_trecho']):return {}
        return {r['id']:r for r in rows}
    except (OSError,ValueError,KeyError,TypeError):return {}


def interpretar(mensagem):
    if not isinstance(mensagem,str) or len(mensagem)>300 or any(c in mensagem for c in '\n\r\t'):return None
    q=normalizar(mensagem.strip())
    aliases={'variavel':'variaveis','variaveis':'variaveis','nome':'nomes','nomes':'nomes',
             'reatribuicao':'reatribuicao','reatribuicao de nomes':'reatribuicao',
             'mutabilidade':'mutabilidade','tupla':'tuplas','tuplas':'tuplas','lista':'tuplas','listas':'tuplas',
             'concatenacao de tuplas':'concatenacao','diferenca entre lista e tupla':'tuplas',
             'diferenca entre listas e tuplas':'tuplas'}
    match=re.fullmatch(r'(?:o que (?:e|sao)|explique|como funciona|como funcionam) (?:uma? |as? |os? )?(.+) em python',q)
    exemplo=False
    if not match:
        match=re.fullmatch(r'(?:de|mostre|pode dar) um exemplo(?: simples)? (?:de|sobre) (.+) em python',q)
        exemplo=True
    if match and match[1] in aliases:return aliases[match[1]],exemplo
    return None


def _preparar_direto(mensagem):
    if not isinstance(mensagem,str):return None
    explicita=mensagem.strip().casefold().startswith(PREFIXO)
    if explicita:
        topico=normalizar(mensagem.strip()[len(PREFIXO):].strip())
        exemplo=topico.endswith(' exemplo')
        if exemplo:topico=topico[:-8]
        if len(mensagem)>300 or any(c in mensagem for c in '\n\r\t') or topico not in TOPICOS:
            return {'resposta':AJUDA,'estado':'formato_invalido','registros':[]}
    else:
        pedido=interpretar(mensagem)
        if pedido is None:return None
        topico,exemplo=pedido
    data=carregar()
    if not data:return {'resposta':INDISPONIVEL,'estado':'catalogo_indisponivel','registros':[]}
    rows=[data[i] for i in TOPICOS[topico]]
    partes=['Consulta documental local — transcrição de registros pendentes.',
            'Nenhuma pesquisa web nem explicação gerada por modelo neste turno. A correspondência com o registro não comprova sua verdade.']
    meta=[]
    for row in rows:
        partes.append('['+row['id']+'] '+row['titulo']+'\n'
                      'Trecho literal (en): '+row['trecho']+'\n'
                      'Notas editoriais locais (pt-BR): '+row['notas_editoriais']+'\n'
                      'Fonte registrada: '+row['url']+'\n'
                      'Registro: pendente; preparado pela equipe de desenvolvimento em '+row['registrado_em']+'.')
        if exemplo:
            sample=row['exemplo_editorial']
            partes.append('Exemplo editorial local (não executado neste turno):\n```python\n'
                          +sample['codigo']+'\n```\nSaída esperada registrada:\n'+sample['saida_esperada'].rstrip())
        meta.append({'id':row['id'],'url':row['url'],'estado_registro':'pendente',
                     'sha256_trecho':row['sha256_trecho'],'sha256_catalogo':SHA256_CATALOGO,
                     'consulta_web_neste_turno':False,'notas_editoriais_sao_citacao_literal':False,'exemplo_editorial_incluido':exemplo})
    return {'resposta':'\n\n'.join(partes),'estado':'transcricao_registros_pendentes','registros':meta}


LIMITE_CONTEXTO_DOCUMENTAL=20
SEM_OUTRO_EXEMPLO='Não há exemplo editorial adicional cadastrado para essa consulta. Posso apresentar apenas o material já registrado, sem inventar outro exemplo.'


def _tipo_continuacao(mensagem):
    if not isinstance(mensagem,str) or len(mensagem)>150:return None
    q=normalizar(mensagem.strip())
    if q in {'explique o que acontece se eu mudar o valor depois','e se eu mudar o valor depois','o que acontece se eu mudar o valor depois'}:
        return 'reatribuicao'
    m=re.fullmatch(r'(?:(?:voce )?pode (?:dar|mostrar)|de|mostre) (um|outro) exemplo(?: simples)?(?: disso| disto)?',q)
    return m[1] if m else None


def _continuar(tipo,estado):
    ids=tuple(r['id'] for r in estado['registros'])
    if tipo=='reatribuicao':
        return _preparar_direto(PREFIXO+' reatribuicao exemplo') if ids==('PY-NOMES',) else None
    if tipo=='outro' and any(r.get('exemplo_editorial_incluido') for r in estado['registros']):
        return {'resposta':SEM_OUTRO_EXEMPLO,'estado':'sem_exemplo_adicional','registros':[]}
    topico=next((t for t,values in TOPICOS.items() if values==ids),None)
    return _preparar_direto(PREFIXO+' '+topico+' exemplo') if topico else None


def preparar(mensagem,historico=None):
    direta=_preparar_direto(mensagem)
    if direta is not None:return direta
    tipo=_tipo_continuacao(mensagem)
    if tipo is None:return None
    if historico is None:
        from cerebro.memoria_longa import recuperar_historico
        historico=recuperar_historico(LIMITE_CONTEXTO_DOCUMENTAL)
    if not isinstance(historico,list):return None
    rows=list(historico[-LIMITE_CONTEXTO_DOCUMENTAL:])
    if rows and isinstance(rows[-1],dict) and rows[-1].get('remetente')=='usuario' and rows[-1].get('mensagem')==mensagem:rows.pop()
    estado=None
    pedido=None
    for row in rows:
        if not isinstance(row,dict) or not isinstance(row.get('mensagem'),str):
            estado=None;pedido=None;continue
        if row.get('remetente')=='usuario':
            if pedido is not None:estado=None
            pedido=row['mensagem']
        elif row.get('remetente')=='luci' and pedido is not None:
            item=_preparar_direto(pedido)
            if item is None and estado is not None:
                anterior_tipo=_tipo_continuacao(pedido)
                if anterior_tipo:item=_continuar(anterior_tipo,estado)
            if item is None or item['resposta']!=row['mensagem']:
                estado=None
            elif item['estado']=='transcricao_registros_pendentes' and item['registros']:
                estado=item
            elif item['estado']!='sem_exemplo_adicional':
                estado=None
            pedido=None
        else:
            estado=None;pedido=None
    if pedido is not None or estado is None:return None
    return _continuar(tipo,estado)


def responder(mensagem):
    item=preparar(mensagem)
    return item['resposta'] if item is not None else None


def diagnostico(mensagem,resposta):
    item=preparar(mensagem)
    if item is None:return None
    confere=isinstance(resposta,str) and resposta==item['resposta']
    return {'nivel':'transcricao_documental_local_conferida' if confere else 'transcricao_documental_local_divergente',
            'bloquear_resposta':not confere,'verificacao_independente':False,
            'quantidade_afirmacoes':0,'afirmacoes_analisadas':[],
            'quantidade_registros':len(item['registros']) if confere else 0,
            'registros_documentais':item['registros'] if confere else [],
            'estado_consulta':item['estado'],'descricao':'Conferência exata da transcrição local, sem validação da verdade do conteúdo.'}
