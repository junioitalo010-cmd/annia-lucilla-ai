 
from dataclasses import dataclass


@dataclass
class Decisao:
    acao: str
    nivel_risco: str
    autorizacao_necessaria: bool
    motivo: str


ACOES_PROTEGIDAS = (
    "excluir",
    "apagar",
    "formatar",
    "instalar",
    "desinstalar",
    "enviar",
    "comprar",
    "pagar",
    "alterar sistema",
    "executar arquivo",
)


def avaliar_acao(acao):
    texto = acao.lower().strip()

    if not texto:
        return Decisao(
            acao=acao,
            nivel_risco="indefinido",
            autorizacao_necessaria=True,
            motivo="Ação não identificada."
        )

    if any(item in texto for item in ACOES_PROTEGIDAS):
        return Decisao(
            acao=acao,
            nivel_risco="alto",
            autorizacao_necessaria=True,
            motivo="A ação pode alterar arquivos, sistemas ou gerar consequências externas."
        )

    return Decisao(
        acao=acao,
        nivel_risco="baixo",
        autorizacao_necessaria=False,
        motivo="Nenhum risco elevado identificado pelas regras atuais."
    )
