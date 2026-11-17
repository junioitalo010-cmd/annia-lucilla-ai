"""Recorte de contexto para uma troca social recente; não apaga memória."""
import re
import unicodedata


def normalizar(texto):
    if not isinstance(texto,str):return ''
    return ' '.join(''.join(c for c in unicodedata.normalize('NFD',texto.casefold()) if not unicodedata.combining(c)).split()).rstrip('.!? ')


SAUDACOES={'ola','oi','bom dia','boa tarde','boa noite'}
CONVITES_SOCIAIS={'convite_social'}
RESPOSTAS_BREVES={'bem','estou bem','to bem','tudo bem','muito bem','vou bem'}



def forma_social(mensagem):
    q=normalizar(mensagem)
    if re.fullmatch(r'(?:ola,? )?(?:quero (?:participar (?:da conversa|do teste de conversa)|experimentar (?:esta|essa) conversa|conversar(?: um pouco)?)|podemos (?:comecar(?: o teste de conversa)?|conversar))',q):return 'convite_social'
    match=re.fullmatch(r'(ola|oi|bom dia|boa tarde|boa noite)(?:,? (?:luci|annia lucilla))?',q)
    if match:return match[1]
    if q in RESPOSTAS_BREVES:return q
    if re.fullmatch(r'(?:(?:estou|to|vou) (?:muito )?bem|(?:tudo (?:bem|tranquilo))(?: por aqui)?|bem)(?:,? (?:(?:so |apenas )?quero (?:conversar(?: um pouco)?|bater papo)|podemos conversar))?',q):
        return 'estou bem'
    return q

def orientacoes_sociais(mensagem):
    """Texto interno fixo: nunca interpola memoria ou instrucoes do usuario."""
    texto=('Esta é uma troca social breve. Você responde como Luci ao usuário. '
           'Dirija-se ao interlocutor como você; não troque quem está falando. '
           'Responda à mensagem atual sem repetir a saudação anterior nem retomar assuntos técnicos não solicitados.')
    texto+=' Use até duas frases curtas. Faça no máximo uma pergunta pertinente, sem repetir a saudação após a resposta do usuário.'
    atual=forma_social(mensagem)
    if atual in CONVITES_SOCIAIS:
        texto+=' O usuário quer iniciar uma conversa. Faça somente uma pergunta breve sobre os interesses dele, sem introdução, fatos, gostos próprios ou dados privados.'
    elif atual in SAUDACOES:
        texto+=' O usuário acabou de cumprimentá-la. Cumprimente-o com uma frase breve e natural.'
    elif atual in RESPOSTAS_BREVES:
        texto+=' O usuário respondeu como está. Reconheça essa resposta com uma frase breve, natural e educada.'
    return texto


def motivo_reformulacao(mensagem,resposta,turnos):
    if re.search(r'\bcomo estou\s*\?',normalizar(resposta)+'?'):
        return 'troca_de_interlocutor'
    if forma_social(mensagem) in RESPOSTAS_BREVES:
        if re.match(r'^(?:ola|oi|bom dia|boa tarde|boa noite)\b',normalizar(resposta)):
            return 'saudacao_repetida_apos_estado'
        if re.match(r'^(?:estou|to|vou) (?:muito )?bem\b',normalizar(resposta)):
            return 'estado_do_usuario_atribuido_a_luci'
        previous=next((texto for papel,texto in reversed(turnos) if papel=='assistant'),None)
        if previous and normalizar(previous)==normalizar(resposta):return 'repeticao_da_resposta_anterior'
    return None


