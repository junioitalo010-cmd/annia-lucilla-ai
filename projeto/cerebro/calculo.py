"""Aritmetica limitada com AST e fracoes exatas; sem eval ou comandos."""
import ast
import re
import unicodedata
from fractions import Fraction
from decimal import Decimal,localcontext

ALLOWED=(ast.Expression,ast.BinOp,ast.UnaryOp,ast.Constant,ast.Add,ast.Sub,ast.Mult,ast.Div,ast.UAdd,ast.USub)

def formatar_valor(value):
    d=value.denominator
    for factor in [2,5]:
        while d%factor==0:d//=factor
    if d!=1:return str(value.numerator)+'/'+str(value.denominator)
    with localcontext() as ctx:
        ctx.prec=400
        text=format(Decimal(value.numerator)/Decimal(value.denominator),'f')
    if '.' in text:text=text.rstrip('0').rstrip('.')
    return text.replace('.',',')

PEDIDOS_REVISAO = {'isso esta errado. pode revisar', 'pode revisar a conta',
                  'revise a conta', 'confira a conta anterior'}


def _normalizar_revisao(texto):
    return ''.join(c for c in unicodedata.normalize('NFD', texto.casefold())
                   if not unicodedata.combining(c)).strip().rstrip('?!. ').strip()


def revisar_ultima_conta(texto):
    if texto not in PEDIDOS_REVISAO:
        return None
    from cerebro.memoria_longa import recuperar_historico
    rows = list(recuperar_historico(4))
    if (rows and rows[-1].get('remetente') == 'usuario'
            and _normalizar_revisao(rows[-1].get('mensagem', '')) == texto):
        rows.pop()
    if len(rows) < 2:
        return None
    usuario, luci = rows[-2:]
    if usuario.get('remetente') != 'usuario' or luci.get('remetente') != 'luci':
        return None
    pergunta = usuario.get('mensagem')
    resposta_anterior = luci.get('mensagem')
    if not isinstance(pergunta, str) or not isinstance(resposta_anterior, str):
        return None
    # Somente a conta imediatamente anterior; nao encadeia revisoes recursivas.
    if _normalizar_revisao(pergunta) in PEDIDOS_REVISAO:
        return None
    conta = calcular_pergunta(pergunta)
    if conta is None or conta['estado'] != 'calculado':
        return None
    coincide = verificar_calculo(resposta_anterior, pergunta) is not None
    nota = ('a resposta anterior coincide com esta conta'
            if coincide else 'esta é a conta recalculada, sem verificar outras afirmações anteriores')
    resposta = 'Conferência local: ' + conta['resposta'].rstrip('. ') + '; ' + nota + '.'
    return {'expressao': conta['expressao'], 'resposta': resposta,
            'estado': 'revisao_calculo', 'valor': conta['valor'],
            'operacao': 'revisao_conta_anterior', 'coincide_com_conta': coincide}


NUMERO_TROCA = r'[+-]?[0-9]{1,12}(?:[.,][0-9]{1,8})?'
PEDIDO_TROCA = re.compile(r'(?:e se (?:trocar|substituir)|troque|substitua) ('
                          + NUMERO_TROCA + r') por (' + NUMERO_TROCA + r')')


