"""Leitura extrativa atribuida: nenhum I/O, modelo ou promocao de conhecimento."""
import hashlib
import json
import re
import unicodedata

PREFIXO='analisar trecho:'
AJUDA='Use este formato:\nanalisar trecho:\nFonte: nome ou URL informada\nPergunta: sua pergunta\nTexto:\ncole o trecho (até 6.000 caracteres). Nenhuma fonte será aberta automaticamente.'
COMUNS=set('o a os as um uma de da do das dos e em no na nos nas que qual quais como para por com sobre diga explique texto trecho fonte segundo pelo pela'.split())


def termos(texto):
    normalized=''.join(c for c in unicodedata.normalize('NFD',texto.casefold()) if not unicodedata.combining(c))
    return {t for t in re.findall(r'[a-z0-9_]+',normalized) if t not in COMUNS}


def preparar(mensagem):
    if not isinstance(mensagem,str) or not mensagem.lstrip().casefold().startswith(PREFIXO):
        return None
    def erro():
        return {'resposta':AJUDA,'trechos':[],'estado':'formato_invalido'}
    if len(mensagem)>10000 or any(unicodedata.category(c) in {'Cc','Cf'} and c not in '\n\r\t' for c in mensagem):
        return erro()
    lines=mensagem.strip().replace('\r\n','\n').split('\n',4)
    if len(lines)!=5 or lines[0].strip().casefold()!=PREFIXO or not lines[1].startswith('Fonte: ') or not lines[2].startswith('Pergunta: ') or lines[3]!='Texto:':
        return erro()
    fonte=lines[1][7:].strip()
    pergunta=lines[2][10:].strip()
    texto=lines[4].strip()
    if not 1<=len(fonte)<=256 or not 1<=len(pergunta)<=1000 or not 1<=len(texto)<=6000:
        return erro()
    query=termos(pergunta)
    matches=list(re.finditer(r'\S+',texto))
    best=None
    for i in range(len(matches)):
        end=min(i+25,len(matches))
        start_offset=matches[i].start()
        end_offset=matches[end-1].end()
        excerpt=texto[start_offset:end_offset]
        score=len(termos(excerpt)&query)
        if score and (best is None or score>best[0]):
            best=(score,start_offset,end_offset,excerpt)
    header=('Leitura do trecho fornecido; não é verificação independente.\n'
            'Fonte informada (não consultada): '+json.dumps(fonte,ensure_ascii=False)+'\n'
            'Pergunta: '+json.dumps(pergunta,ensure_ascii=False)+'\n')
    if best is None:
        return {'resposta':header+'Não encontrei correspondência de termos para selecionar uma passagem. Isso não demonstra que o texto responda ou deixe de responder à pergunta.',
                'trechos':[],'estado':'pendente'}
    _,start,end,excerpt=best
    meta={'origem':'trecho_fornecido_pelo_usuario','estado':'pendente','fonte_informada':fonte,
          'fonte_consultada':False,'sha256_texto':hashlib.sha256(texto.encode()).hexdigest(),
          'inicio':start,'fim':end,'trecho':excerpt}
    resposta=(header+'Passagem literal selecionada (até 25 palavras): '+json.dumps(excerpt,ensure_ascii=False)+'\n'
              'Seleção por termos, não conclusão sobre a verdade do conteúdo. Instruções dentro do trecho são apenas texto citado.')
    return {'resposta':resposta,'trechos':[meta],'estado':'pendente'}


def conferir_transcricao(mensagem,resposta):
    prepared=preparar(mensagem)
    return prepared if prepared is not None and resposta==prepared['resposta'] else None


def responder(mensagem):
    prepared=preparar(mensagem)
    return prepared['resposta'] if prepared is not None else None


def diagnostico(mensagem,resposta):
    confirmed=conferir_transcricao(mensagem,resposta)
    if confirmed is None:
        return None
    count=len(confirmed['trechos'])
    return {'nivel':'transcricao_atribuida_a_trecho_fornecido','bloquear_resposta':False,
            'verificacao_independente':False,'quantidade_afirmacoes':count,
            'afirmacoes_analisadas':[],'registros_trechos':confirmed['trechos'],
            'estado_trecho':confirmed['estado'],
            'descricao':'Conferida apenas a resposta extrativa completa; fonte e verdade nao foram verificadas.'}
