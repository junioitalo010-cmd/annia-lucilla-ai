
from nucleo.central import NucleoCentral


def main():

    print("\n=== TESTE DE AQUISICAO DA ANNIA LUCILLA ===")

    luci = NucleoCentral()

    print("\n1. Testando aquisicao com nucleo desligado...")

    resultado_inativo = luci.adquirir_conhecimento(
        "Como funciona o sistema de refrigeracao de uma geladeira?"
    )

    print(resultado_inativo)

    if resultado_inativo.get("estado") != "nucleo_inativo":
        print("ERRO: a protecao de nucleo inativo falhou.")
        return

    print("\n2. Iniciando o nucleo central...")

    if not luci.iniciar():
        print("ERRO: nao foi possivel iniciar o nucleo.")
        return

    print("\n3. Estado atual do nucleo:")
    print(luci.recuperar_estado())

    print("\n4. Iniciando aquisicao de conhecimento...")

    relatorio = luci.adquirir_conhecimento(
        consulta=(
            "Como funciona o sistema de refrigeracao "
            "de uma geladeira?"
        ),
        quantidade=5,
        limite=10
    )

    print("\n5. Relatorio da aquisicao:")
    print(relatorio)

    print("\n6. Estado da ultima aquisicao:")
    print(luci.recuperar_estado_aquisicao())

    print("\n7. Encerrando nucleo...")

    luci.encerrar()

    print("\n=== TESTE FINALIZADO ===")


if __name__ == "__main__":
    main()
