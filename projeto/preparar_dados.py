from pathlib import Path
import shutil

base = Path(__file__).resolve().parent / "dados"
for nome in ("memoria.json", "experiencias.json", "conhecimentos.json", "decisoes.json"):
    destino = base / nome
    origem = base / (nome + ".example")
    if not destino.exists():
        shutil.copy2(origem, destino)
        print("Criado:", destino)
