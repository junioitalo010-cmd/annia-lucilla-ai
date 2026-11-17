ANNIA LUCILLA V25 — MF-04 (CANDIDATA EXPERIMENTAL)

Implementa pedidos de atualizacao e exclusao para registros de teste MF-02/MF-03, com confirmacao por codigo de uso unico (valido somente enquanto o processo do servidor permanece ligado). Nenhuma alteracao e realizada antes da confirmacao. Cancelamento e possivel.

Comandos (exemplos):
Luci, guarde a informação de teste cor_favorita: lilás.
Luci, atualize a informação de teste cor_favorita: azul.
Luci, confirme a operacao CODIGO.
Luci, qual é minha cor favorita?
Luci, exclua a informação de teste cor_favorita.
Luci, confirme a operacao CODIGO.
Luci, consulte a informação de teste cor_favorita.

Substitua CODIGO pelo codigo de oito caracteres apresentado pela Luci. Para cancelar: Luci, cancele a operacao CODIGO.

A auditoria mf04_auditoria guarda tipo, identificador e data, nao o valor. ATENCAO: o adaptador SQLite preexistente registra snapshots integrais na tabela revisoes; portanto valores antigos podem permanecer no historico tecnico do banco apos exclusao logica. NAO e apagamento seguro nem eliminacao de backups/historico de conversa. Nao use dados pessoais ou segredos.

Limitacoes: nao ha autenticacao; confirmacoes pendentes sao compartilhadas pelo processo e expiram apenas ao reiniciar/cancelar/confirmar; nao usar fora de localhost. As operacoes e auditoria nao sao uma unica transacao atomica; se auditoria falhar, a resposta avisa. Confirmacao nao sobrevive ao reinicio. Preserva UI V25 e os demais modulos.

Testes isolados com SQLite temporario: criacao, leitura contextual, solicitacao sem alteracao, confirmacao de atualizacao, leitura atualizada, confirmacao de exclusao e persistencia da exclusao apos reabrir banco passaram. Teste na interface Windows ainda pendente.

Executar da pasta extraida:
python -B -X utf8 projeto\iniciar_backend_transferencia.py --port 8788
Abrir http://127.0.0.1:8788/

IMPORTANTE: cada pasta possui banco proprio; dados da MF-03 nao sao migrados automaticamente. Preserve a pasta e o ZIP MF-03 como backup. Se cor_favorita ja existir, nao tente gravar novamente: consulte antes de atualizar.
