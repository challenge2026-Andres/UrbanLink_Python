import time

FATOR_CONVERSAO_BILHETES = 0.05  
MENU_PRINCIPAL = (
    "[1] Gerenciar pontos (CRUD)",
    "[2] Consultar histórico de tarefas",
    "[0] Sair",
)

SUBMENU_PONTOS = (
    "[1] Consultar pontos",
    "[2] Adicionar pontos",
    "[3] Atualizar pontos",
    "[4] Excluir pontos",
    "[5] Converter pontos em bilhetes",
    "[0] Voltar ao menu principal",
) 

def exibir_menu(titulo, opcoes):
    print(f"\n - - - - - - | {titulo} | - - - - - - -")
    for item in opcoes:
        print(item)
    return input("Escolha uma opção: ").strip()


def ler_inteiro(mensagem):
    while True:
        try:
            valor = int(input(mensagem))
        except ValueError:
            print("Valor inválido! Digite apenas números inteiros.")
        else:
            return valor


def validar_quantidade(quantidade, minimo=0, maximo=None):
    if quantidade < minimo:
        return False
    if maximo is not None and quantidade > maximo:
        return False
    return True


def registrar_historico(historico, tipo, detalhe=""):
    historico.append({
        "tipo": tipo,
        "detalhe": detalhe,
        "data_hora": time.strftime("%d/%m/%Y %H:%M:%S"),
    })
    return historico


def calcular_estatisticas(valores):
    if not valores:
        return None
    return {
        "maior": max(valores),
        "menor": min(valores),
        "media": sum(valores) / len(valores),
    }

def consultar_pontos(pontos, historico):
    print("\nConsultando...")
    time.sleep(1.5)
    print("------------------------------------")
    print(f"Pontos acumulados: {pontos}")
    print("------------------------------------")
    return registrar_historico(historico, "Consulta de pontos")


def adicionar_pontos(pontos, historico, historico_adicionados):
    print("----------------------------------------------------")
    try:
        qtd_pontos = ler_inteiro("Digite a quantidade de pontos que deseja adicionar:\n")
        while not validar_quantidade(qtd_pontos, minimo=1):
            print("Digite um valor inteiro maior que zero.")
            qtd_pontos = ler_inteiro("Digite a quantidade de pontos que deseja adicionar:\n")
    except Exception as erro:
        print(f"Não foi possível concluir a adição de pontos: {erro}")
    else:
        pontos += qtd_pontos
        historico_adicionados.append(qtd_pontos)
        print("\nAdicionando os pontos...")
        time.sleep(1.5)
        print("Pontos adicionados com sucesso!")
        historico = registrar_historico(historico, "Adição de pontos", f"+{qtd_pontos} pontos")
    finally:
        print("----------------------------------------------------")
    return pontos, historico, historico_adicionados


def atualizar_pontos(pontos, historico, historico_atualizados):
    print("----------------------------------------------")
    print(f"Saldo atual de pontos: {pontos}")
    try:
        qtd_pontos = ler_inteiro("Digite a nova quantidade do saldo de pontos:\n")
        while not validar_quantidade(qtd_pontos, minimo=0):
            print("Digite um valor inteiro maior ou igual a zero.")
            qtd_pontos = ler_inteiro("Digite a nova quantidade do saldo de pontos:\n")
    except Exception as erro:
        print(f"Não foi possível concluir a atualização de pontos: {erro}")
    else:
        pontos = qtd_pontos
        historico_atualizados.append(qtd_pontos)
        print("\nAtualizando os pontos...")
        time.sleep(1.5)
        print("Pontos atualizados com sucesso!")
        historico = registrar_historico(historico, "Atualização de pontos", f"novo saldo: {qtd_pontos}")
    finally:
        print("----------------------------------------------")
    return pontos, historico, historico_atualizados


def excluir_pontos(pontos, historico, historico_excluidos):
    if pontos <= 0:
        print("Você não possui pontos para excluir.")
        return pontos, historico, historico_excluidos

    print("---------------------------------------------------")
    try:
        qtd_pontos = ler_inteiro("Digite a quantidade de pontos que deseja excluir:\n")
        while not validar_quantidade(qtd_pontos, minimo=0, maximo=pontos):
            print("Valor inválido! Não pode ser negativo nem maior que o saldo.")
            qtd_pontos = ler_inteiro("Digite a quantidade de pontos que deseja excluir:\n")
    except Exception as erro:
        print(f"Não foi possível concluir a exclusão de pontos: {erro}")
    else:
        pontos -= qtd_pontos
        historico_excluidos.append(qtd_pontos)
        print("\nExcluindo os pontos...")
        time.sleep(2)
        print("Pontos excluídos com sucesso!")
        historico = registrar_historico(historico, "Exclusão de pontos", f"-{qtd_pontos} pontos")
    finally:
        print("---------------------------------------------------")
    return pontos, historico, historico_excluidos

