ANNIA LUCILLA V25 — CANDIDATA MF-02 (experimental)

MF-01: auditoria confirmou memoria_longa, backend SQLite transacional, e roteamento controlado no nucleo/central.py.
MF-02: adiciona cerebro/memoria_flexivel.py e roteamento de comandos estritos, sem LLM, para registros de teste nomeados.

Comandos exatos:
Luci, guarde a informação de teste cor_favorita: lilás.
Luci, consulte a informação de teste cor_favorita.

O nome deve ter 2-40 caracteres e o valor 1-200 caracteres. Uma chave existente nao e sobrescrita. Valores sao declaracoes do usuario, nao fatos verificados. Nao salve dados sensiveis. Nao ha autenticacao; use somente localhost.

Limites: reconhecimento por chave exata; nao implementa recuperacao semantica, edicao, exclusao, ou controle robusto de conteudo sensivel. A lista de palavras bloqueadas e somente uma defesa inicial, nao garante protecao de segredos. Nao usar dados pessoais reais nesta candidata.

Execute na pasta extraida: python -B -X utf8 projeto/iniciar_backend_transferencia.py --port 8786
Acesse http://127.0.0.1:8786/
Nao substitua a copia funcional anterior.
