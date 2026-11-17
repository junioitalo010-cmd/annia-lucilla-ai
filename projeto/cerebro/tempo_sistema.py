"""Data civil baseada no relogio do sistema, nao no modelo de linguagem."""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import re
import unicodedata

FUSO='America/Sao_Paulo'
DIAS=['segunda-feira','terça-feira','quarta-feira','quinta-feira','sexta-feira','sábado','domingo']
MESES=['janeiro','fevereiro','março','abril','maio','junho','julho','agosto','setembro','outubro','novembro','dezembro']

def normalizar(texto):
    if not isinstance(texto,str):return ''
    text=''.join(c for c in unicodedata.normalize('NFD',texto.casefold()) if not unicodedata.combining(c))
    return re.sub(r'\s+',' ',text).strip().rstrip('.!? ')

def data_local(momento=None):
    moment=momento if momento is not None else datetime.now(timezone.utc)
    if moment.tzinfo is None:raise ValueError('Momento deve incluir fuso horario.')
    return moment.astimezone(ZoneInfo(FUSO))

def frase_data(momento=None):
    local=data_local(momento)
    return f'Hoje é {DIAS[local.weekday()]}, {local.day} de {MESES[local.month-1]} de {local.year}.'

PERGUNTAS_DATA={'qual dia e hoje','que dia e hoje','qual e o dia de hoje','qual a data de hoje','qual e a data de hoje','que data e hoje','qual e a data atual','qual o dia de hoje','qual e a data hoje'}

def responder_data_sistema(pergunta):
    if normalizar(pergunta) not in PERGUNTAS_DATA:return None
    try:return frase_data()
    except ZoneInfoNotFoundError:return None

def verificar_data_sistema(texto,momento=None):
    text=re.sub(r'^senhor italo\s*[,!:]\s*','',normalizar(texto))
    try:
        local=data_local(momento)
        if text!=normalizar(frase_data(local)):return None
    except ZoneInfoNotFoundError:return None
    return {'origem':'relogio_sistema','estado':'consultado_no_sistema','campo':'data_atual',
            'valor':local.date().isoformat(),'fuso':FUSO,
            'observacao':'Data civil calculada pelo relogio do sistema; depende da configuracao correta do relogio.'}
