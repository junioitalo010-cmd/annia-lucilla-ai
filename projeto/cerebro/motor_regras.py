"""Deducao finita de regras booleanas fornecidas; sem modelo ou executor."""
import hashlib
import itertools
import json
import re

KEY=re.compile(r'[a-z][a-z0-9_]{0,39}')


def texto(value,limite):
    if not isinstance(value,str) or not 1<=len(value)<=limite or value!=value.strip():
        raise ValueError('Texto invalido.')
    return value


def objeto(value,campos):
    if not isinstance(value,dict) or set(value)!=set(campos):
        raise ValueError('Campos invalidos.')


def valores(data):
    objeto(data,('valor','fonte_informada'))
    texto(data['valor'],100)
    texto(data['fonte_informada'],256)


def booleanos(data,maximo):
    if not isinstance(data,dict) or len(data)>maximo:
        raise ValueError('Fatos/condicoes invalidos.')
    if any(not isinstance(k,str) or not KEY.fullmatch(k) or type(v) is not bool for k,v in data.items()):
        raise ValueError('Somente chaves identificadoras e booleanos estritos.')


def carregar_json(raw):
    if not isinstance(raw,str) or len(raw.encode('utf-8'))>16384:
        raise ValueError('JSON excede limite.')
    def unique(pairs):
        d={}
        for k,v in pairs:
            if k in d:
                raise ValueError('Chave duplicada.')
            d[k]=v
        return d
    return json.loads(raw,object_pairs_hook=unique)


def analisar(data):
    objeto(data,('objetivo','padrao','regras','fatos'))
    texto(data['objetivo'],200)
    valores(data['padrao'])
    booleanos(data['fatos'],24)
    rules=data['regras']
    if not isinstance(rules,list) or len(rules)>12:
        raise ValueError('No maximo doze regras.')
    ids=set()
    variables=set()
    for rule in rules:
        objeto(rule,('id','quando','resultado'))
        if not isinstance(rule['id'],str) or not KEY.fullmatch(rule['id']) or rule['id'] in ids:
            raise ValueError('Identificador invalido ou duplicado.')
        ids.add(rule['id'])
        booleanos(rule['quando'],8)
        if not rule['quando']:
            raise ValueError('Regra deve conter condicao.')
        variables.update(rule['quando'])
        valores(rule['resultado'])
    if len(variables)>8:
        raise ValueError('No maximo oito variaveis de condicao.')
    missing=sorted(variables-set(data['fatos']))
    possibilities={}
    conflicts=[]
    trace={}
    for rule in rules:
        cond=rule['quando']
        if any(k in data['fatos'] and data['fatos'][k] is not v for k,v in cond.items()):
            status='nao_aplicavel'
        elif all(k in data['fatos'] for k in cond):
            status='aplicavel'
        else:
            status='condicao_desconhecida'
        trace[rule['id']]={'estado':status,'fonte_informada':rule['resultado']['fonte_informada']}
    worlds=0
    for combination in itertools.product((False,True),repeat=len(missing)):
        worlds+=1
        facts=dict(data['fatos'])|dict(zip(missing,combination))
        applicable=[r for r in rules if all(facts[k] is v for k,v in r['quando'].items())]
        active=applicable or [{'id':'__padrao__','resultado':data['padrao']}]
        outcomes={r['resultado']['valor'] for r in active}
        if len(outcomes)>1:
            conflicts.append({'hipotese':dict(zip(missing,combination)),
                              'regras':sorted(r['id'] for r in applicable),'valores':sorted(outcomes)})
        for rule in active:
            value=rule['resultado']['valor']
            possibilities.setdefault(value,{'regras':set(),'fontes_informadas':set()})
            possibilities[value]['regras'].add(rule['id'])
            possibilities[value]['fontes_informadas'].add(rule['resultado']['fonte_informada'])
    if conflicts:
        status='conflito' if len(conflicts)==worlds else 'conflito_possivel'
    else:
        status='determinado' if len(possibilities)==1 else 'indeterminado'
    canonical=json.dumps(data,ensure_ascii=False,sort_keys=True,separators=(',',':'))
    return {'objetivo':data['objetivo'],'estado':status,
            'resultado':next(iter(possibilities)) if status=='determinado' else None,
            'possibilidades':[{ 'valor':v,'regras':sorted(d['regras']),'fontes_informadas':sorted(d['fontes_informadas'])}
                             for v,d in sorted(possibilities.items())],
            'condicoes_ausentes':missing,'regras_avaliadas':trace,'hipoteses_conferidas':worlds,
            'conflitos':conflicts,'entrada_sha256':hashlib.sha256(canonical.encode()).hexdigest(),
            'estado_fontes':'nao_verificadas','verificacao_independente':False,'executou_acao':False,
            'liberado_para_chat':False,'metodo':'enumeracao_finita_de_condicoes_booleanas'}
