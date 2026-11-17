/* V25: bridge local para API existente. Não altera memória, modelos ou rotas. */
(() => {
  'use strict';
  const form = document.getElementById('formulario');
  const input = document.getElementById('mensagem');
  const send = document.getElementById('enviar');
  const log = document.getElementById('conversa');
  const status = document.querySelector('.v7-status-label small');
  const tag = document.querySelector('.titulo-chat .tag');
  const notice = document.querySelector('.chat-aviso');
  if (!form || !input || !send || !log) return;
  let socket = null, busy = false, connected = false, waiting = false;
  let retry = 0;
  const setStatus = (state, detail) => {
    if (status) status.textContent = detail;
    if (tag) tag.textContent = state;
    if (notice) notice.textContent = state === 'CONECTADO'
      ? 'Chat conectado ao núcleo local. As outras seções da V25 permanecem demonstrativas.'
      : 'Chat: ' + detail + '. Não há reenvio automático de mensagens.';
    send.disabled = !connected || busy;
  };
  const append = (who, message) => {
    const item = document.createElement('div');
    item.className = 'mensagem ' + (who === 'LUCI' ? 'luci' : 'usuario');
    const name = document.createElement('div'); name.className = 'nome'; name.textContent = who;
    const content = document.createElement('div'); content.className = 'conteudo';
    content.textContent = String(message); content.style.whiteSpace = 'pre-wrap';
    item.append(name, content); log.append(item); log.scrollTop = log.scrollHeight;
  };
  const finish = () => {busy = false;waiting = false;setStatus(connected?'CONECTADO':'DESCONECTADO',connected?'Núcleo local conectado':'Conexão indisponível');};
  const connect = () => {
    if (socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) return;
    if (!['localhost','127.0.0.1','::1','[::1]'].includes(location.hostname)) {
      setStatus('BLOQUEADO','A candidata é exclusiva para acesso local');return;
    }
    setStatus('CONECTANDO','Conectando ao núcleo local');
    socket = new WebSocket((location.protocol === 'https:'?'wss:':'ws:')+'//'+location.host+'/ws');
    socket.addEventListener('open',()=>{connected=true;retry=0;setStatus('CONECTADO','Núcleo local conectado');});
    socket.addEventListener('message',event=>{
      let data;
      try {data=JSON.parse(event.data);}catch {append('LUCI','O servidor enviou dados inválidos.');finish();return;}
      if (data.tipo === 'resposta' && typeof data.mensagem === 'string') append('LUCI',data.mensagem);
      else if (data.tipo === 'erro') append('LUCI','Erro do servidor: '+String(data.mensagem||'Erro desconhecido'));
      else {append('LUCI','Formato de resposta inesperado.');}
      finish();
    });
    socket.addEventListener('close',()=>{
      connected=false;
      if(waiting)append('LUCI','A conexão caiu antes da confirmação da resposta. A mensagem não será reenviada automaticamente.');
      finish();setStatus('DESCONECTADO','Servidor local indisponível');
      if(retry<3){retry++;setTimeout(connect,Math.min(retry*2000,6000));}
    });
    socket.addEventListener('error',()=>setStatus('ERRO','Falha de comunicação com servidor local'));
  };
  form.addEventListener('submit',event=>{
    event.preventDefault();
    const message=input.value.trim();
    if(!message || message.length>10000 || busy || !connected || socket.readyState!==WebSocket.OPEN)return;
    busy=true;waiting=true;send.disabled=true;
    try {socket.send(JSON.stringify({mensagem:message}));append('VOCÊ',message);input.value='';input.dispatchEvent(new Event('input'));setStatus('PROCESSANDO','Luci está processando a mensagem');}
    catch {append('LUCI','Falha ao enviar. Verifique a conexão.');finish();}
  });
  connect();
})();