def converter_bilhetes(pontos, historico):
    print("------------------------------------")
    print("\nFazendo o cálculo da conversão...")
    time.sleep(1.5)
    bilhetes = int(pontos * FATOR_CONVERSAO_BILHETES)
    print(f"Pontos acumulados: {pontos}")
    print(f"A sua quantidade de pontos acumulados equivale a: {bilhetes} bilhetes.")
    print("------------------------------------")
    historico = registrar_historico(historico, "Conversão em bilhetes", f"{bilhetes} bilhetes")
    return bilhetes, historico

def consultar_historico(historico, historico_adicionados, historico_atualizados, historico_excluidos):
    print("\nBuscando o histórico...")
    time.sleep(1.5)
    print("\n- - - HISTÓRICO DE TAREFAS (DA MAIS ANTIGA ATÉ A MAIS RECENTE): - - -\n")

    for item in historico:
        detalhe = f" ({item['detalhe']})" if item["detalhe"] else ""
        print(f"-> [{item['data_hora']}] {item['tipo']}{detalhe}")

    print(f"\nTotal de atividades realizadas:\n{len(historico)}")
    historico = registrar_historico(historico, "Consulta do Histórico de Tarefas")

    print("\n- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n")

    grupos = (
        ("NA ADIÇÃO DE PONTOS", historico_adicionados, "adicionados"),
        ("NA ATUALIZAÇÃO DE PONTOS", historico_atualizados, "inseridos"),
        ("NA EXCLUSÃO DE PONTOS", historico_excluidos, "excluídos"),
    )

    for titulo, valores, rotulo in grupos:
        estatisticas = calcular_estatisticas(valores)
        print("----------")
        if estatisticas is None:
            acao = titulo.split(" ", 2)[-1].lower()
            print(f"Ainda não foi feita nenhuma {acao}.")
            continue
        print(f"{titulo}:")
        print(f"Maior valor {rotulo}: {estatisticas['maior']}")
        print(f"Menor valor {rotulo}: {estatisticas['menor']}")
        print(f"Média geral dos pontos {rotulo}: {estatisticas['media']:.2f}")

    print("\n- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n")
    return historico

def menu_gerenciar_pontos(pontos, historico, historico_adicionados, historico_atualizados, historico_excluidos):
    opcao = exibir_menu("SUBMENU | GERENCIAR PONTOS", SUBMENU_PONTOS)
    while opcao != "0":
        match opcao:
            case "1":
                historico = consultar_pontos(pontos, historico)
            case "2":
                pontos, historico, historico_adicionados = adicionar_pontos(
                    pontos, historico, historico_adicionados)
            case "3":
                pontos, historico, historico_atualizados = atualizar_pontos(
                    pontos, historico, historico_atualizados)
            case "4":
                pontos, historico, historico_excluidos = excluir_pontos(
                    pontos, historico, historico_excluidos)
            case "5":
                _, historico = converter_bilhetes(pontos, historico)
            case _:
                print("Opção inválida! Tente novamente.")

        opcao = exibir_menu("SUBMENU | GERENCIAR PONTOS", SUBMENU_PONTOS)

    return pontos, historico, historico_adicionados, historico_atualizados, historico_excluidos

def main():
    pontos = 0
    historico = []
    historico_adicionados = []
    historico_atualizados = []
    historico_excluidos = []

    print(" - - - - - - - - - - - - - - - - - - - ")
    print("|         U R B A N   L I N K         |")
    print(" - - - - - - - - - - - - - - - - - - - ")

    opcao = exibir_menu("MENU PRINCIPAL", MENU_PRINCIPAL)

    while opcao != "0":
        match opcao:
            case "1":
                (pontos, historico, historico_adicionados,
                 historico_atualizados, historico_excluidos) = menu_gerenciar_pontos(
                    pontos, historico, historico_adicionados,
                    historico_atualizados, historico_excluidos)
            case "2":
                historico = consultar_historico(
                    historico, historico_adicionados,
                    historico_atualizados, historico_excluidos)
            case _:
                print("Opção inválida! Tente novamente.")

        opcao = exibir_menu("MENU PRINCIPAL", MENU_PRINCIPAL)

    print("\nSaindo do sistema...")
    time.sleep(2)

if __name__ == "__main__":
    main()
