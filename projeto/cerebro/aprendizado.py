 
# ANNIA LUCILLA AI
# Modulo de leitura de dados

from pathlib import Path
import pandas as pd

# Localizar a pasta principal do projeto
PASTA_PROJETO = Path(__file__).resolve().parent.parent

# Localizar nossa base de treinamento
ARQUIVO_DADOS = PASTA_PROJETO / "dados" / "treinamento.csv"


# Funcao para carregar os dados
def carregar_dados():

    dados = pd.read_csv(ARQUIVO_DADOS)

    print("\nTOTAL DE FRASES:", len(dados))

    print("\nDISTRIBUICAO:")
    print(dados["sentimento"].value_counts())

    return dados


# Executar o modulo
if __name__ == "__main__":

    dados = carregar_dados()

    print("================================")
    print("      ANNIA LUCILLA AI")
    print("================================")

    print("\nBase de conhecimento carregada!")

    print("\nPrimeiros exemplos:")
    print(dados.head())

    print("\nQuantidade de exemplos:")
    print(len(dados))

    print("\nDistribuicao dos sentimentos:")
    print(dados["sentimento"].value_counts())
