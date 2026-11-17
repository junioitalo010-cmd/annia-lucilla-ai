 
from nucleo.decisao import avaliar_acao
from nucleo.planejamento import criar_plano
from nucleo.raciocinio import MotorRaciocinio

from nucleo.memoria_decisoes import (
    recuperar_decisoes,
    recuperar_decisao_por_id,
    contar_decisoes,
    buscar_decisoes,
    atualizar_resultado,
    registrar_feedback_decisao,
    recuperar_historico_resultados,
    contar_resultados
)

from nucleo.memoria_experiencias import (
    registrar_experiencia,
    recuperar_experiencias,
    recuperar_experiencia_por_id,
    recuperar_experiencias_por_decisao,
    recuperar_avaliacoes_experiencia,
    buscar_experiencias,
    contar_experiencias,
    atualizar_experiencia,
    avaliar_experiencia,
    identificar_padroes
)


class Coordenador:

    def __init__(self, funcao_modelo=None):
        self.raciocinio = MotorRaciocinio(funcao_modelo)

        self.ultima_decisao = None
        self.ultimo_plano = None

        self.ultimas_experiencias = []
        self.ultimo_feedback = None
        self.ultimos_resultados = {}
        self.ultimos_padroes = {}

        self.ultima_resposta_planejada = None
        self.ultimo_objetivo_planejado = None

        self.ultimo_relatorio_aquisicao = None

    # --------------------------------------------------
    # COMUNICACAO E RACIOCINIO
    # --------------------------------------------------

    def conectar_modelo(self, funcao_modelo):
        self.raciocinio.conectar_modelo(funcao_modelo)

    def conversar(self, mensagem):
        return self.raciocinio.analisar(mensagem)

    def conversar_com_planejamento(self, mensagem, objetivo):

        if not isinstance(mensagem, str) or not mensagem.strip():
            raise ValueError("A mensagem não pode estar vazia.")

        if not isinstance(objetivo, str) or not objetivo.strip():
            raise ValueError("O objetivo não pode estar vazio.")

        resposta = self.raciocinio.analisar_com_planejamento(
            mensagem,
            objetivo
        )

        self.ultima_resposta_planejada = resposta
        self.ultimo_objetivo_planejado = objetivo

        self.ultimo_plano = self.raciocinio.recuperar_plano()

        self.ultimas_experiencias = (
            self.raciocinio.recuperar_experiencias_consultadas()
        )

        self.ultimos_padroes = (
            self.raciocinio.recuperar_padroes_consultados()
        ) or {}

        return resposta

    def recuperar_confiabilidade(self):
        return self.raciocinio.recuperar_analise()

    def recuperar_verificacao(self):
        return self.raciocinio.recuperar_verificacao()

    def recuperar_decisao_memoria(self):
        return recuperar_decisoes()

    # --------------------------------------------------
    # AQUISICAO DE CONHECIMENTO
    # --------------------------------------------------

    def adquirir_conhecimento(
        self,
        consulta,
        quantidade=5,
        limite=10
    ):
        """
        Encaminha a solicitacao de pesquisa ao motor de raciocinio.

        A aquisicao analisa os resultados, mas nao aprova
        nem salva automaticamente novos conhecimentos.
        """

        if not isinstance(consulta, str) or not consulta.strip():
            raise ValueError("A consulta não pode estar vazia.")

        relatorio = self.raciocinio.adquirir_conhecimento(
            consulta=consulta,
            quantidade=quantidade,
            limite=limite
        )

        self.ultimo_relatorio_aquisicao = relatorio

        return relatorio

    def recuperar_ultima_aquisicao(self):
        return self.raciocinio.recuperar_ultima_aquisicao()

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
            "consulta": relatorio.get("consulta"),
            "conhecimento_salvo": relatorio.get(
                "conhecimento_salvo",
                relatorio.get("knowledge_saved", False)
            ),
            "conhecimento_verificado": relatorio.get(
                "conhecimento_verificado",
                relatorio.get("knowledge_verified", False)
            )
        }

    # --------------------------------------------------
    # MEMORIA DE DECISOES
    # --------------------------------------------------

    def recuperar_historico_decisoes(self, limite=20):
        return recuperar_decisoes(limite)

    def recuperar_decisao_por_id(self, identificador):
        return recuperar_decisao_por_id(identificador)

    def buscar_historico_decisoes(self, consulta, limite=10):
        return buscar_decisoes(consulta, limite)

    def contar_decisoes_registradas(self):
        return contar_decisoes()

    def atualizar_resultado_decisao(
        self,
        identificador,
        resultado,
        justificativa="",
        origem="sistema",
        confianca=None
    ):
        return atualizar_resultado(
            identificador=identificador,
            resultado=resultado,
            justificativa=justificativa,
            origem=origem,
            confianca=confianca
        )

    # --------------------------------------------------
    # FEEDBACK DAS DECISOES
    # --------------------------------------------------

    def registrar_feedback_decisao(
        self,
        identificador,
        resultado,
        justificativa="",
        origem="usuario",
        confianca=None
    ):
        feedback = registrar_feedback_decisao(
            identificador=identificador,
            resultado=resultado,
            justificativa=justificativa,
            origem=origem,
            confianca=confianca
        )

        self.ultimo_feedback = feedback

        return feedback

    def recuperar_historico_resultados(self, identificador):
        return recuperar_historico_resultados(identificador)

    def recuperar_ultimo_feedback(self):
        return self.ultimo_feedback

    def contar_resultados_decisoes(self):
        self.ultimos_resultados = contar_resultados()
        return self.ultimos_resultados

    def recuperar_estatisticas_resultados(self):
        return self.contar_resultados_decisoes()

    # --------------------------------------------------
    # MEMORIA DE EXPERIENCIAS
    # --------------------------------------------------

    def registrar_experiencia(
        self,
        situacao,
        acao_realizada,
        resultado,
        aprendizado="",
        decisao_id=None,
        classificacao_resultado="inconclusivo",
        origem="desconhecida",
        confianca=None
    ):
        if decisao_id is not None:
            decisao = recuperar_decisao_por_id(decisao_id)

            if decisao is None:
                raise ValueError(
                    "A decisão informada não existe na memória."
                )

        return registrar_experiencia(
            situacao=situacao,
            acao_realizada=acao_realizada,
            resultado=resultado,
            aprendizado=aprendizado,
            decisao_id=decisao_id,
            classificacao_resultado=classificacao_resultado,
            origem=origem,
            confianca=confianca
        )

    def registrar_experiencia_da_decisao(
        self,
        decisao_id,
        resultado,
        aprendizado="",
        classificacao_resultado="inconclusivo",
        origem="usuario",
        confianca=None
    ):
        decisao = recuperar_decisao_por_id(decisao_id)

        if decisao is None:
            raise ValueError(
                "A decisão informada não existe na memória."
            )

        return self.registrar_experiencia(
            situacao=decisao.get("objetivo", ""),
            acao_realizada=decisao.get("acao", ""),
            resultado=resultado,
            aprendizado=aprendizado,
            decisao_id=decisao_id,
            classificacao_resultado=classificacao_resultado,
            origem=origem,
            confianca=confianca
        )

    def consultar_experiencias(self, consulta, limite=10):
        self.ultimas_experiencias = buscar_experiencias(
            consulta,
            limite
        )

        return self.ultimas_experiencias

    def recuperar_historico_experiencias(self, limite=20):
        return recuperar_experiencias(limite)

    def recuperar_experiencia_por_id(self, identificador):
        return recuperar_experiencia_por_id(identificador)

    def recuperar_experiencias_da_decisao(self, decisao_id):
        return recuperar_experiencias_por_decisao(decisao_id)

    def contar_experiencias_registradas(self):
        return contar_experiencias()

    def atualizar_experiencia(
        self,
        identificador,
        resultado=None,
        aprendizado=None
    ):
        return atualizar_experiencia(
            identificador,
            resultado,
            aprendizado
        )

    # --------------------------------------------------
    # AVALIACOES DE EXPERIENCIAS
    # --------------------------------------------------

    def avaliar_experiencia(
        self,
        identificador,
        classificacao,
        justificativa,
        origem="usuario",
        confianca=None
    ):
        return avaliar_experiencia(
            identificador=identificador,
            classificacao=classificacao,
            justificativa=justificativa,
            origem=origem,
            confianca=confianca
        )

    def recuperar_avaliacoes_experiencia(self, identificador):
        return recuperar_avaliacoes_experiencia(identificador)

    # --------------------------------------------------
    # PADROES DAS EXPERIENCIAS
    # --------------------------------------------------

    def identificar_padroes_experiencias(self, consulta=None):
        self.ultimos_padroes = identificar_padroes(consulta)
        return self.ultimos_padroes

    def recuperar_padroes_consultados(self):
        return self.raciocinio.recuperar_padroes_consultados()

    def recuperar_avaliacoes_consultadas(self):
        return self.raciocinio.recuperar_avaliacoes_consultadas()

    def recuperar_ultimas_experiencias_consultadas(self):
        return self.raciocinio.recuperar_experiencias_consultadas()

    # --------------------------------------------------
    # PLANEJAMENTO
    # --------------------------------------------------

    def planejar(self, objetivo):
        if not isinstance(objetivo, str) or not objetivo.strip():
            raise ValueError("O objetivo não pode estar vazio.")

        self.ultimas_experiencias = buscar_experiencias(
            objetivo,
            limite=5
        )

        self.ultimos_padroes = identificar_padroes(objetivo)

        self.raciocinio.ultimas_experiencias = (
            self.ultimas_experiencias
        )

        self.raciocinio.ultimos_padroes = (
            self.ultimos_padroes
        )

        self.raciocinio.preparar_contexto_planejamento(
            objetivo
        )

        self.ultimo_plano = self.raciocinio.recuperar_plano()

        self.ultimo_objetivo_planejado = objetivo

        return self.ultimo_plano

    def recuperar_ultimo_plano(self):
        return self.ultimo_plano

    def recuperar_contexto_planejamento(self):
        return self.raciocinio.recuperar_contexto_planejamento()

    def recuperar_estado_planejamento(self):
        if self.ultimo_plano is None:
            return {
                "disponivel": False,
                "objetivo": None,
                "status": "sem_planejamento"
            }

        return {
            "disponivel": True,
            "objetivo": self.ultimo_plano.get("objetivo"),
            "status": self.ultimo_plano.get("status"),
            "total_etapas": len(
                self.ultimo_plano.get("etapas", [])
            ),
            "experiencias_consultadas": self.ultimo_plano.get(
                "quantidade_experiencias",
                0
            )
        }

    def recuperar_ultima_resposta_planejada(self):
        return self.ultima_resposta_planejada

    # --------------------------------------------------
    # AVALIACAO DE DECISOES
    # --------------------------------------------------

    def avaliar(self, acao):
        self.ultima_decisao = avaliar_acao(acao)
        return self.ultima_decisao
