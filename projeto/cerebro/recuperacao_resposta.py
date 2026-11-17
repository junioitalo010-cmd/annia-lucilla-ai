"""Recuperacao limitada: nao libera texto gerado nem promove conhecimento."""
LIMITACAO='Não tenho informações suficientes para confirmar isso. Qual aspecto você quer estudar?'
LIMITACAO_CONTINUIDADE='Não tenho informações suficientes para confirmar isso. Você pode compartilhar um trecho ou uma fonte para analisarmos?'


def preparar_limitacao(verificacao, confiabilidade, *, foco_social, planejamento, repetida=False):
    if foco_social is not False or planejamento is not False:
        return None
    if not isinstance(verificacao,dict) or not isinstance(confiabilidade,dict):
        return None
    if verificacao.get('bloquear_resposta') is not True or confiabilidade.get('bloquear_resposta') is not True:
        return None
    if verificacao.get('nivel')!='possui_afirmacoes_sem_evidencia':
        return None
    if confiabilidade.get('nivel') not in {'sem_apoio_local','possui_afirmacoes_sem_evidencia'}:
        return None
    if type(repetida) is not bool:
        return None
    return LIMITACAO_CONTINUIDADE if repetida else LIMITACAO
