# Correção contextual conservadora

Ajuste limitado ao reconhecimento de perguntas didáticas: permite vocativo inicial «Luci,» e «explique com suas próprias palavras». Mantém verificadores, bloqueios, política de proveniência e salvamento intactos. A comunicação de conhecimento geral continua rotulada como não verificada externamente e não é promovida à memória aprovada.

Executar na pasta extraída: `python -B -X utf8 projeto\iniciar_backend_transferencia.py --port 8782`

Teste: «Luci, explique com suas próprias palavras o que é inteligência artificial e dê dois exemplos de utilização.»

Resultado esperado: explicação precedida do aviso «Conhecimento geral do modelo — não verificado externamente.»; se o modelo alegar operações, fontes ou capacidades não verificadas, a resposta deve continuar bloqueada.

Não expor na LAN/internet; sem autenticação integrada. A correção foi testada de forma isolada, não validada em execução real no Windows.
