"""Retoma escolhas explícitas de tema do usuário, sem inferir fatos externos."""
import json
import re
from cerebro.foco_conversa import normalizar, convite_assunto, continuacao_interesse, SAUDACOES, RESPOSTAS_BREVES
from cerebro.consulta_documental import interpretar, _tipo_continuacao

LIMITE = 40
SEM_ASSUNTO = 'Não consigo identificar um assunto explícito nas mensagens recentes. Qual tema você deseja retomar?'
PERGUNTAS = {'sobre qual assunto estamos conversando', 'sobre o que estamos conversando',
             'qual e o assunto atual', 'qual era o assunto da conversa',
             'qual tema escolhi por ultimo', 'qual assunto escolhi por ultimo',
             'qual foi o ultimo tema que escolhi', 'qual foi o ultimo assunto que escolhi'}
PERGUNTAS_ESTILO = {'qual preferencia de comunicacao acabei de escolher',
                   'qual e minha preferencia de comunicacao mais recente',
                   'qual preferencia de resposta escolhi por ultimo'}
SEM_ESTILO = 'Não encontrei uma preferência de comunicação reconhecida nas mensagens recentes disponíveis. Como prefere receber as respostas?'


def _estilo(texto):
    if not isinstance(texto, str) or len(texto) > 180 or any(c in texto for c in ('?', ';', ':', '\n')):
        return None
    q = normalizar(texto)
    m = re.fullmatch(r'(?:agora )?prefiro (respostas curtas|explicacoes detalhadas|respostas detalhadas)', q)
    if not m:
        return None
    return {'respostas curtas': 'respostas curtas',
            'explicacoes detalhadas': 'explicações detalhadas',
            'respostas detalhadas': 'respostas detalhadas'}[m[1]]


def _declaracao_estilo(texto):
    return (isinstance(texto, str) and len(texto) <= 180
            and not any(c in texto for c in ('?', ';', ':', '\n'))
            and bool(re.match(r'^(?:agora )?(?:prefiro|nao (?:quero|prefiro)(?: mais)?) (?:respostas|explicacoes|outro estilo|outra forma)\b', normalizar(texto))))


def _preparar_estilo(historico):
    atual = None
    for row in historico[-LIMITE:]:
        if not isinstance(row, dict) or row.get('remetente') != 'usuario':
            continue
        texto = row.get('mensagem')
        if _declaracao_estilo(texto):
            valor = _estilo(texto)
            atual = {'preferencia': valor, 'mensagem_usuario': texto} if valor else None
    if atual is None:
        return {'resposta': SEM_ESTILO, 'estado': 'sem_preferencia_reconhecida', 'registros': [],
                'tipo_contexto': 'preferencia_comunicacao_declarada'}
    resposta = ('Pelas suas mensagens recentes, você pediu ' + json.dumps(atual['preferencia'], ensure_ascii=False)
                + '. Sua mensagem foi: ' + json.dumps(atual['mensagem_usuario'], ensure_ascii=False) + '.')
    return {'resposta': resposta, 'estado': 'preferencia_atribuida_usuario', 'registros': [atual],
            'tipo_contexto': 'preferencia_comunicacao_declarada'}


ROTULOS = {'variaveis': 'variáveis em Python', 'nomes': 'nomes em Python',
           'reatribuicao': 'reatribuição em Python', 'mutabilidade': 'mutabilidade em Python',
           'tuplas': 'listas e tuplas em Python', 'concatenacao': 'concatenação em Python'}



OPCOES_ORDINAIS = {'a primeira': 0, 'a primeira opcao': 0, 'primeira opcao': 0,
                   'a segunda': 1, 'a segunda opcao': 1, 'segunda opcao': 1}
SEM_OPCOES = 'Não identifiquei duas opções explícitas na pergunta imediatamente anterior. Qual opção você deseja escolher?'

def _ordinal(mensagem):
    if not isinstance(mensagem, str) or len(mensagem) > 60 or any(c in mensagem for c in ('?', ';', ':', '\n')):
        return None
    return OPCOES_ORDINAIS.get(normalizar(mensagem))

def _preparar_opcao(mensagem, historico):
    indice = _ordinal(mensagem)
    if indice is None:
        return None
    rows = list(historico) if isinstance(historico, list) else []
    if rows and isinstance(rows[-1], dict) and rows[-1].get('remetente') == 'usuario' and rows[-1].get('mensagem') == mensagem:
        rows.pop()
    vazio = {'resposta': SEM_OPCOES, 'estado': 'sem_opcoes_reconhecidas', 'registros': [], 'tipo_contexto': 'escolha_ordinal'}
    if len(rows) < 2 or any(not isinstance(r, dict) for r in rows[-2:]):
        return vazio
    user, assistant = rows[-2:]
    question = assistant.get('mensagem')
    if (user.get('remetente') != 'usuario' or assistant.get('remetente') != 'luci'
            or not isinstance(user.get('mensagem'), str) or not isinstance(question, str)
            or len(question) > 220 or any(c in question for c in ('\n', ';', ':')) or question.count('?') != 1):
        return vazio
    match = re.fullmatch(r'Você prefere ([^?]+) ou ([^?]+)\?', question.strip(), re.IGNORECASE)
    if not match:
        return vazio
    options = [x.strip() for x in match.groups()]
    if any(not x or len(x) > 90 or re.search(r'\bou\b', x, re.IGNORECASE) for x in options):
        return vazio
    # Conteúdo citado como dado, nunca executado ou promovido a fato externo.
    chosen = options[indice]
    resposta = ('Pela sua resposta, você indicou a opção ' + str(indice + 1) + ' da pergunta anterior: '
                + json.dumps(chosen, ensure_ascii=False) + '.')
    return {'resposta': resposta, 'estado': 'opcao_atribuida_usuario',
            'registros': [{'pergunta_luci': question, 'mensagem_usuario': mensagem,
                           'indice': indice + 1, 'opcao': chosen}], 'tipo_contexto': 'escolha_ordinal'}


