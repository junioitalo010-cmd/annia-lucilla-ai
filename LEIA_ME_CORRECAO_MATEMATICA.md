# ANNIA LUCILLA V25 — candidata de distribuição matemática

Mudança pontual em `projeto/cerebro/calculo.py`: reconhecimento determinístico de enunciados com **N caixas, M livros por caixa e P pessoas**, com distribuição inteira, usando cálculo Python exato. O resultado passa pelo verificador já existente como calculadora local. Não usa o modelo de linguagem para validar a própria resposta.

**Limites:** reconhece apenas a formulação textual fechada testada. Se a divisão não for exata ou o enunciado for diferente, a rota não se aplica. Isso não é um solucionador geral de problemas matemáticos. Nenhum arquivo de memória foi intencionalmente modificado.

## Iniciar no Windows

1. Extraia em pasta nova; não substitua a versão anterior.
2. Abra PowerShell na pasta extraída e execute:
   `python -B -X utf8 projeto\iniciar_backend_transferencia.py --port 8783`
3. Abra `http://127.0.0.1:8783/`.
4. Envie: `Luci, tenho 3 caixas com 12 livros em cada uma. Vou distribuir todos os livros igualmente entre 4 pessoas. Quantos livros cada pessoa receberá? Explique seu raciocínio.`

Esperado: 9 livros por pessoa, com os dois passos. Testes isolados passaram; integração no PC do usuário ainda não testada. Não expor o servidor na rede: autenticação não integrada.
