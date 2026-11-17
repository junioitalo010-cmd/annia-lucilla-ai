ANNIA LUCILLA V25 — MF-03 (candidata experimental)

Adiciona recuperação contextual CONSERVADORA a MF-02, sem LLM e sem serviço externo.
Perguntas devem terminar em '?' e conter palavras de consulta (qual, quais, quanto, quanta, lembra, recorda), além de TODOS os termos da chave separados por underscore, cada termo com mais de 2 caracteres. Apenas chaves com 2+ termos são elegíveis. Em caso de ambiguidade, exige consulta pelo nome exato. Sem correspondência, segue fluxo anterior; não inventa lembrança.

Exemplo:
Luci, guarde a informação de teste cor_favorita: lilás.
Luci, qual é minha cor favorita?

IMPORTANTE: ao extrair em pasta nova, a memória da pasta MF-02 NÃO é migrada automaticamente. O teste deve gravar novamente 'cor_favorita' na MF-03 usando dados fictícios, ou realizar migração segura manual em etapa separada. Não copie bancos SQLite com o servidor ligado. Não sobrescreva o backup MF-02.

Teste de unidade isolado com banco SQLite temporário: gravação, consulta direta, consulta contextual, pergunta sem registro e recuperação após reabertura passaram. Interface e núcleo não foram alterados. Ainda não testado em execução real no Windows.

Execute na pasta extraída:
python -B -X utf8 projeto\iniciar_backend_transferencia.py --port 8787
Abra http://127.0.0.1:8787/

Limites: isto NÃO é busca semântica geral; não entende sinônimos nem variações complexas, não edita/exclui registros e não tem autenticação. Uso somente localhost e dados fictícios.