def eh_consulta(mensagem):
    return isinstance(mensagem, str) and len(mensagem) <= 120 and (normalizar(mensagem) in PERGUNTAS | PERGUNTAS_ESTILO or _ordinal(mensagem) is not None)


def _explicito(mensagem):
    doc = interpretar(mensagem)
    if doc:
        return ROTULOS[doc[0]]
    if isinstance(mensagem, str) and len(mensagem) <= 180 and not any(c in mensagem for c in ('?', ';', ':', '\n')):
        q = normalizar(mensagem)
        m = re.fullmatch(r'(?:agora )?(?:prefiro|quero) (?:falar|conversar) (?:de|sobre) ([a-z]+(?: [a-z]+){0,7})', q)
        if m and not re.search(r'\b(?:nao|nunca|mas|ignore|apague|execute|salve)\b', m[1]):
            return re.search(r'\b(?:de|sobre)\s+(.+)', mensagem, re.IGNORECASE)[1].rstrip('.! ')
    if convite_assunto(mensagem):
        # Copia somente o tema literal; não o interpola em instruções do modelo.
        return re.search(r'\bsobre\s+(.+)', mensagem, re.IGNORECASE)[1].rstrip('.!? ')
    return None


def preparar(mensagem, historico=None):
    if not eh_consulta(mensagem):
        return None
    if historico is None:
        from cerebro.memoria_longa import recuperar_historico
        historico = recuperar_historico(LIMITE)
    if not isinstance(historico, list):
        historico = []
    rows = list(historico[-LIMITE:])
    if _ordinal(mensagem) is not None:
        return _preparar_opcao(mensagem, rows)
    if rows and isinstance(rows[-1], dict) and rows[-1].get('remetente') == 'usuario' and rows[-1].get('mensagem') == mensagem:
        rows.pop()
    if normalizar(mensagem) in PERGUNTAS_ESTILO:
        return _preparar_estilo(rows)
    assunto = None
    pedido = None
    anterior = None
    for indice, row in enumerate(rows):
        if not isinstance(row, dict) or not isinstance(row.get('mensagem'), str):
            assunto = pedido = anterior = None
            continue
        if row.get('remetente') == 'usuario':
            if pedido is not None:
                assunto = anterior = None
            pedido = row['mensagem']
            continue
        if row.get('remetente') != 'luci' or pedido is None:
            assunto = pedido = anterior = None
            continue
        topico = _explicito(pedido)
        if topico:
            assunto = {'topico': topico, 'mensagem_usuario': pedido}
        elif continuacao_interesse(pedido, rows[:indice]):
            tema = re.sub(r'^(?:gosto de|meu interesse (?:é|e))\s+', '', pedido.strip(), flags=re.IGNORECASE).rstrip('.!? ')
            assunto = {'topico': tema, 'mensagem_usuario': pedido}
        elif eh_consulta(pedido) or _tipo_continuacao(pedido) or _declaracao_estilo(pedido):
            pass  # Uma referência mantém um assunto já identificado; não cria um.
        elif (anterior and convite_assunto(anterior) and assunto
              and re.fullmatch(r'[a-z]+(?: [a-z]+){0,3}', normalizar(pedido))
              and normalizar(pedido) not in SAUDACOES | RESPOSTAS_BREVES):
            assunto = {'topico': pedido.rstrip('.!? '), 'mensagem_usuario': pedido}
        else:
            assunto = None  # Não apresentar um tema antigo como atual após fala não reconhecida.
        anterior = pedido
        pedido = None
    if pedido is not None:
        assunto = None
    if assunto is None:
        return {'resposta': SEM_ASSUNTO, 'estado': 'sem_assunto_explicito', 'registros': []}
    resposta = ('Pelas suas mensagens recentes, o assunto é ' + json.dumps(assunto['topico'], ensure_ascii=False)
                + '. Sua mensagem foi: ' + json.dumps(assunto['mensagem_usuario'], ensure_ascii=False) + '.')
    return {'resposta': resposta, 'estado': 'assunto_atribuido_usuario', 'registros': [assunto]}


def responder(mensagem):
    item = preparar(mensagem)
    return item['resposta'] if item is not None else None


def diagnostico(mensagem, resposta):
    item = preparar(mensagem)
    if item is None:
        return None
    confere = isinstance(resposta, str) and resposta == item['resposta']
    return {'nivel': 'contexto_conversa_conferido' if confere else 'contexto_conversa_divergente',
            'bloquear_resposta': not confere, 'verificacao_independente': False,
            'quantidade_afirmacoes': 0, 'afirmacoes_analisadas': [],
            'estado_contexto': item['estado'], 'registros_contexto': item['registros'] if confere else [],
            'descricao': 'Correspondência com escolhas explícitas do usuário na janela recente; não valida fatos externos.'}
