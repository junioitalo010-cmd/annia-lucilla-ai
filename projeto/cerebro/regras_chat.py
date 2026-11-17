"""Comando explicito de deducao, sem ferramentas ou extracao por modelo."""
import json
import copy
import re
from .motor_regras import carregar_json,analisar

PREFIXO='analisar regras:'
CONTINUAR='continuar regras:'
AJUDA=('Use analisar regras: em uma linha e, abaixo, um JSON com objetivo, padrao, regras e fatos. '
       'Cada resultado contém valor e fonte_informada. Cada regra contém id, quando e resultado. '
       'Condições e fatos devem ser true ou false; omita fatos desconhecidos. '
       'Esta análise não executa ações nem verifica as premissas.')


AJUDA_CONTINUAR=('Use continuar regras: em uma linha e, abaixo, JSON com analise_sha256 e fatos booleanos. '
                 'Copie o ID da análise desejada. Só condições já definidas podem ser atualizadas. '
                 'A análise precisa estar no histórico recente; nenhuma ação será executada.')


def _corpo(mensagem,prefixo):
    if len(mensagem)>10000:
        raise ValueError('Limite excedido.')
    first,sep,body=mensagem.lstrip().partition('\n')
    if first.strip().casefold()!=prefixo or not sep:
        raise ValueError('Formato invalido.')
    return carregar_json(body)


def _atualizar(data,update):
    if not isinstance(update,dict) or set(update)!={'analise_sha256','fatos'}:
        raise ValueError('Campos invalidos.')
    if not isinstance(update['analise_sha256'],str) or not re.fullmatch('[0-9a-f]{64}',update['analise_sha256']):
        raise ValueError('ID invalido.')
    changes=update['fatos']
    variables={key for rule in data['regras'] for key in rule['quando']}
    if not isinstance(changes,dict) or not 1<=len(changes)<=8 or not set(changes)<=variables or any(type(v) is not bool for v in changes.values()):
        raise ValueError('Fatos invalidos ou fora da analise.')
    derived=copy.deepcopy(data)
    derived['fatos'].update(changes)
    return derived


def _render(data):
    result=analisar(data)
    quoted=lambda value:json.dumps(value,ensure_ascii=False)
    lines=['Análise condicional das regras fornecidas.','ID da análise: '+result['entrada_sha256'],
           'Estado: '+result['estado']+'.']
    if result['resultado'] is not None:
        lines.append('Resultado sob essas premissas: '+quoted(result['resultado']))
    else:
        lines.append('Não há resultado único sob as premissas fornecidas.')
    lines.append('Possibilidades:')
    for item in result['possibilidades']:
        lines.append('- '+quoted(item['valor'])+' | regras: '+quoted(item['regras'])+' | fontes informadas: '+quoted(item['fontes_informadas']))
    lines.append('Condições ausentes: '+quoted(result['condicoes_ausentes']))
    lines.append('Hipóteses conferidas: '+str(result['hipoteses_conferidas']))
    if result['conflitos']:
        lines.append('Há hipóteses com regras simultâneas conflitantes; nenhuma prioridade foi inventada.')
    lines.append('Fatos e fontes foram fornecidos, não verificados independentemente. Nenhuma ação foi executada.')
    return {'resposta':'\n'.join(lines),'analise':result,'erro_formato':False}


def _indice(historico):
    """Reconstroi so pares usuario/resposta canonica; nenhuma gravacao ou cache."""
    if not isinstance(historico,list):
        return {}
    history=historico[-50:]
    index={}
    for first,second in zip(history,history[1:]):
        if not isinstance(first,dict) or not isinstance(second,dict) or first.get('remetente')!='usuario' or second.get('remetente')!='luci':
            continue
        message=first.get('mensagem')
        if not isinstance(message,str):
            continue
        try:
            if message.lstrip().casefold().startswith(PREFIXO):
                data=_corpo(message,PREFIXO)
            elif message.lstrip().casefold().startswith(CONTINUAR):
                update=_corpo(message,CONTINUAR)
                if not isinstance(update,dict) or not isinstance(update.get('analise_sha256'),str) or update['analise_sha256'] not in index:
                    continue
                data=_atualizar(index[update['analise_sha256']],update)
            else:
                continue
            result=_render(data)
            if second.get('mensagem')==result['resposta']:
                index[result['analise']['entrada_sha256']]=copy.deepcopy(data)
        except (ValueError,TypeError,UnicodeError,RecursionError):
            continue
    return index


def preparar(mensagem,historico=None):
    if not isinstance(mensagem,str):
        return None
    prefix=mensagem.lstrip().casefold()
    if prefix.startswith(PREFIXO):
        try:
            return _render(_corpo(mensagem,PREFIXO))
        except (ValueError,TypeError,UnicodeError,RecursionError):
            return {'resposta':AJUDA,'analise':None,'erro_formato':True}
    if not prefix.startswith(CONTINUAR):
        return None
    try:
        update=_corpo(mensagem,CONTINUAR)
        if not isinstance(update,dict) or not isinstance(update.get('analise_sha256'),str):
            raise ValueError('ID invalido.')
        if historico is None:
            from .memoria_longa import recuperar_contexto_conversa
            historico=recuperar_contexto_conversa(50)
        index=_indice(historico)
        if update['analise_sha256'] not in index:
            return {'resposta':'Não encontrei essa análise no histórico recente validado. Reenvie as regras completas para iniciar uma nova análise. '+AJUDA_CONTINUAR,
                    'analise':None,'erro_formato':True}
        return _render(_atualizar(index[update['analise_sha256']],update))
    except (ValueError,TypeError,UnicodeError,RecursionError):
        return {'resposta':AJUDA_CONTINUAR,'analise':None,'erro_formato':True}


def responder(mensagem):
    result=preparar(mensagem)
    return result['resposta'] if result is not None else None


def diagnostico(mensagem,resposta):
    result=preparar(mensagem)
    if result is None or resposta!=result['resposta']:
        return None
    analysis=result['analise']
    return {'nivel':'deducao_condicional_regras_explicitas','bloquear_resposta':False,
            'verificacao_independente':False,'quantidade_afirmacoes':0,'afirmacoes_analisadas':[],
            'estado_analise':analysis['estado'] if analysis is not None else 'formato_invalido',
            'entrada_sha256':analysis['entrada_sha256'] if analysis is not None else None,
            'executou_acao':False,'descricao':'Conferida reproducao da deducao finita; premissas e fontes nao foram verificadas.'}
