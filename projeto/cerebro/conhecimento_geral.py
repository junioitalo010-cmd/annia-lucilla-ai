"""Política explícita de comunicação; não verifica nem promove conhecimento."""
import hashlib
import re
from cerebro.foco_conversa import normalizar

AVISO = 'Conhecimento geral do modelo — não verificado externamente.'
EXCLUSOES = re.compile(
    r'\b(?:voce|seu|sua|meu|minha|criador|luci|lucilla|hoje|agora|atual|atualmente|'
    r'cotacao|preco|noticia|presidente|eleicao|diagnostico|tratamento|medicamento|dose|'
    r'sintoma|doenca|cancer|diabetes|saude|investimento|comprar|vender|contrato|lei|juridico|'
    r'execute|executar|apague|apagar|instale|instalar|pesquise|pesquisar|acesse|acessar|'
    r'salve|salvar|altere|alterar|ignore|ignorar|verifique|verificar|fonte|fontes|'
    r'referencia|referencias|ficticio|ficticia)\b')
INICIO = re.compile(r'^(?:o que (?:e|sao)|explique|como funciona|como funcionam|'
                    r'quero entender|quero aprender sobre|me explique)\b')
CONTINUACAO = re.compile(r'^(?:pode |voce pode )?(?:dar|mostrar|explicar) (?:um |outro )?'
                        r'exemplo(?: simples)?(?: disso| disto| em python)?[.!? ]*$')
# Pedidos fechados de reformulacao, sem interpolar novas ordens no system.
REFORMULACAO = re.compile(
    r'^(?:(?:pode |voce pode )?explicar (?:melhor|de forma mais simples)|'
    r'explique (?:melhor|de forma mais simples)|'
    r'(?:resuma|resumir|pode resumir) (?:isso|em uma frase)|'
    r'nao entendi)[.!? ]*$')


def eh_continuacao(mensagem):
    q = normalizar(mensagem)
    return bool(CONTINUACAO.fullmatch(q) or REFORMULACAO.fullmatch(q))


OPERACOES = re.compile(
    r'\b(?:pesquisei|consultamos|consultei|verifiquei|confirmei|executei|instalei|salvei|'
    r'aprendi|treinei|acessei|agendei|enviei|alterei|realizei|criei|li|comprovei)\b|'
    r'\b(?:foi|foram) (?:pesquisad[oa]s?|verificad[oa]s?|confirmad[oa]s?|executad[oa]s?)\b|'
    r'\b(?:acabei|acabamos) de (?:pesquisar|consultar|executar|salvar|treinar)\b|'
    r'https?://|www\.|\b(?:segundo|conforme a fonte|referencias? bibliograficas?)\b|'
    r'\b(?:tenho|possuo|sinto|sou)\b.{0,50}\b(?:consciencia|sentimentos?|consciente)\b')


# Marcadores reservados a rotas documentais; uma geracao nao pode usar esses
# recibos como prova da propria origem. Isto nao verifica a verdade do conteudo.
PROVENIENCIA_INCOMPATIVEL = re.compile(
    r'\bnenhuma pesquisa web nem explicacao gerada por modelo\b|'
    r'\b(?:nenhuma|sem) (?:resposta|explicacao) gerada por (?:um )?modelo\b|'
    r'\b(?:resposta|explicacao) (?:nao foi|nao e) gerada por (?:um )?modelo\b|'
    r'\bnao houve (?:geracao|explicacao|resposta)(?: gerada)? (?:por|de) (?:um )?modelo\b|'
    r'\b(?:consulta documental local|transcricao de registros pendentes|exemplo editorial local)\b')


# A rota geral nao possui prova de consulta/validacao de estudos ou autoridades.
AUTORIDADE_SEM_FONTE = re.compile(
    r'\b(?:estudos?|pesquisas?) (?:tambem |ja |cientific[oa]s? |recentes? )*'
    r'(?:mostram|mostra|indicam|indica|comprovam|comprova|demonstram|demonstra|sugerem|sugere|apontam|aponta)\b|'
    r'\b(?:cientistas|especialistas|estudiosos|educadores) (?:tambem )?'
    r'(?:afirmam|recomendam|concordam|demonstram|comprovam)\b|'
    r'\b(?:propost[ao]|defendid[ao]|recomendad[ao]) por (?:varios |diversos )?'
    r'(?:estudiosos|educadores|cientistas|especialistas)\b')


