"""Inicializador da copia de transferencia; nao altera a instalacao original."""
from pathlib import Path
import os,sys,argparse,socket
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P));sys.dont_write_bytecode=True
def main():
 parser=argparse.ArgumentParser(description="Luci: copia sanitizada, somente loopback")
 parser.add_argument("--port",type=int,default=8766);args=parser.parse_args()
 if not 1024<=args.port<=65535:raise SystemExit("Escolha porta entre 1024 e 65535.")
 try:
  with socket.socket() as probe:probe.bind(("127.0.0.1",args.port))
 except OSError:raise SystemExit("Porta ocupada. Nao encerre o servidor existente; escolha --port diferente.")
 from cerebro.persistencia_sqlite import MemoriaSQLite
 db=P/"dados/memoria.sqlite3"
 if not db.exists():MemoriaSQLite.importar_json(P/"dados/memoria.json",db)
 # Entrada opt-in atual, configurada exclusivamente para os dados desta copia.
 os.environ["LUCI_CANDIDATA_SQLITE"]=str(db)
 from plataforma.app_sqlite import criar_app
 app=criar_app()
 import uvicorn
 print("COPIA DE TRANSFERENCIA: dados iniciais vazios; sem autenticacao integrada.")
 print("Modelo gerador requer Ollama local e llama3.2:3b. Nao expor na LAN/internet.")
 uvicorn.run(app,host="127.0.0.1",port=args.port)
if __name__=="__main__":main()
