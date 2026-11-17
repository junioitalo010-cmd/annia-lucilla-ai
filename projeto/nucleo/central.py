
from nucleo.coordenador import Coordenador


class NucleoCentral:

    VERSAO = "1.0"

    def __init__(self, funcao_modelo=None):
        self.coordenador = Coordenador()

        self.ativo = False
        self.estado = "desligado"

        self.ultima_operacao = None
        self.ultimo_erro = None

        if funcao_modelo is not None:
            self.conectar_modelo(funcao_modelo)

    # --------------------------------------------------
    # VALIDACOES
    # --------------------------------------------------

    @staticmethod
    def validar_texto(valor, nome):
        if not isinstance(valor, str) or not valor.strip():
            raise ValueError(f"{nome} nao pode estar vazio.")

        return valor.strip()

    @staticmethod
    def validar_limite(valor, nome, minimo=1, maximo=100):
        if isinstance(valor, bool) or not isinstance(valor, int):
            raise ValueError(f"{nome} precisa ser um numero inteiro.")

        if not minimo <= valor <= maximo:
            raise ValueError(
                f"{nome} precisa estar entre {minimo} e {maximo}."
            )

        return valor

    # --------------------------------------------------
    # INICIALIZACAO
    # --------------------------------------------------

    def iniciar(self):
        print("================================")
        print("       ANNIA LUCILLA")
        print("       NUCLEO CENTRAL")
        print("================================")

        self.estado = "inicializando"
        self.ativo = False
        self.ultimo_erro = None

        try:
            from cerebro.interacao import (
                preparar_nucleo,
                consultar_ollama
            )

            preparar_nucleo()

            self.conectar_modelo(consultar_ollama)

            self.ultima_operacao = "inicializacao"

            print("Cerebro local conectado.")
            print("Memoria e conhecimentos disponiveis.")
            print("Nucleo inicializado com sucesso.")

            return True

        except Exception as erro:
            self.ativo = False
            self.estado = "erro"
            self.ultimo_erro = str(erro)

            print("Nao foi possivel inicializar o nucleo.")
            print(f"Detalhes: {erro}")

            return False

    # --------------------------------------------------
    # ENCERRAMENTO
    # --------------------------------------------------

    def encerrar(self):
        self.ativo = False
        self.estado = "desligado"
        self.ultima_operacao = "encerramento"

        print("Nucleo Central desativado.")

        return True

    # --------------------------------------------------
    # CONEXAO COM MODELO
    # --------------------------------------------------

    def conectar_modelo(self, funcao_modelo):

        if not callable(funcao_modelo):
            raise ValueError(
                "A funcao do modelo precisa ser executavel."
            )

        self.coordenador.conectar_modelo(funcao_modelo)

        self.ativo = True
        self.estado = "ativo"
        self.ultimo_erro = None
        self.ultima_operacao = "conexao_com_modelo"

        return True

    # --------------------------------------------------
    # VERIFICACAO DE DISPONIBILIDADE
    # --------------------------------------------------

    def _verificar_disponibilidade(self):
        if not self.ativo:
            return False

        motor = getattr(self.coordenador, "raciocinio", None)

        funcao_modelo = getattr(
            motor,
            "funcao_modelo",
            None
        )

        return callable(funcao_modelo)

    def _registrar_erro(self, operacao, erro):
        self.ultimo_erro = str(erro)
        self.ultima_operacao = operacao

        print(
            f"Erro na operacao '{operacao}': {erro}"
        )

    # --------------------------------------------------
    # PROCESSAMENTO DE MENSAGENS
    # --------------------------------------------------

    def processar(self, mensagem):

        self.validar_texto(mensagem, "A mensagem")

        if not self._verificar_disponibilidade():
            return "O Nucleo Central ainda nao esta disponivel."

        self.ultima_operacao = "conversa"
        self.ultimo_erro = None

        from cerebro.memoria_longa import guardar_historico

        try:
            guardar_historico("usuario", mensagem)
            # Operacoes explicitas e restritas de memoria nao dependem de
            # promessas do modelo de linguagem nem da classificacao textual.
            from cerebro.memoria_chat_controlada import processar_comando
            resposta_memoria = processar_comando(mensagem)
            if resposta_memoria is None:
                from cerebro.memoria_flexivel import processar_comando as memoria_flexivel
                resposta_memoria = memoria_flexivel(mensagem)
            if resposta_memoria is not None:
                guardar_historico("luci", resposta_memoria)
                return resposta_memoria
            resposta = self.coordenador.conversar(mensagem)

            verificacao = self.coordenador.recuperar_verificacao()
            confiabilidade = self.coordenador.recuperar_confiabilidade()

            print("\n===== DIAGNOSTICO DA LUCI =====")
            print("VERIFICACAO:", verificacao)
            print("CONFIABILIDADE:", confiabilidade)
            print("===== FIM DO DIAGNOSTICO =====\n")

            print("\n===== DIAGNOSTICO DA PLATAFORMA =====")
            print("VERIFICACAO:")
            print(verificacao)

            print("\nCONFIABILIDADE:")
            print(confiabilidade)

            print("\n===== FIM DO DIAGNOSTICO =====\n")

            liberada = (
                isinstance(verificacao, dict)
                and verificacao.get("bloquear_resposta") is False
                and isinstance(confiabilidade, dict)
                and confiabilidade.get("bloquear_resposta") is False
            )

            from cerebro.conhecimento_geral import validar_entrega
            politica=getattr(self.coordenador.raciocinio,'ultima_politica_resposta',None)
            if validar_entrega(resposta,politica):
                # Historico de fala entregue, nao registro de conhecimento aprovado.
                guardar_historico('luci',resposta)
            elif liberada:
                from cerebro.interacao import registrar_historico_aprovado

                registrar_historico_aprovado(mensagem, resposta)
                guardar_historico("luci", resposta)
            else:
                recuperacao=self.coordenador.raciocinio.ultima_recuperacao
                if (isinstance(recuperacao,dict)
                    and recuperacao.get('geracao_original_bloqueada') is True
                    and recuperacao.get('resposta_comunicada')==resposta
                    and isinstance(recuperacao.get('verificacao_limitacao'),dict)
                    and recuperacao['verificacao_limitacao'].get('bloquear_resposta') is False
                    and isinstance(recuperacao.get('confiabilidade_limitacao'),dict)
                    and recuperacao['confiabilidade_limitacao'].get('bloquear_resposta') is False):
                    # Guarda apenas a limitacao entregue, nao a geracao rejeitada.
                    # Nao passa por registrar_historico_aprovado da geracao.
                    guardar_historico('luci',resposta)

            return resposta

        except Exception as erro:
            self._registrar_erro("conversa", erro)

            return (
                "Nao foi possivel concluir o processamento "
                "da mensagem."
            )

    def processar_com_planejamento(self, mensagem, objetivo):

        self.validar_texto(mensagem, "A mensagem")
        self.validar_texto(objetivo, "O objetivo")

        if not self._verificar_disponibilidade():
            return "O Nucleo Central ainda nao esta disponivel."

        self.ultima_operacao = "conversa_com_planejamento"
        self.ultimo_erro = None

        try:
            return self.coordenador.conversar_com_planejamento(
                mensagem,
                objetivo
            )

        except Exception as erro:
            self._registrar_erro(
                "conversa_com_planejamento",
                erro
            )

            return (
                "Nao foi possivel concluir a conversa "
                "com planejamento."
            )

    # --------------------------------------------------
    # AQUISICAO DE CONHECIMENTO
    # --------------------------------------------------

    def adquirir_conhecimento(
        self,
        consulta,
        quantidade=5,
        limite=10
    ):
        self.validar_texto(consulta, "A consulta")

        self.validar_limite(
            quantidade,
            "A quantidade",
            1,
            10
        )

        self.validar_limite(
            limite,
            "O limite",
            1,
            100
        )

        if not self.ativo:
            return {
                "consulta": consulta,
                "estado": "nucleo_inativo",
                "erro": (
                    "O Nucleo Central precisa estar ativo "
                    "para realizar a aquisicao."
                ),
                "conhecimento_salvo": False,
                "conhecimento_verificado": False
            }

        self.ultima_operacao = "aquisicao_de_conhecimento"
        self.ultimo_erro = None

        try:
            relatorio = self.coordenador.adquirir_conhecimento(
                consulta=consulta,
                quantidade=quantidade,
                limite=limite
            )

            if not isinstance(relatorio, dict):
                raise RuntimeError(
                    "O fluxo retornou um relatorio invalido."
                )

            return relatorio

        except Exception as erro:
            self._registrar_erro(
                "aquisicao_de_conhecimento",
                erro
            )

            return {
                "consulta": consulta,
                "estado": "erro_na_aquisicao",
                "erros": [str(erro)],
                "conhecimento_salvo": False,
                "conhecimento_verificado": False
            }

    def recuperar_ultima_aquisicao(self):
        return self.coordenador.recuperar_ultima_aquisicao()

    def recuperar_estado_aquisicao(self):
        return self.coordenador.recuperar_estado_aquisicao()

    # --------------------------------------------------
    # PLANEJAMENTO
    # --------------------------------------------------

    def planejar(self, objetivo):

        self.validar_texto(objetivo, "O objetivo")

        if not self._verificar_disponibilidade():
            return None

        self.ultima_operacao = "planejamento"
        self.ultimo_erro = None

        try:
            return self.coordenador.planejar(objetivo)

        except Exception as erro:
            self._registrar_erro("planejamento", erro)
            return None

    def recuperar_plano(self):
        return self.coordenador.recuperar_ultimo_plano()

    def recuperar_estado_planejamento(self):
        return self.coordenador.recuperar_estado_planejamento()

    def recuperar_contexto_planejamento(self):
        return self.coordenador.recuperar_contexto_planejamento()

    # --------------------------------------------------
    # DECISOES E AVALIACOES
    # --------------------------------------------------

    def avaliar_acao(self, acao):

        self.validar_texto(acao, "A acao")

        if not self.ativo:
            return None

        self.ultima_operacao = "avaliacao"

        try:
            return self.coordenador.avaliar(acao)

        except Exception as erro:
            self._registrar_erro("avaliacao", erro)
            return None

    def recuperar_decisoes(self):
        return self.coordenador.recuperar_historico_decisoes()

    def contar_decisoes(self):
        return self.coordenador.contar_decisoes_registradas()

    # --------------------------------------------------
    # MEMORIA DE EXPERIENCIAS
    # --------------------------------------------------

    def recuperar_experiencias(self, limite=20):
        self.validar_limite(
            limite,
            "O limite de experiencias",
            1,
            100
        )

        return self.coordenador.recuperar_historico_experiencias(
            limite
        )

    def contar_experiencias(self):
        return self.coordenador.contar_experiencias_registradas()

    def identificar_padroes(self, consulta=None):
        if consulta is not None:
            self.validar_texto(consulta, "A consulta")

        return self.coordenador.identificar_padroes_experiencias(
            consulta
        )

    # --------------------------------------------------
    # VERIFICACAO E CONFIABILIDADE
    # --------------------------------------------------

    def recuperar_verificacao(self):
        return self.coordenador.recuperar_verificacao()

    def recuperar_confiabilidade(self):
        return self.coordenador.recuperar_confiabilidade()

    # --------------------------------------------------
    # ESTADO DO NUCLEO
    # --------------------------------------------------

    def recuperar_estado(self):
        from cerebro.memoria_longa import estado_persistencia
        memoria = estado_persistencia()
        degradado = self.ativo and memoria['disponivel'] is False

        return {
            "nome": "ANNIA LUCILLA",
            "versao": self.VERSAO,
            "ativo": self.ativo,
            "estado": 'degradado' if degradado else self.estado,
            "memoria": memoria,
            "ultima_operacao": self.ultima_operacao,
            "ultimo_erro": self.ultimo_erro,
            "modelo_conectado": (
                self._verificar_disponibilidade()
            ),
            "aquisicao_disponivel": self.ativo and not degradado,
            "ultima_aquisicao": (
                self.recuperar_estado_aquisicao()
            )
        }
