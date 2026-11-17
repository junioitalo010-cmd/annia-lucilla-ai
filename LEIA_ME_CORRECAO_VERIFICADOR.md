# Correção do verificador de cálculos em múltiplas frases

O cálculo de distribuição de livros já era produzido corretamente pela calculadora local, mas o verificador dividia a resposta em três afirmações e tentava comparar cada uma com a resposta integral, causando bloqueio.

A alteração está em `projeto/nucleo/verificador.py`: somente quando a **resposta completa** coincide exatamente com a saída recalculada pelo motor determinístico e seu estado é `calculado`, as frases que compõem essa resposta recebem a evidência `apoio_calculo_local`.

Não é concedido suporte a respostas alteradas, com frases extras ou com resultado diferente. Não há desativação do modo rigoroso.

## Testes isolados
- Resposta original: 3 afirmações apoiadas, sem bloqueio.
- Resultado adulterado: bloqueado.
- Texto extra inserido: bloqueado.

## Execução local
Extraia em pasta nova, não sobrescreva versões anteriores. Na pasta que contém `projeto`, execute:

`python -B -X utf8 projeto\iniciar_backend_transferencia.py --port 8784`

Abra `http://127.0.0.1:8784/` e repita a pergunta dos livros. Testes de integração no Windows e com Ollama não foram realizados aqui.

**Segurança:** sem autenticação integrada. Não exponha o servidor à rede local ou internet.
