"""Gramática fechada de atos sociais; não comprova emoções ou fatos."""
import re
from cerebro.foco_conversa import forma_social, normalizar, SAUDACOES, RESPOSTAS_BREVES, CONVITES_SOCIAIS


def contexto_social(pergunta):
    return isinstance(pergunta, str) and forma_social(pergunta) in SAUDACOES | RESPOSTAS_BREVES | CONVITES_SOCIAIS


def formula_social(texto, pergunta):
    if not isinstance(texto, str) or not contexto_social(pergunta):
        return False
    q = forma_social(pergunta)
    s = normalizar(texto)
    saudacoes = r'(?:ola|oi|bom dia|boa tarde|boa noite)'
    if q in CONVITES_SOCIAIS:
        if texto.strip().endswith('?') and re.fullmatch(r'(?:sobre quais assuntos voce gosta de conversar|quais assuntos (?:interessam a voce|voce gostaria de explorar)|qual (?:e )?o seu interesse ou (?:tema|topico) favorito (?:para conversar|que gostaria de discutir))',s):return True
        if re.fullmatch(r'(?:vamos (?:comecar|conversar)(?: entao)?|claro|podemos conversar)',s):return True
    perguntas = (
        r'como (?:voce esta|esta voce|vai voce)(?: hoje)?',
        r'como (?:voce )?esta se sentindo(?: hoje)?',
        r'tudo bem com voce',
        r'como posso (?:te )?ajudar(?: voce| voce hoje| hoje)?',
        r'como estas(?: hoje)?',
        r'o que voce gostaria de conversar sobre(?: hoje)?',
        r'como voce gostaria de comecar',
        r'(?:sobre o que|qual assunto) voce gostaria de conversar(?: hoje)?',
        r'(?:sobre o que|qual assunto) (?:quer|gostaria de) conversar(?: hoje)?',
    )
    # Pontuação precisa fazer parte da fórmula; sem remover conteúdo anexado.
    if texto.strip().endswith('?') and any(re.fullmatch(p, s) for p in perguntas):
        return True
    if q in SAUDACOES and re.fullmatch(saudacoes, s):
        return True
    if re.fullmatch(r'(?:e um prazer|prazer em|fico feliz em|fico contente em) (?:conversar|falar) com voce(?: tambem)?', s):
        return True
    if q in RESPOSTAS_BREVES:
        if s in {'que bom', 'que otimo', 'que bom saber disso', 'que bom ouvir isso'}:
            return True
        if re.fullmatch(r'(?:que bom que|(?:fico feliz|fico contente) (?:em )?(?:saber|ouvir) que) voce esta bem', s):
            return True
    verbo = r'(?:conversar|ouvir|escutar|ajudar)'
    oferta = r'(?:estou aqui para|estou disponivel para|posso) ' + verbo
    oferta += r'(?: e ' + verbo + r')?(?: (?:com voce|um pouco))?'
    if re.fullmatch(oferta, s):return True
    return texto.strip().endswith('?') and bool(re.fullmatch(oferta + r', como posso(?: ajudar)?', s))


def preparar_retomada_social(pergunta, verificacao, confiabilidade, *, foco_social, planejamento):
    """Texto editorial de recuperacao; jamais reutiliza o texto gerado bloqueado."""
    if foco_social is not True or planejamento is not False or not contexto_social(pergunta):
        return None
    if not isinstance(verificacao, dict) or not isinstance(confiabilidade, dict):
        return None
    if verificacao.get('bloquear_resposta') is not True or confiabilidade.get('bloquear_resposta') is not True:
        return None
    if verificacao.get('nivel') not in {'possui_afirmacoes_sem_evidencia', 'incoerencia_social_persistente'}:
        return None
    if confiabilidade.get('nivel') not in {'sem_apoio_local', 'possui_afirmacoes_sem_evidencia'}:
        return None
    if forma_social(pergunta) in CONVITES_SOCIAIS:
        return 'Sobre quais assuntos você gosta de conversar?'
    if forma_social(pergunta) in SAUDACOES:
        return 'Olá! Como você está hoje?'
    return 'Que bom! Sobre o que você gostaria de conversar?'