def substituir_na_ultima_conta(texto):
    pedido = PEDIDO_TROCA.fullmatch(texto)
    if not pedido:
        return None
    def esclarecer(resposta):
        return {'expressao': '', 'resposta': resposta, 'estado': 'esclarecimento_substituicao',
                'valor': None, 'operacao': 'substituicao_numero'}
    sem_base = 'Escreva a conta completa com a alteração desejada; não há uma expressão aritmética anterior confirmada para esta substituição.'
    from cerebro.memoria_longa import recuperar_historico
    rows = list(recuperar_historico(4))
    if (rows and rows[-1].get('remetente') == 'usuario'
            and _normalizar_revisao(rows[-1].get('mensagem', '')) == texto):
        rows.pop()
    if len(rows) < 2 or rows[-2].get('remetente') != 'usuario' or rows[-1].get('remetente') != 'luci':
        return esclarecer(sem_base)
    pergunta, resposta = rows[-2].get('mensagem'), rows[-1].get('mensagem')
    if not isinstance(pergunta, str) or not isinstance(resposta, str):
        return esclarecer(sem_base)
    # Nao reconstroi cadeias de substituicao/revisao nem altera medias silenciosamente.
    anterior = _normalizar_revisao(pergunta)
    if PEDIDO_TROCA.fullmatch(anterior) or anterior in PEDIDOS_REVISAO:
        return esclarecer(sem_base)
    conta = calcular_pergunta(pergunta)
    if (conta is None or conta['estado'] != 'calculado' or conta.get('operacao')
            or verificar_calculo(resposta, pergunta) is None):
        return esclarecer(sem_base)
    expressao = conta['expressao']
    antigo = Fraction(pedido[1].replace(',', '.'))
    novo = pedido[2].replace(',', '.')
    encontrados = []
    def procurar(node):
        if isinstance(node, ast.UnaryOp) and isinstance(node.operand, ast.Constant):
            valor = Fraction(ast.get_source_segment(expressao, node.operand))
            if isinstance(node.op, ast.USub):
                valor = -valor
            if valor == antigo:
                encontrados.append(node)
            return
        if isinstance(node, ast.Constant):
            if Fraction(ast.get_source_segment(expressao, node)) == antigo:
                encontrados.append(node)
            return
        for child in ast.iter_child_nodes(node):
            procurar(child)
    procurar(ast.parse(expressao, mode='eval'))
    if len(encontrados) > 1:
        return esclarecer('Esse valor aparece mais de uma vez; escreva a conta completa com a alteração desejada.')
    if not encontrados:
        return esclarecer('Esse valor não aparece como um número na expressão anterior; escreva a conta completa com a alteração desejada.')
    node = encontrados[0]
    if novo.startswith(('-', '+')):
        novo = '(' + novo + ')'
    linhas = expressao.splitlines(keepends=True)
    inicio = sum(map(len, linhas[:node.lineno-1])) + node.col_offset
    fim = sum(map(len, linhas[:node.end_lineno-1])) + node.end_col_offset
    alterada = expressao[:inicio] + novo + expressao[fim:]
    resultado = calcular_pergunta(alterada)
    if resultado is None:
        return esclarecer('A expressão alterada excede os limites da calculadora; escreva uma conta mais simples.')
    return dict(resultado, resposta='Substituição local: ' + resultado['resposta'],
                operacao='substituicao_numero')


def calcular_media(texto):
    """Gramatica fechada: virgula seguida de espaco separa inteiros; ponto e virgula permite decimais."""
    match = re.fullmatch(
        r'(?:calcule (?:a )?|qual (?:e )?a |explique (?:a )?)'
        r'media(?: aritmetica)? (?:de|dos numeros) ([0-9+.,; /-]+)', texto)
    if not match:
        return None
    lista = match.group(1).strip()
    if ';' in lista:
        partes = lista.split(';')
        numero = r'[+-]?[0-9]{1,12}(?:[.,][0-9]{1,8})?'
    else:
        partes = lista.split(',')
        numero = r'[+-]?[0-9]{1,12}'
    if not 2 <= len(partes) <= 20:
        return None
    partes = [parte.strip() for parte in partes]
    if not all(re.fullmatch(numero, parte) for parte in partes):
        return None
    if ';' not in lista and (len(partes) == 2 or re.search(r',(?=\S)', lista)):
        return {'expressao': lista, 'resposta': 'Para evitar confundir vírgula decimal com separador de valores, separe os números por ponto e vírgula; exemplo: 1,5; 2,5.',
                'estado': 'entrada_ambigua', 'valor': None}
    valores = [Fraction(parte.replace(',', '.')) for parte in partes]
    soma = sum(valores, Fraction(0))
    valor = formatar_valor(soma / len(valores))
    termos = [formatar_valor(v) for v in valores]
    expressao = '(' + ' + '.join(termos) + ') / ' + str(len(valores))
    resposta = ('Média aritmética: somar os ' + str(len(valores)) + ' valores e dividir pela quantidade; '
                + expressao + ' = ' + valor + '.')
    return {'expressao': expressao, 'resposta': resposta, 'estado': 'calculado', 'valor': valor,
            'operacao': 'media_aritmetica', 'quantidade': len(valores), 'soma': formatar_valor(soma)}


def resolver_distribuicao_livros(pergunta):
    """Resolve apenas o enunciado fechado de caixas/livros/pessoas.

    Nao interpreta livremente outros problemas nem confia em contas do LLM.
    """
    if not isinstance(pergunta, str) or len(pergunta) > 500:
        return None
    texto = _normalizar_revisao(pergunta)
    texto = re.sub(r'^(?:luci[,!. ]+)', '', texto)
    padrao = (r'tenho ([1-9][0-9]{0,5}) caixas? com ([1-9][0-9]{0,5}) livros? em cada uma\. '
              r'vou distribuir todos os livros igualmente entre ([1-9][0-9]{0,5}) pessoas?\. '
              r'quantos livros cada pessoa recebera\? explique (?:seu raciocinio|como chegou ao resultado)')
    # A normalizacao remove apenas pontuacao final, nao a pontuacao interna.
    match = re.fullmatch(padrao, texto)
    if not match:
        return None
    caixas, por_caixa, pessoas = map(int, match.groups())
    total = caixas * por_caixa
    if total % pessoas:
        return None  # Nao assumir fracionamento de livros.
    por_pessoa = total // pessoas
    resposta = (f'{caixas} caixas × {por_caixa} livros por caixa = {total} livros. '
                f'{total} livros ÷ {pessoas} pessoas = {por_pessoa} livros por pessoa. '
                f'Portanto, cada pessoa receberá {por_pessoa} livros.')
    return {'expressao': f'({caixas} * {por_caixa}) / {pessoas}',
            'resposta': resposta, 'estado': 'calculado',
            'valor': str(por_pessoa), 'operacao': 'distribuicao_livros_exata'}


