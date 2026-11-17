# ANNIA LUCILLA AI (Luci)

Projeto pessoal de assistente de inteligência artificial com execução local, desenvolvido em Python.

## Tecnologias
- Python e FastAPI (API local e WebSocket)
- SQLite (memória persistente)
- Ollama + `llama3.2:3b` (modelo local, instalado separadamente)
- HTML, CSS e JavaScript (interface web V25)
- pandas, scikit-learn e joblib (componentes de classificação)

## Funcionalidades presentes no código
- Interface V25 integrada a um núcleo Python.
- Conversação por WebSocket em servidor local.
- Memória flexível e recuperação contextual, com atualização e exclusão controladas.
- Ferramentas offline para verificar integridade, criar backup SQLite e testar restauração em cópia isolada.

**Estado:** projeto em desenvolvimento. Os testes de MF-01 a MF-05 cobrem cenários específicos; não representam uma auditoria completa de segurança ou garantia de funcionamento em todos os ambientes. A exclusão de memória ativa não garante apagamento físico de revisões antigas.

## Executar no Windows
Pré-requisitos: Python compatível com as dependências, Ollama instalado e modelo local disponível.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r projeto\requirements-execucao.txt
ollama pull llama3.2:3b
python -B -X utf8 projeto\iniciar_backend_transferencia.py --port 8789
```

Acesse http://127.0.0.1:8789/ no mesmo computador.

Se as versões fixadas não forem compatíveis com seu Python, revise as dependências em um ambiente isolado. Não execute o servidor na internet ou na rede local: esta versão não possui autenticação integrada.

## Manutenção da memória
Com o servidor desligado:

```powershell
python -B -X utf8 projeto\mf05_manutencao.py verificar projeto\dados\memoria.sqlite3
python -B -X utf8 projeto\mf05_manutencao.py backup projeto\dados\memoria.sqlite3 backups\memoria_mf05.sqlite3
python -B -X utf8 projeto\mf05_manutencao.py restaurar-copia backups\memoria_mf05.sqlite3 backups\restauracao_teste.sqlite3
```

A restauração cria uma **cópia isolada**, sem ativá-la como banco em uso.

## Privacidade
Esta distribuição de portfólio foi preparada sem o banco SQLite do arquivo recebido, sem históricos pessoais e sem arquivos de backup. Não faça commit de dados reais, tokens, credenciais ou logs. A pasta `projeto/dados` contém apenas dados iniciais de demonstração e metadados estáticos do projeto.

## Autoria
Projeto criado por Italo Junio. Nome: **ANNIA LUCILLA AI**; apelido: **Luci**.

## Licença
Nenhuma licença de redistribuição foi definida neste pacote. Adicione uma licença somente após decidir como deseja permitir o uso do código por terceiros.
