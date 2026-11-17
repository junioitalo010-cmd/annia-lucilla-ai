ANNIA LUCILLA V25 — MF-05, candidata de manutencao offline

Preserva a interface e os modulos da MF-04. Adiciona projeto/mf05_manutencao.py para verificar integridade SQLite, gerar backup consistente com API sqlite3.backup e criar copia isolada para teste de restauracao. Nao ativa restauracao nem altera o banco em uso. Desligue o servidor antes de executar.

Na pasta extraida, comandos PowerShell:
python -B -X utf8 projeto\mf05_manutencao.py verificar projeto\dados\memoria.sqlite3
python -B -X utf8 projeto\mf05_manutencao.py backup projeto\dados\memoria.sqlite3 backups\memoria_mf05.sqlite3
python -B -X utf8 projeto\mf05_manutencao.py restaurar-copia backups\memoria_mf05.sqlite3 backups\restauracao_teste.sqlite3

Os caminhos de destino devem ser novos; nunca sobrescreve. Nao migrar dados automaticamente. O backup contem dados e snapshots integrais de revisoes, inclusive valores excluidos logicamente; proteja-o. A verificacao detecta erros SQLite, estrutura v3 e consistencia basica de revisoes, mas nao detecta todas as corrupcoes semanticas ou adulteracoes sofisticadas. O historico mf04_auditoria nao e transacional com alteracoes. Nao ha autenticacao e a interface deve continuar apenas em localhost.

Testes isolados: verificar, backup, copia isolada e verificacao da copia. A integracao Windows e o teste de falhas reais permanecem pendentes. Nao usar dados sensiveis.

Executar a interface como na MF-04:
python -B -X utf8 projeto\iniciar_backend_transferencia.py --port 8789
Abrir http://127.0.0.1:8789/