def selecionar(mensagem, historico):
    """Reconhecimento conservador de pedido didático; não é classificador semântico."""
    if not isinstance(mensagem, str) or not 1 <= len(mensagem) <= 600:
        return False
    if any(c in mensagem for c in ('\n', ';', ':')):
        return False
    q = normalizar(mensagem)
    # Remove somente o vocativo inicial; referencias a identidade no restante seguem excluidas.
    q = re.sub(r'^(?:luci|annia lucilla)[,!. ]+', '', q, count=1)
    # Pedido de explicacao com estilo proprio nao altera o assunto nem a confiabilidade.
    q = re.sub(r'^(explique) com (?:suas|as suas) proprias palavras\s+', r'\1 ', q, count=1)
    continuacao = eh_continuacao(mensagem)
    if EXCLUSOES.search(q) and not continuacao:
        return False
    if INICIO.match(q) and not continuacao:
        return True
    if not continuacao or not isinstance(historico, list):
        return False
    rows = list(historico)
    if rows and rows[-1].get('remetente') == 'usuario' and rows[-1].get('mensagem') == mensagem:
        rows.pop()
    return bool(rows and rows[-1].get('remetente') == 'luci'
                and isinstance(rows[-1].get('mensagem'), str)
                and rows[-1]['mensagem'].startswith(AVISO + '\n\n'))


def turnos_pertinentes(mensagem, historico):
    """Mantem apenas a cadeia didatica explicitamente retomada; nunca toda a memoria."""
    if not selecionar(mensagem, historico) or not eh_continuacao(mensagem):
        return ()
    rows = list(historico)
    if rows and rows[-1].get('remetente') == 'usuario' and rows[-1].get('mensagem') == mensagem:
        rows.pop()
    pares = []
    while len(rows) >= 2 and len(pares) < 3:
        usuario, luci = rows[-2:]
        texto = luci.get('mensagem')
        pergunta = usuario.get('mensagem')
        if (usuario.get('remetente') != 'usuario' or luci.get('remetente') != 'luci'
                or not isinstance(texto, str) or not texto.startswith(AVISO + '\n\n')
                or not isinstance(pergunta, str) or not selecionar(pergunta, rows[:-2])):
            break
        pares.insert(0, (('user', pergunta[:2000]), ('assistant', texto[:2000])))
        rows = rows[:-2]
        if not eh_continuacao(pergunta):
            break
    return tuple(turno for par in pares for turno in par)


def autorizar_comunicacao(resposta, verificacao, confiabilidade):
    """Diagnósticos originais permanecem intactos, inclusive seus bloqueios."""
    if (not isinstance(resposta, str) or not resposta.strip() or OPERACOES.search(normalizar(resposta))
            or PROVENIENCIA_INCOMPATIVEL.search(normalizar(resposta)) or AUTORIDADE_SEM_FONTE.search(normalizar(resposta))
            or re.search(r'\bvoce (?:mora|nasceu|possui|tem (?:[0-9]|doenca|filh[oa])|e (?:um|uma))\b', normalizar(resposta))):
        return None
    if (not isinstance(verificacao, dict) or not isinstance(confiabilidade, dict)
            or type(verificacao.get('bloquear_resposta')) is not bool
            or type(confiabilidade.get('bloquear_resposta')) is not bool):
        return None
    if verificacao.get('nivel') not in {'possui_afirmacoes_sem_evidencia', 'sem_afirmacoes_factuais', 'afirmacoes_com_suporte_local'}:
        return None
    if confiabilidade.get('nivel') not in {'sem_apoio_local', 'possui_afirmacoes_sem_evidencia', 'sem_afirmacoes_factuais', 'afirmacoes_com_suporte_local'}:
        return None
    permitidas = {'sem_evidencia_local', 'apoio_marcado_verificado'}
    # Não ultrapassar conflitos, conhecimento pendente/contestado ou fatos pessoais.
    for diagnostic, key in ((verificacao, 'contagens'), (confiabilidade, 'contagens_afirmacoes')):
        counts = diagnostic.get(key)
        if not isinstance(counts, dict) or not counts:
            return None
        if any(type(v) is not int or v < 0 or (v and k not in permitidas) for k, v in counts.items()):
            return None
    return {'politica': 'conhecimento_geral_v1', 'estado': 'modelo_nao_verificado',
            'origem': 'modelo_de_linguagem_local', 'verificacao_independente': False,
            'pesquisa_executada': False, 'promovido_a_conhecimento': False,
            'resposta_sha256': hashlib.sha256(resposta.encode('utf-8')).hexdigest(),
            'bloqueio_verificador_original': verificacao.get('bloquear_resposta'),
            'bloqueio_confiabilidade_original': confiabilidade.get('bloquear_resposta')}


def validar_entrega(resposta,politica):
    if not isinstance(resposta,str) or not resposta.startswith(AVISO+'\n\n') or not isinstance(politica,dict):return False
    if (politica.get('politica')!='conhecimento_geral_v1' or politica.get('estado')!='modelo_nao_verificado'
            or politica.get('origem')!='modelo_de_linguagem_local'
            or politica.get('verificacao_independente') is not False
            or politica.get('pesquisa_executada') is not False
            or politica.get('promovido_a_conhecimento') is not False):return False
    raw=resposta[len(AVISO)+2:]
    return bool(raw.strip() and not PROVENIENCIA_INCOMPATIVEL.search(normalizar(raw)) and not AUTORIDADE_SEM_FONTE.search(normalizar(raw))
                and hashlib.sha256(raw.encode('utf-8')).hexdigest()==politica.get('resposta_sha256'))
