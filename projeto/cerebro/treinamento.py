 
from pathlib import Path
import pandas as pd
import joblib

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, classification_report

PASTA = Path(__file__).resolve().parent.parent
TREINO = PASTA / "dados" / "treinamento.csv"
TESTE = PASTA / "dados" / "teste.csv"
MODELO = PASTA / "modelos" / "annia_sentimentos.joblib"


def treinar():
    dados_treino = pd.read_csv(TREINO)
    dados_teste = pd.read_csv(TESTE)

    print("\nCOLUNAS DO TREINAMENTO:", dados_treino.columns.tolist())
    print("COLUNAS DO TESTE:", dados_teste.columns.tolist())

    print("\nPRIMEIRAS LINHAS DO TESTE:")
    print(dados_teste.head())

    print("\nExemplos de treinamento:", len(dados_treino))
    print("Exemplos de teste:", len(dados_teste))

    frases_treino = dados_treino["texto"]
    sentimentos_treino = dados_treino["sentimento"]

    frases_teste = dados_teste["texto"]
    sentimentos_teste = dados_teste["sentimento"]

    modelo = Pipeline([
        ("vetorizador", TfidfVectorizer()),
        ("classificador", LogisticRegression(max_iter=1000))
    ])

    modelo.fit(frases_treino, sentimentos_treino)

    previsoes = modelo.predict(frases_teste)

    print("\nAcuracia:", accuracy_score(sentimentos_teste, previsoes) * 100, "%")
    print("\nRelatorio:")
    print(classification_report(sentimentos_teste, previsoes, zero_division=0))

    MODELO.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(modelo, MODELO)

    print("\nModelo salvo em:", MODELO)


if __name__ == "__main__":
    treinar()
