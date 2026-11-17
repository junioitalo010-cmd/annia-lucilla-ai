"""Visao derivada de declaracoes explicitas; nao grava nem inventa preferencias."""
import re
import unicodedata


def normalizar(texto):
    texto = unicodedata.normalize('NFD', texto.casefold())
    return ' '.join(''.join(c for c in texto if unicodedata.category(c) != 'Mn').split())


def _extrair(texto, sujeito):
    if not isinstance(texto, str) or not 3 <= len(texto) <= 2000:
        return None
    # Frases compostas, perguntas e negacoes nao fornecem evidencia por esta gramatica.
    if re.search(r'[?\n;,:]|\b(?:nao|nunca|jamais|mas|porem|porque|pois)\b', normalizar(texto)):
        return None
    pattern = (sujeito + r' (?P<campo>[\w]+(?: [\w]+){0,2}) '
               r'favorit[oa] (?:é|e) (?P<valor>.+?)\s*[.!]?')
    match = re.fullmatch(pattern, texto.strip(), flags=re.IGNORECASE)
    if not match:
        return None
    campo = normalizar(match['campo'])
    if not re.fullmatch(r'[a-z]+(?: [a-z]+){0,2}', campo):
        return None
    valor = match['valor'].rstrip('.! ').strip()
    # Evita transformar novas oracoes/instrucoes em valor simples.
    if not 2 <= len(valor) <= 200 or re.search(r'[.!]|\b(?:e|ou|ignore|execute|altere|apague)\b', normalizar(valor)):
        return None
    return {'campo': campo, 'valor': valor}


def extrair_declaracao(texto):
    return _extrair(_declaracao_sem_prefixo(texto), r'(?:[OoAa] )?(?:[Mm]eu|[Mm]inha)')


def _declaracao_sem_prefixo(texto):
    if not isinstance(texto,str):
        return texto
    # Prefixo fechado, somente no inicio; nao elimina virgulas do restante.
    return re.sub(r'^\s*na verdade,\s*','',texto,flags=re.IGNORECASE)


def extrair_resposta(texto):
    if not isinstance(texto, str):
        return None
    # Remove apenas prefixos fechados de atribuicao; prova vem do historico, nao do verbo.
    texto = re.sub(r'^voce (?:mencionou|disse|informou|declarou) que ', '', normalizar(texto))
    return _extrair(texto, r'(?:o |a )?(?:seu|sua)')


def campo_perguntado(consulta):
    if not isinstance(consulta, str):
        return None
    text = normalizar(consulta).rstrip('?.! ')
    text = re.sub(r'^voce (?:se )?lembra(?: de)? ','',text)
    text = re.sub(r' agora$','',text)
    match = re.fullmatch(r'qual (?:e )?(?:o |a )?(?:meu|minha) ([a-z]+(?: [a-z]+){0,2}) favorit[oa]', text)
    return match[1] if match else None


def preferencia_atual(consulta, registros):
    campo = campo_perguntado(consulta)
    if not campo or not isinstance(registros, list):
        return None
    for index in range(len(registros) - 1, -1, -1):
        row = registros[index]
        if not isinstance(row, dict) or row.get('remetente') != 'usuario':
            continue
        item = extrair_declaracao(row.get('mensagem'))
        if item and item['campo'] == campo:
            return {**item, 'fonte': 'declaracao_usuario', 'mensagem_origem': row['mensagem'],
                    'posicao_historico': index,
                    'escopo': 'mais_recente_nos_registros_disponiveis'}
        raw = _declaracao_sem_prefixo(row.get('mensagem'))
        if isinstance(raw, str) and '?' not in raw and re.match(
                r'^(?:o |a )?(?:meu|minha) ' + re.escape(campo) + r' favorit[oa]\b', normalizar(raw)):
            # Atualizacao nao interpretavel invalida a resolucao automatica anterior.
            return None
    return None


def responder_preferencia(consulta,registros):
    """Retoma declaracao explicita; nao gera nem altera preferencia pessoal."""
    atual=preferencia_atual(consulta,registros)
    if atual is None:
        return None
    return _formatar_atribuicao(atual)


def _formatar_atribuicao(atual):
    origem=normalizar(_declaracao_sem_prefixo(atual['mensagem_origem']))
    feminino=bool(re.match(r'^(?:a )?minha\b',origem))
    sujeito='sua' if feminino else 'seu'
    adjetivo='favorita' if feminino else 'favorito'
    return f"Você informou que {sujeito} {atual['campo']} {adjetivo} é {atual['valor']}."


def confirmar_declaracao(mensagem,registros):
    """Confirma so a declaracao atual ja presente no historico, sem alegar verdade externa."""
    item=extrair_declaracao(mensagem)
    if item is None or not isinstance(registros,list) or not registros:
        return None
    last=registros[-1]
    if not isinstance(last,dict) or last.get('remetente')!='usuario' or not isinstance(last.get('mensagem'),str) or last['mensagem'].strip()!=mensagem.strip():
        return None
    atual=preferencia_atual('qual meu '+item['campo']+' favorito?',registros)
    if atual is None or normalizar(atual['valor'])!=normalizar(item['valor']) or atual['mensagem_origem'].strip()!=mensagem.strip():
        return None
    return _formatar_atribuicao(atual)


def precisa_esclarecimento(mensagem, historico):
    if not isinstance(mensagem, str) or not isinstance(historico, list):
        return False
    if not re.fullmatch(r'(?:voce )?pode (?:fazer|executar|continuar) (?:isso|isto|aquilo)[?!. ]*', normalizar(mensagem)):
        return False
    previous = list(historico)
    if previous and previous[-1].get('remetente') == 'usuario' and previous[-1].get('mensagem') == mensagem:
        previous.pop()
    return not previous