def calcular_pergunta(pergunta):
    if not isinstance(pergunta,str) or len(pergunta)>240:return None
    distribuicao = resolver_distribuicao_livros(pergunta)
    if distribuicao is not None:
        return distribuicao
    text=''.join(c for c in unicodedata.normalize('NFD',pergunta.casefold()) if not unicodedata.combining(c))
    text=text.strip().rstrip('?!. ').strip()
    # Pedido explicativo fechado: retirar somente esta frase, sem executar comandos.
    explicacao_solicitada = False
    sufixo = 'explique como chegou ao resultado'
    if text.endswith(sufixo):
        prefixo = text[:-len(sufixo)].rstrip(' ?!.')
        if prefixo and prefixo != text:
            text = prefixo
            explicacao_solicitada = True
    revisao = revisar_ultima_conta(text)
    if revisao is not None:
        return revisao
    troca = substituir_na_ultima_conta(text)
    if troca is not None:
        return troca
    media = calcular_media(text)
    if media is not None:
        return media
    text=re.sub(r'^(?:quanto (?:e|da)|calcule|calcular|qual (?:e )?o resultado de)\s+','',text)
    for word,operator in [('dividido por','/'),('multiplicado por','*'),('vezes','*'),('mais','+'),('menos','-')]:
        text=re.sub(r'\b'+word+r'\b',operator,text)
    text=text.replace('×','*').replace('÷','/').replace('−','-').replace(',','.')
    if not text or len(text)>160 or not re.fullmatch(r'[0-9\s.()+*/-]+',text):return None
    try:
        tree=ast.parse(text,mode='eval');nodes=list(ast.walk(tree))
        if len(nodes)>96 or not any(isinstance(n,ast.BinOp) for n in nodes):return None
        for node in nodes:
            if type(node) not in ALLOWED:return None
            if isinstance(node,ast.Constant):
                raw=ast.get_source_segment(text,node)
                if type(node.value) not in (int,float) or not raw or len(raw)>24:return None
        def evaluate(node,depth=0):
            if depth>16:raise ValueError('Profundidade excedida')
            if isinstance(node,ast.Expression):return evaluate(node.body,depth+1)
            if isinstance(node,ast.Constant):return Fraction(ast.get_source_segment(text,node))
            if isinstance(node,ast.UnaryOp):
                value=evaluate(node.operand,depth+1)
                return value if isinstance(node.op,ast.UAdd) else -value
            a=evaluate(node.left,depth+1);b=evaluate(node.right,depth+1)
            if isinstance(node.op,ast.Add):value=a+b
            elif isinstance(node.op,ast.Sub):value=a-b
            elif isinstance(node.op,ast.Mult):value=a*b
            else:value=a/b
            if max(value.numerator.bit_length(),value.denominator.bit_length())>256:raise ValueError('Resultado excede limites')
            return value
        value=evaluate(tree)
    except ZeroDivisionError:
        return {'expressao':text,'resposta':'Não é possível dividir por zero.','estado':'divisao_por_zero','valor':None}
    except (ValueError,SyntaxError,RecursionError,OverflowError):return None
    result=formatar_valor(value)
    expression=re.sub(r'\s+',' ',text).strip().replace('.',',')
    return {'expressao':text,'resposta':expression+' = '+result+'.','estado':'calculado','valor':result}

def responder_calculo(pergunta):
    result=calcular_pergunta(pergunta)
    return result['resposta'] if result else None

def verificar_calculo(afirmacao,pergunta):
    if not isinstance(afirmacao,str):return None
    result=calcular_pergunta(pergunta)
    if result is None:return None
    text=afirmacao.strip().rstrip('. ')
    expected=result['resposta'].rstrip('. ')
    if re.sub(r'\s+','',text)!=re.sub(r'\s+','',expected):
        if result['valor'] is None or text!=result['valor']:return None
    return {'origem':'calculadora_local','estado':result['estado'],'campo':'aritmetica',
            'expressao':result['expressao'],'valor':result['valor'],
            'observacao':'Operacoes basicas calculadas por aritmetica exata, sem modelo e sem execucao de codigo.'}
