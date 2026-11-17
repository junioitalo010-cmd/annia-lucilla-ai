"""Apoio limitado a atribuições explícitas na mensagem atual, sem persistência.

Reconhecer uma atribuição não comprova capacidade nem autoriza sua execução.
Gramática fechada: formas desconhecidas continuam sem apoio.
"""
import re
import unicodedata


def normalizar(texto):
    return ' '.join(''.join(c for c in unicodedata.normalize('NFD', texto.lower())
                           if unicodedata.category(c) != 'Mn').split())


OBJETO = r'(?:o hardware|o software|as fontes|a documentacao|o codigo|os testes|a pesquisa|o projeto)'
VERBOS = {'cuido': 'cuidar', 'cuida': 'cuidar', 'analiso': 'analisar',
          'analisa': 'analisar', 'reviso': 'revisar', 'revisa': 'revisar',
          'organizo': 'organizar', 'organiza': 'organizar'}
CLAUSULA = re.compile(r'(?P<sujeito>eu|voce) (?P<verbo>cuido|cuida|analiso|analisa|reviso|revisa|organizo|organiza) (?P<objeto>(?:d)?' + OBJETO + r')')


def extrair(texto, resposta=False):
    partes = re.split(r',? e |, ', texto)
    resultado = []
    for parte in partes:
        m = CLAUSULA.fullmatch(parte)
        if not m:
            return None
        sujeito, verbo, objeto = m.group('sujeito', 'verbo', 'objeto')
        # Concordância impede aceitar "eu cuida" e trocar a perspectiva.
        if (sujeito == 'eu') != verbo.endswith('o'):
            return None
        if verbo in ('cuido', 'cuida'):
            if not objeto.startswith('d'):
                return None
            objeto = objeto[1:]
        elif objeto.startswith('d'):
            return None
        ator = ('luci' if resposta else 'usuario') if sujeito == 'eu' else ('usuario' if resposta else 'luci')
        resultado.append((ator, VERBOS[verbo], objeto))
    return resultado


def eh_atribuicao(texto):
    return bool(extrair(normalizar(texto).rstrip('.!')))


def verificar_atribuicao(afirmacao, mensagem):
    if not isinstance(mensagem, str) or not isinstance(afirmacao, str):
        return None
    if len(mensagem) > 10000:
        return None
    # Somente sentenças completas declarativas; uma pergunta nunca é evidência.
    sentencas = re.findall(r'[^.!?]+[.!?]|[^.!?]+$', normalizar(mensagem))
    fatos = []
    for sentenca in sentencas:
        if sentenca.endswith('?'):
            continue
        extraidos = extrair(sentenca.strip().rstrip('.!').strip())
        if not extraidos:
            # Uma correção ou negação fora da gramática pode invalidar o anterior.
            return None
        fatos.extend(extraidos)
    resposta = extrair(normalizar(afirmacao).rstrip('.!'), resposta=True)
    if not resposta or not all(fato in fatos for fato in resposta):
        return None
    # Atribuições conflitantes na mesma mensagem exigem esclarecimento.
    for ator, acao, objeto in resposta:
        if any(a != ator and v == acao and o == objeto for a, v, o in fatos):
            return None
    return {'origem': 'mensagem_atual_usuario', 'estado': 'declaracao_registrada',
            'campo': 'atribuicoes_conversa',
            'valor': [{'ator': a, 'acao': v, 'objeto': o} for a, v, o in resposta],
            'observacao': 'Confirma apenas a atribuição declarada nesta mensagem; não comprova execução, capacidade ou autorização.'}