def recortar(mensagem,historico):
    if not isinstance(mensagem,str) or not isinstance(historico,list):return historico,False
    q=forma_social(mensagem)
    if q not in SAUDACOES|RESPOSTAS_BREVES|CONVITES_SOCIAIS:return historico,False
    records=[r for r in historico if isinstance(r,dict) and isinstance(r.get('mensagem'),str)]
    prior=records[:-1] if records and records[-1].get('remetente')=='usuario' and forma_social(records[-1]['mensagem'])==q else records
    if q in SAUDACOES|CONVITES_SOCIAIS:
        return records[len(prior):],True
    if q in RESPOSTAS_BREVES and re.search(r'\b(?:quero conversar|quero bater papo|podemos conversar)\b',normalizar(mensagem)):
        return records[max(0,len(prior)-1):],True
    if q in RESPOSTAS_BREVES:
        if not prior or prior[-1].get('remetente')!='luci':return historico,False
        last=normalizar(prior[-1]['mensagem'])
        if not re.search(r'como (?:voce|o senhor) esta|como vai voce|tudo bem com voce',last) and not re.match(r'^(?:ola|oi|bom dia|boa tarde|boa noite)\b',last):return historico,False
    for i in range(len(prior)-1,-1,-1):
        if prior[i].get('remetente')=='usuario' and forma_social(prior[i]['mensagem']) in SAUDACOES:
            return records[i:],True
    return records[max(0,len(prior)-1):],True


def convite_assunto(mensagem):
    """Reconhece apenas convite simples; o assunto continua dado do usuario."""
    if not isinstance(mensagem,str) or len(mensagem)>160:
        return False
    q=normalizar(mensagem)
    return bool(re.fullmatch(
        r'(?:agora quero (?:falar|conversar)|quero (?:falar|conversar)|vamos (?:falar|conversar)) sobre [a-z]+(?: [a-z]+){0,7}',q))


def continuacao_interesse(mensagem, historico):
    """Declaracao simples de interesse depois de pergunta social reconhecida."""
    if not isinstance(mensagem, str) or not isinstance(historico, list) or len(mensagem) > 180:
        return ()
    q = normalizar(mensagem)
    match = re.fullmatch(r'(?:gosto de|meu interesse e) ([a-z]+(?: [a-z]+){0,5})', q)
    if not match or any(c in mensagem for c in ('?', ';', ':', '\n')):
        return ()
    from cerebro.conhecimento_geral import EXCLUSOES
    if EXCLUSOES.search(match[1]) or re.search(r'\b(?:senha|endereco|telefone|ignore|ignorar|documentos|medicamentos)\b', match[1]):
        return ()
    rows = list(historico)
    if rows and rows[-1].get('remetente') == 'usuario' and rows[-1].get('mensagem') == mensagem:
        rows.pop()
    if len(rows) < 2:
        return ()
    user, assistant = rows[-2:]
    if user.get('remetente') != 'usuario' or assistant.get('remetente') != 'luci':
        return ()
    initial = user.get('mensagem', '')
    question = assistant.get('mensagem', '')
    from cerebro.formulas_sociais import formula_social
    if (forma_social(initial) not in CONVITES_SOCIAIS or not isinstance(question, str)
            or not question.strip().endswith('?') or not formula_social(question, initial)):
        return ()
    return (('user', initial), ('assistant', question))


def continuacao_assunto(mensagem,historico):
    """Uma especificacao curta apos convite explicito e pergunta da Luci."""
    if not isinstance(mensagem,str) or not isinstance(historico,list) or '?' in mensagem:return ()
    q=normalizar(mensagem)
    if not re.fullmatch(r'[a-z]+(?: [a-z]+){0,4}',q) or q in SAUDACOES|RESPOSTAS_BREVES:return ()
    rows=list(historico)
    if rows and rows[-1].get('remetente')=='usuario' and rows[-1].get('mensagem')==mensagem:rows.pop()
    if len(rows)<2:return ()
    user,assistant=rows[-2:]
    if user.get('remetente')!='usuario' or assistant.get('remetente')!='luci':return ()
    initial=user.get('mensagem','');question=assistant.get('mensagem','')
    if not convite_assunto(initial) or not isinstance(question,str) or not question.strip().endswith('?'):return ()
    if len(question)>1000:return ()
    return (('user',initial),('assistant',question))


def responder_interesse(mensagem):
    """Pergunta editorial neutra; nao infere pratica nem grava preferencias."""
    from cerebro.memoria_longa import recuperar_historico
    if not continuacao_interesse(mensagem, recuperar_historico(4)):
        return None
    texto = re.sub(r'\s+', ' ', mensagem.strip()).rstrip('.!? ')
    match = re.fullmatch(r'(?:gosto de|meu interesse (?:é|e)) (.+)', texto, flags=re.IGNORECASE)
    if match is None:
        return None
    return 'O que você gostaria de explorar sobre ' + match[1] + '?'
