# ANNIA LUCILLA AI — V25 candidata integrada

Esta é uma **cópia separada** do código sanitizado recebido. A V25 original foi mantida byte a byte em `referencia_visual_original/`. A cópia em `projeto/plataforma/templates/v25_integrada.html` habilita o chat e inclui `static/js/v25_integracao.js`.

## Como executar no Windows

1. Extraia este ZIP para uma **pasta nova**, fora da instalação original.
2. Abra PowerShell na pasta extraída. Crie e ative um ambiente virtual Python próprio, se necessário.
3. Instale as dependências de `projeto/requirements-execucao.txt` no ambiente virtual, se ainda não estiverem disponíveis.
4. Execute `python -B -X utf8 projeto/iniciar_backend_transferencia.py --port 8780`.
5. Abra `http://127.0.0.1:8780/` no mesmo computador.
6. Para geração livre, o Ollama e o modelo `llama3.2:3b` precisam estar disponíveis separadamente. Operações locais do núcleo podem funcionar sem eles.

**Não use a porta 8766** se o servidor original estiver ativo. Não altere o host para `0.0.0.0` nem exponha esta candidata na LAN ou internet: **não há autenticação integrada**. O chat utiliza `/ws` e a API original; não cria rotas PI-006.

## Escopo e limitações

- Apenas a seção Chat da V25 foi conectada ao WebSocket real.
- Navegação, projetos, mapa mental, painéis e demais recursos continuam demonstrativos, conforme a V25 original.
- O backend pode persistir mensagens **nos dados da própria cópia**, mesmo que a conexão caia. A cópia usa dados sanitizados, não os dados pessoais originais.
- O frontend não reenvia mensagens automaticamente após falhas.
- O histórico do chat não é restaurado na interface após recarregar a página.
- Testes estáticos e testes isolados não substituem validação manual em Windows com Ollama.
- O arquivo `projeto/plataforma/templates/index.html` antigo foi mantido como referência, mas não é a página inicial desta candidata.
- Nenhuma versão 1.1 foi declarada aprovada.

## Arquivos alterados somente nesta cópia

- `projeto/plataforma/app.py`: rota `/` entrega a V25 integrada.
- `projeto/plataforma/templates/v25_integrada.html`: cópia modificada da V25 original.
- `projeto/plataforma/static/js/v25_integracao.js`: conexão WebSocket e estados do chat.
