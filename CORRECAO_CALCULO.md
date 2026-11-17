# Correção isolada — reconhecimento de pergunta matemática

Esta candidata preserva a V25 e o backend original, alterando apenas `projeto/cerebro/calculo.py` para reconhecer o sufixo exato “Explique como chegou ao resultado” após uma expressão aritmética. A calculadora local retorna a expressão e o resultado exato; uma explicação detalhada passo a passo ainda não foi implementada.

O verificador, o mecanismo de confiabilidade, a API e o frontend não foram alterados.

## Como testar no Windows

1. Encerre a candidata anterior com Ctrl+C, sem apagar a pasta.
2. Extraia este ZIP em outra pasta.
3. Execute `python -B -X utf8 projeto\iniciar_backend_transferencia.py --port 8781`.
4. Abra `http://127.0.0.1:8781/` e pergunte: `Luci, quanto é 17 × 23? Explique como chegou ao resultado.`

**Atenção:** a palavra “Luci,” no começo ainda não é reconhecida pela calculadora, portanto teste primeiro a forma `Quanto é 17 × 23? Explique como chegou ao resultado.`. A resposta esperada da calculadora é `17 * 23 = 391.`. A comunicação completa com Ollama no computador do proprietário não foi testada neste ambiente. Não expor o servidor à rede.
