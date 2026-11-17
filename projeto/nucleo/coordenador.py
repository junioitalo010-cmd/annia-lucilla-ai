from nucleo.raciocinio import MotorRaciocinio
from nucleo.decisao import avaliar_acao

from nucleo.memoria_decisoes import (
    registrar_decisao,
    recuperar_decisoes,
)

from nucleo.memoria_experiencias import (
    registrar_experiencia,
    recuperar_experiencias,
    avaliar_experiencia,
    identificar_padroes,
)


class Coordenador:
    """
    Coordena os principais componentes do núcleo da ANNIA LUCILLA.

    Responsabilidades:
    - Coordenar o motor de raciocínio.
    - Gerenciar conversas e planejamento.
    - Coordenar decisões.
    - Registrar e recuperar experiências.
    - Acompanhar a aquisição de conhecimentos.
    """

    def __init__(self, funcao_modelo=None):
        self.raciocinio = MotorRaciocinio(funcao_modelo)

        self.ultima_decisao = None
        self.ultimo_plano = None
        self.ultimas_experiencias = []
        self.ultimo_feedback = None
        self.ultimos_resultados = []
        self.ultimos_padroes = []

        self.ultima_resposta_planejada = None
        self.ultimo_objetivo = None
        self.ultimo_relatorio_aquisicao = None

    # --------------------------------------------------
    # VALIDAÇÕES
    # --------------------------------------------------

    @staticmethod
    def validar_texto(valor, nome="valor"):
        if not isinstance(valor, str):
            raise TypeError(f"{nome} deve ser um texto.")

        valor = valor.strip()

        if not valor:
            raise ValueError(f"{nome} não pode estar vazio.")

        return valor

    @staticmethod
    def validar_limite(valor, nome, minimo, maximo):
        if isinstance(valor, bool) or not isinstance(valor, int):
            raise TypeError(f"{nome} deve ser um número inteiro.")

        if not minimo <= valor <= maximo:
            raise ValueError(
                f"{nome} deve estar entre {minimo} e {maximo}."
            )

        return valor

    # --------------------------------------------------
    # MODELO DE IA
    # --------------------------------------------------

    def conectar_modelo(self, funcao_modelo):
        """
        Encaminha a conexão do modelo ao motor de raciocínio.
        """
        if not callable(funcao_modelo):
            raise TypeError("O modelo precisa ser uma função executável.")

        self.raciocinio.conectar_modelo(funcao_modelo)

        return True

    # --------------------------------------------------
    # CONVERSAÇÃO
    # --------------------------------------------------

    def conversar(self, mensagem):
        mensagem = self.validar_texto(mensagem, "mensagem")

        return self.raciocinio.analisar(mensagem)

    def conversar_com_planejamento(self, mensagem, objetivo):
        mensagem = self.validar_texto(mensagem, "mensagem")
        objetivo = self.validar_texto(objetivo, "objetivo")

        resultado = self.raciocinio.analisar_com_planejamento(
            mensagem,
            objetivo
        )

        self.ultima_resposta_planejada = resultado
        self.ultimo_objetivo = objetivo

        if isinstance(resultado, dict):
            self.ultimo_plano = resultado.get("plano")
            self.ultimas_experiencias = resultado.get(
                "experiencias",
                []
            )
            self.ultimos_padroes = resultado.get("padroes", [])

        return resultado

    # --------------------------------------------------
    # CONFIABILIDADE E VERIFICAÇÃO
    # --------------------------------------------------

    def recuperar_confiabilidade(self):
        return self.raciocinio.recuperar_analise()

    def recuperar_verificacao(self):
        return self.raciocinio.recuperar_verificacao()

    # --------------------------------------------------
    # AQUISIÇÃO DE CONHECIMENTO
    # --------------------------------------------------

    def adquirir_conhecimento(
        self,
        consulta,
        quantidade=5,
        limite=10,
        conhecimentos=None
    ):
        consulta = self.validar_texto(consulta, "consulta")

        quantidade = self.validar_limite(
            quantidade,
            "quantidade",
            1,
            10
        )

        limite = self.validar_limite(
            limite,
            "limite",
            1,
            100
        )

        relatorio = self.raciocinio.adquirir_conhecimento(
            consulta=consulta,
            quantidade=quantidade,
            limite=limite,
            conhecimentos=conhecimentos
        )

        self.ultimo_relatorio_aquisicao = relatorio

        return relatorio

    def recuperar_ultima_aquisicao(self):
        """
        Recupera o relatório diretamente do motor de raciocínio,
        mantendo uma única referência principal ao resultado.
        """
        relatorio = getattr(
            self.raciocinio,
            "ultimo_relatorio_aquisicao",
            None
        )

        if relatorio is not None:
            self.ultimo_relatorio_aquisicao = relatorio

        return self.ultimo_relatorio_aquisicao

    def recuperar_estado_aquisicao(self):
        relatorio = self.recuperar_ultima_aquisicao()

        if not isinstance(relatorio, dict):
            return {
                "disponivel": False,
                "estado": "sem_aquisicao"
            }

        return {
            "disponivel": True,
            "estado": relatorio.get("estado", "desconhecido"),
            "conhecimento_salvo": relatorio.get(
                "conhecimento_salvo",
                False
            ),
            "conhecimento_verificado": relatorio.get(
                "conhecimento_verificado",
                False
            )
        }

    # --------------------------------------------------
    # HISTÓRICO DE DECISÕES
    # --------------------------------------------------

    def registrar_decisao(self, decisao):
        resultado = registrar_decisao(decisao)

        self.ultima_decisao = decisao

        return resultado

    def recuperar_decisoes(self, limite=50):
        return recuperar_decisoes(limite)

    # --------------------------------------------------
    # MEMÓRIA DE EXPERIÊNCIAS
    # --------------------------------------------------

    def registrar_experiencia(
        self,
        situacao,
        acao,
        resultado,
        avaliacao=None
    ):
        registro = registrar_experiencia(
            situacao=situacao,
            acao=acao,
            resultado=resultado,
            avaliacao=avaliacao
        )

        self.ultimas_experiencias.append(registro)

        return registro

    def recuperar_experiencias(self, limite=50):
        experiencias = recuperar_experiencias(limite)

        self.ultimas_experiencias = experiencias

        return experiencias

    def avaliar_experiencia(self, identificador, avaliacao):
        resultado = avaliar_experiencia(
            identificador,
            avaliacao
        )

        self.ultimo_feedback = avaliacao

        return resultado

    def identificar_padroes(self, limite=100):
        padroes = identificar_padroes(limite)

        self.ultimos_padroes = padroes

        return padroes

    # --------------------------------------------------
    # PLANEJAMENTO
    # --------------------------------------------------

    def planejar(self, objetivo):
        objetivo = self.validar_texto(objetivo, "objetivo")

        experiencias = self.recuperar_experiencias()
        padroes = self.identificar_padroes()

        self.raciocinio.experiencias_contexto = experiencias
        self.raciocinio.padroes_contexto = padroes

        plano = self.raciocinio.preparar_contexto_planejamento(
            objetivo
        )

        self.ultimo_objetivo = objetivo
        self.ultimo_plano = plano
        self.ultimas_experiencias = experiencias
        self.ultimos_padroes = padroes

        return plano

    # --------------------------------------------------
    # AVALIAÇÃO DE AÇÕES
    # --------------------------------------------------

    def avaliar(self, acao):
        resultado = avaliar_acao(acao)

        self.ultimo_feedback = resultado

        return resultado

    # --------------------------------------------------
    # ESTADO DO COORDENADOR
    # --------------------------------------------------

    def recuperar_estado(self):
        return {
            "modelo_conectado": callable(
                getattr(self.raciocinio, "funcao_modelo", None)
            ),
            "ultima_decisao": self.ultima_decisao,
            "ultimo_objetivo": self.ultimo_objetivo,
            "ultimo_plano": self.ultimo_plano,
            "quantidade_experiencias": len(
                self.ultimas_experiencias
            ),
            "quantidade_padroes": len(
                self.ultimos_padroes
            ),
            "ultima_aquisicao": self.recuperar_estado_aquisicao()
        }