# ANNIA LUCILLA V25 — candidata de memória controlada

Esta candidata preserva o chat V25, as correções matemáticas e a política existente de respostas.

## Escopo da mudança

Adiciona somente dois comandos explícitos e estritos para testar a gravação e leitura de **um código de teste** na memória persistente já existente. Não implementa memória conversacional genérica, aprendizado automático ou alterações de identidade. Comandos não reconhecidos continuam pelo fluxo anterior.

A confirmação de gravação ocorre somente depois de a API local de memória retornar sucesso e de o valor ser relido. O comando de leitura consulta a memória persistente. A chave utilizada é `teste_codigo_autorizado_v1`.

## Teste

1. Extraia em pasta nova, sem substituir a versão funcional.
2. No PowerShell aberto na pasta extraída, execute `python -B -X utf8 projeto\iniciar_backend_transferencia.py --port 8785`.
3. Abra `http://127.0.0.1:8785/`.
4. Envie: `Luci, quero que você guarde na sua memória esta informação de teste: meu código de teste é ESTRELA-42. Confirme se conseguiu salvar.`
5. Envie: `Luci, qual é o código de teste que pedi para você guardar?`
6. Encerre com Ctrl+C, reinicie o mesmo comando e repita a pergunta de leitura.

**Atenção:** esta cópia não tem autenticação integrada. Não exponha a porta à LAN ou à internet. Não use dados pessoais ou segredos neste teste. A memória fica na pasta da candidata; não migra automaticamente para outras versões.

Testes locais realizados: sintaxe, gravação e leitura em JSON isolado, persistência SQLite em arquivo temporário, reabertura do banco, rejeição de comando não reconhecido. Integração com o Ollama e navegador do usuário ainda não testada.
