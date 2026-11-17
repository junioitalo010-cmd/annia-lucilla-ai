"""Comandos estritos de memoria de teste, sem interpretacao por LLM.

Nao altera identidade, configuracoes, regras ou registros de conhecimento.
"""
import re
from .memoria_longa import guardar_informacao, recuperar_informacao

CHAVE = 'teste_codigo_autorizado_v1'
PADRAO_GRAVAR = re.compile(
    r'^Luci, quero que voc[eê] guarde na sua mem[oó]ria esta informa[cç][aã]o de teste:\s*'
    r'meu c[oó]digo de teste [eé] ([A-Za-z0-9-]{1,40})\.\s*'
    r'Confirme se conseguiu salvar\.$', re.IGNORECASE)
PADRAO_LER = re.compile(
    r'^Luci, qual [eé] o c[oó]digo de teste que pedi para voc[eê] guardar\?$', re.IGNORECASE)


def processar_comando(mensagem):
    """Retorna None se nao for um comando explicitamente suportado."""
    texto = mensagem.strip()
    grava = PADRAO_GRAVAR.fullmatch(texto)
    if grava:
        codigo = grava.group(1)
        if not guardar_informacao(CHAVE, codigo):
            return 'Nao foi possivel confirmar a gravacao do codigo de teste.'
        if recuperar_informacao(CHAVE) != codigo:
            return 'Nao foi possivel confirmar a leitura apos a gravacao.'
        return f'Codigo de teste {codigo} salvo e conferido na memoria local.'
    if PADRAO_LER.fullmatch(texto):
        codigo = recuperar_informacao(CHAVE)
        if codigo is None:
            return 'Ainda nao encontrei um codigo de teste salvo nesta memoria.'
        return f'O codigo de teste armazenado e {codigo}.'
    return None
