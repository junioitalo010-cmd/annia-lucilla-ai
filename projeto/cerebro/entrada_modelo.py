"""Entrada interna com mensagem atual explicita; preserva compatibilidade str."""
class EntradaModelo(str):
    def __new__(cls,texto,contexto,mensagem,turnos=(),foco_social=False,modo_conversa=None,reformulacao_social=False):
        if not all(isinstance(s,str) for s in (texto,contexto,mensagem)):
            raise TypeError('Entrada de modelo deve conter textos.')
        if not mensagem.strip() or len(mensagem)>10000 or len(texto)>36000 or len(contexto)>36000:
            raise ValueError('Entrada de modelo fora dos limites.')
        obj=super().__new__(cls,texto)
        obj._contexto=contexto
        obj._mensagem=mensagem
        if not isinstance(turnos,(tuple,list)) or len(turnos)>12:
            raise ValueError('Turnos fora do limite.')
        clean=[]
        for turno in turnos:
            if not isinstance(turno,(tuple,list)) or len(turno)!=2 or not isinstance(turno[0],str) or turno[0] not in {'user','assistant'} or not isinstance(turno[1],str) or not 1<=len(turno[1])<=2000:
                raise ValueError('Turno inválido.')
            clean.append(tuple(turno))
        if sum(len(t[1]) for t in clean)>12000:raise ValueError('Histórico estruturado fora do limite.')
        obj._turnos=tuple(clean)
        if type(foco_social) is not bool:raise ValueError('Foco social inválido.')
        obj._foco_social=foco_social
        if type(reformulacao_social) is not bool or (reformulacao_social and not foco_social):
            raise ValueError("Reformulacao exige foco social explicito.")
        obj._reformulacao_social=reformulacao_social
        if modo_conversa not in {None, 'memoria_atual', 'esclarecimento', 'convite_assunto', 'conhecimento_geral'}:
            raise ValueError('Modo de conversa invalido.')
        obj._modo_conversa=modo_conversa
        return obj

    @property
    def contexto(self):return self._contexto

    @property
    def mensagem(self):return self._mensagem

    @property
    def turnos(self):return self._turnos

    @property
    def foco_social(self):return self._foco_social

    @property
    def modo_conversa(self):return self._modo_conversa

    @property
    def reformulacao_social(self):return self._reformulacao_social
