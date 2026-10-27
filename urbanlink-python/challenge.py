"""UrbanLink - Sprint 4 (Computational Thinking Using Python).

CRUD em Python integrado ao banco Oracle do projeto (o mesmo da API Java e do front-end React),
exportação de dados em JSON e consumo de uma API pública (Open-Meteo).
"""
import json
import os
import time
import uuid

import api_externa
import banco

FATOR_CONVERSAO_BILHETES = 0.05
LIMITE_PONTOS_POR_OPERACAO = 100000
PASTA_EXPORTACAO = "exportacoes"
PAUSA = 1.0   # segundos de "carregando" nas mensagens

MENU_PRINCIPAL = (
    "[1] Gerenciar usuários (CRUD)",
    "[2] Gerenciar pontos",
    "[3] Consultas (ranking, vouchers e impacto ambiental)",
    "[4] Previsão do tempo para sua viagem (API externa)",
    "[5] Exportar dados para JSON",
    "[6] Consultar histórico de tarefas",
    "[0] Sair",
)

SUBMENU_USUARIOS = (
    "[1] Cadastrar usuário (Create)",
    "[2] Listar usuários (Read)",
    "[3] Buscar usuário por ID (Read)",
    "[4] Alterar dados do usuário (Update)",
    "[5] Excluir usuário (Delete)",
    "[0] Voltar ao menu principal",
)

SUBMENU_PONTOS = (
    "[1] Consultar pontos",
    "[2] Adicionar pontos",
    "[3] Atualizar saldo de pontos",
    "[4] Excluir (retirar) pontos",
    "[5] Converter pontos em bilhetes",
    "[0] Voltar ao menu principal",
)

SUBMENU_CONSULTAS = (
    "[1] Ranking de usuários por pontos",
    "[2] Vouchers de um usuário",
    "[3] Todos os vouchers",
    "[4] Resumo de vouchers por status",
    "[5] Impacto ambiental dos usuários",
    "[0] Voltar ao menu principal",
)

SUBMENU_EXPORTAR = (
    "[1] Exportar usuários",
    "[2] Exportar ranking de pontos",
    "[3] Exportar vouchers",
    "[4] Exportar impacto ambiental",
    "[5] Exportar histórico da sessão",
    "[0] Voltar ao menu principal",
)


# ======================================================================
# Funções de apoio (entrada, validação e histórico)
# ======================================================================
def pausar():
    time.sleep(PAUSA)


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


def ler_texto(mensagem, minimo=2, maximo=100):
    while True:
        texto = input(mensagem).strip()
        if minimo <= len(texto) <= maximo:
            return texto
        print(f"Digite um texto de {minimo} a {maximo} caracteres.")


def validar_quantidade(quantidade, minimo=0, maximo=None):
    if quantidade < minimo:
        return False
    if maximo is not None and quantidade > maximo:
        return False
    return True


def validar_email(email):
    email = email.strip().lower()
    arroba = email.find("@")
    valido = (arroba > 0
              and arroba == email.rfind("@")
              and email.find(".", arroba) > arroba + 1
              and not email.endswith(".")
              and " " not in email)
    return valido


def validar_cpf(cpf):
    """Retorna o CPF só com dígitos se for válido (confere os dígitos verificadores); senão, None."""
    digitos = "".join(c for c in cpf if c.isdigit())
    if len(digitos) != 11 or len(set(digitos)) == 1:
        return None
    for tamanho in (9, 10):
        soma = sum(int(digitos[i]) * (tamanho + 1 - i) for i in range(tamanho))
        verificador = (soma * 10) % 11
        if verificador == 10:
            verificador = 0
        if verificador != int(digitos[tamanho]):
            return None
    return digitos


def ler_email():
    while True:
        email = input("E-mail: ").strip().lower()
        if validar_email(email):
            return email
        print("E-mail inválido. Exemplo: nome@email.com")


def ler_cpf():
    while True:
        cpf = validar_cpf(input("CPF (somente números ou com pontuação): "))
        if cpf:
            return cpf
        print("CPF inválido. Confira os números digitados.")


def gerar_id():
    return "USR-" + uuid.uuid4().hex[:8].upper()


def formatar_pontos(valor):
    valor = float(valor)
    return str(int(valor)) if valor == int(valor) else f"{valor:.2f}"


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


def pedir_usuario():
    """Pede o ID e busca no banco. Retorna o usuário (dict) ou None se não existir."""
    id_usuario = input("Digite o ID do usuário (ex.: USR-001): ").strip().upper()
    usuario = banco.buscar_usuario(id_usuario)
    if usuario is None:
        print(f"Usuário '{id_usuario}' não encontrado. Use 'Listar usuários' para ver os IDs.")
    return usuario


def imprimir_usuario(usuario):
    print(f"ID: {usuario['id']} | Nome: {usuario['nome']} | E-mail: {usuario['email']}")
    print(f"CPF: {usuario['cpf']} | Tipo: {usuario['tipo']} | Pontos: {formatar_pontos(usuario['saldo_pontos'])}")


# ======================================================================
# CRUD de usuários
# ======================================================================
def cadastrar_usuario(sessao):
    print("\n--- CADASTRAR USUÁRIO ---")
    usuario = {
        "id": gerar_id(),
        "nome": ler_texto("Nome completo: "),
        "email": ler_email(),
        "cpf": ler_cpf(),
    }
    print("\nSalvando no banco de dados...")
    pausar()
    banco.inserir_usuario(usuario)
    print(f"Usuário cadastrado com sucesso! ID gerado: {usuario['id']}")
    registrar_historico(sessao["historico"], "Cadastro de usuário", usuario["id"])


def listar_usuarios(sessao):
    print("\nConsultando...")
    pausar()
    usuarios = banco.listar_usuarios()
    print("\n--- USUÁRIOS CADASTRADOS ---")
    if not usuarios:
        print("Nenhum usuário cadastrado.")
    for usuario in usuarios:
        print("------------------------------------")
        imprimir_usuario(usuario)
    print(f"\nTotal: {len(usuarios)} usuário(s).")
    registrar_historico(sessao["historico"], "Listagem de usuários", f"{len(usuarios)} usuários")


def buscar_usuario(sessao):
    usuario = pedir_usuario()
    if usuario is None:
        return
    print("------------------------------------")
    imprimir_usuario(usuario)
    print("------------------------------------")
    registrar_historico(sessao["historico"], "Busca de usuário", usuario["id"])


def alterar_usuario(sessao):
    usuario = pedir_usuario()
    if usuario is None:
        return
    print("\nDados atuais:")
    imprimir_usuario(usuario)
    print("\nDigite os novos dados (o CPF e os pontos não são alterados aqui).")
    nome = ler_texto("Novo nome: ")
    email = ler_email()
    print("\nAtualizando os dados...")
    pausar()
    if banco.atualizar_dados_usuario(usuario["id"], nome, email):
        print("Dados atualizados com sucesso!")
        registrar_historico(sessao["historico"], "Alteração de usuário", usuario["id"])
    else:
        print("Nenhum registro foi alterado.")


def excluir_usuario(sessao):
    usuario = pedir_usuario()
    if usuario is None:
        return
    imprimir_usuario(usuario)
    confirmacao = input("\nTem certeza que deseja EXCLUIR este usuário? (s/n): ").strip().lower()
    if confirmacao != "s":
        print("Exclusão cancelada.")
        return
    print("\nExcluindo o usuário...")
    pausar()
    if banco.excluir_usuario(usuario["id"]):
        print("Usuário excluído com sucesso!")
        registrar_historico(sessao["historico"], "Exclusão de usuário", usuario["id"])
    else:
        print("Nenhum registro foi excluído.")


# ======================================================================
# Pontos (mesmas operações da Sprint 3, agora gravadas no banco)
# ======================================================================
def consultar_pontos(sessao):
    usuario = pedir_usuario()
    if usuario is None:
        return
    print("\nConsultando...")
    pausar()
    print("------------------------------------")
    print(f"Usuário: {usuario['nome']}")
    print(f"Pontos acumulados: {formatar_pontos(usuario['saldo_pontos'])}")
    print("------------------------------------")
    registrar_historico(sessao["historico"], "Consulta de pontos", usuario["id"])


def adicionar_pontos(sessao):
    usuario = pedir_usuario()
    if usuario is None:
        return
    print("----------------------------------------------------")
    qtd_pontos = ler_inteiro("Digite a quantidade de pontos que deseja adicionar:\n")
    while not validar_quantidade(qtd_pontos, minimo=1, maximo=LIMITE_PONTOS_POR_OPERACAO):
        print(f"Digite um valor inteiro entre 1 e {LIMITE_PONTOS_POR_OPERACAO}.")
        qtd_pontos = ler_inteiro("Digite a quantidade de pontos que deseja adicionar:\n")
    print("\nAdicionando os pontos...")
    pausar()
    if banco.adicionar_pontos(usuario["id"], qtd_pontos):
        sessao["adicionados"].append(qtd_pontos)
        print("Pontos adicionados com sucesso!")
        registrar_historico(sessao["historico"], "Adição de pontos", f"{usuario['id']}: +{qtd_pontos} pontos")
    print("----------------------------------------------------")


def atualizar_pontos(sessao):
    usuario = pedir_usuario()
    if usuario is None:
        return
    print("----------------------------------------------")
    print(f"Saldo atual de pontos: {formatar_pontos(usuario['saldo_pontos'])}")
    qtd_pontos = ler_inteiro("Digite a nova quantidade do saldo de pontos:\n")
    while not validar_quantidade(qtd_pontos, minimo=0, maximo=LIMITE_PONTOS_POR_OPERACAO):
        print(f"Digite um valor inteiro entre 0 e {LIMITE_PONTOS_POR_OPERACAO}.")
        qtd_pontos = ler_inteiro("Digite a nova quantidade do saldo de pontos:\n")
    print("\nAtualizando os pontos...")
    pausar()
    if banco.definir_saldo(usuario["id"], qtd_pontos):
        sessao["atualizados"].append(qtd_pontos)
        print("Pontos atualizados com sucesso!")
        registrar_historico(sessao["historico"], "Atualização de pontos", f"{usuario['id']}: novo saldo {qtd_pontos}")
    print("----------------------------------------------")


def excluir_pontos(sessao):
    usuario = pedir_usuario()
    if usuario is None:
        return
    saldo = float(usuario["saldo_pontos"])
    if saldo <= 0:
        print("Este usuário não possui pontos para excluir.")
        return
    print("---------------------------------------------------")
    print(f"Saldo atual de pontos: {formatar_pontos(saldo)}")
    qtd_pontos = ler_inteiro("Digite a quantidade de pontos que deseja excluir:\n")
    while not validar_quantidade(qtd_pontos, minimo=1, maximo=saldo):
        print("Valor inválido! Não pode ser menor que 1 nem maior que o saldo.")
        qtd_pontos = ler_inteiro("Digite a quantidade de pontos que deseja excluir:\n")
    print("\nExcluindo os pontos...")
    pausar()
    if banco.retirar_pontos(usuario["id"], qtd_pontos):
        sessao["excluidos"].append(qtd_pontos)
        print("Pontos excluídos com sucesso!")
        registrar_historico(sessao["historico"], "Exclusão de pontos", f"{usuario['id']}: -{qtd_pontos} pontos")
    else:
        print("Não foi possível excluir: o saldo mudou e ficou insuficiente.")
    print("---------------------------------------------------")


def converter_bilhetes(sessao):
    usuario = pedir_usuario()
    if usuario is None:
        return
    print("------------------------------------")
    print("\nFazendo o cálculo da conversão...")
    pausar()
    pontos = float(usuario["saldo_pontos"])
    bilhetes = int(pontos * FATOR_CONVERSAO_BILHETES)
    print(f"Pontos acumulados: {formatar_pontos(pontos)}")
    print(f"A sua quantidade de pontos acumulados equivale a: {bilhetes} bilhetes.")
    print("------------------------------------")
    registrar_historico(sessao["historico"], "Conversão em bilhetes", f"{usuario['id']}: {bilhetes} bilhetes")


# ======================================================================
# Consultas
# ======================================================================
def mostrar_ranking(sessao):
    ranking = banco.ranking_pontos(5)
    print("\n--- RANKING DE PONTOS (TOP 5) ---")
    for posicao, usuario in enumerate(ranking, start=1):
        print(f"{posicao}º {usuario['nome']} ({usuario['id']}) - {formatar_pontos(usuario['saldo_pontos'])} pontos")
    registrar_historico(sessao["historico"], "Consulta de ranking")


def mostrar_vouchers(sessao, id_usuario=None):
    vouchers = banco.listar_vouchers(id_usuario)
    print("\n--- VOUCHERS ---")
    if not vouchers:
        print("Nenhum voucher encontrado.")
    for v in vouchers:
        print(f"{v['codigo']} | usuário {v['usuario_id']} | transporte {v['transporte_id']} | "
              f"R$ {float(v['valor_credito']):.2f} | {formatar_pontos(v['pontos_usados'])} pontos | {v['status']}")
    print(f"\nTotal: {len(vouchers)} voucher(s).")
    registrar_historico(sessao["historico"], "Consulta de vouchers", f"{len(vouchers)} encontrados")


def mostrar_vouchers_do_usuario(sessao):
    usuario = pedir_usuario()
    if usuario is not None:
        mostrar_vouchers(sessao, usuario["id"])


def mostrar_resumo_vouchers(sessao):
    resumo = banco.resumo_vouchers_por_status()
    print("\n--- VOUCHERS POR STATUS ---")
    for linha in resumo:
        print(f"{linha['status']}: {linha['quantidade']} voucher(s), {formatar_pontos(linha['total_pontos'])} pontos")
    registrar_historico(sessao["historico"], "Resumo de vouchers por status")


def mostrar_impactos(sessao):
    impactos = banco.listar_impactos()
    print("\n--- IMPACTO AMBIENTAL ---")
    if not impactos:
        print("Nenhum impacto registrado ainda.")
    for i in impactos:
        print(f"{i['nome']} ({i['usuario_id']}): {float(i['total_co2']):.3f} kg de CO2 evitados em "
              f"{i['total_viagens']} viagem(ns) = {float(i['equiv_arvores']):.2f} árvores/ano")
    registrar_historico(sessao["historico"], "Consulta de impacto ambiental")


# ======================================================================
# API externa
# ======================================================================
def consultar_clima(sessao):
    nome = ler_texto("Digite a cidade da sua viagem: ", minimo=2, maximo=60)
    print("\nBuscando a cidade...")
    cidade = api_externa.buscar_cidade(nome)
    if cidade is None:
        print(f"Cidade '{nome}' não encontrada.")
        return
    print("Buscando a previsão do tempo...")
    previsao = api_externa.buscar_previsao(cidade["latitude"], cidade["longitude"])
    print("\n------------------------------------")
    print(f"Cidade: {cidade['nome']} - {cidade['estado']} ({cidade['pais']})")
    print(f"Agora: {previsao['temperatura_atual']}°C - {api_externa.descrever_clima(previsao['codigo_clima'])}")
    print(f"Hoje: mínima {previsao['minima']}°C | máxima {previsao['maxima']}°C")
    print(f"Chance de chuva: {previsao['chance_chuva']}%")
    print("------------------------------------")
    print(f"Sugestão UrbanLink: {api_externa.sugerir_deslocamento(previsao)}")
    registrar_historico(sessao["historico"], "Previsão do tempo (API)", cidade["nome"])


# ======================================================================
# Exportação para JSON
# ======================================================================
def exportar_json(nome_base, dados):
    """Grava os dados em exportacoes/<nome>_<data-hora>.json e devolve o caminho do arquivo."""
    os.makedirs(PASTA_EXPORTACAO, exist_ok=True)
    carimbo = time.strftime("%Y%m%d_%H%M%S")
    caminho = os.path.join(PASTA_EXPORTACAO, f"{nome_base}_{carimbo}.json")
    conteudo = {
        "exportado_em": time.strftime("%d/%m/%Y %H:%M:%S"),
        "total": len(dados),
        "dados": dados,
    }
    with open(caminho, "w", encoding="utf-8") as arquivo:
        json.dump(conteudo, arquivo, ensure_ascii=False, indent=4, default=str)
    return caminho


def exportar(sessao, nome_base, dados):
    try:
        caminho = exportar_json(nome_base, dados)
    except OSError as erro:
        print(f"Não foi possível gravar o arquivo: {erro}")
        return
    print(f"{len(dados)} registro(s) exportado(s) para: {caminho}")
    registrar_historico(sessao["historico"], "Exportação para JSON", caminho)


# ======================================================================
# Histórico de tarefas (da Sprint 3)
# ======================================================================
def consultar_historico(sessao):
    historico = sessao["historico"]
    print("\nBuscando o histórico...")
    pausar()
    print("\n- - - HISTÓRICO DE TAREFAS (DA MAIS ANTIGA ATÉ A MAIS RECENTE): - - -\n")

    for item in historico:
        detalhe = f" ({item['detalhe']})" if item["detalhe"] else ""
        print(f"-> [{item['data_hora']}] {item['tipo']}{detalhe}")

    print(f"\nTotal de atividades realizadas:\n{len(historico)}")
    registrar_historico(historico, "Consulta do Histórico de Tarefas")

    print("\n- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n")

    grupos = (
        ("NA ADIÇÃO DE PONTOS", sessao["adicionados"], "adicionados"),
        ("NA ATUALIZAÇÃO DE PONTOS", sessao["atualizados"], "inseridos"),
        ("NA EXCLUSÃO DE PONTOS", sessao["excluidos"], "excluídos"),
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


# ======================================================================
# Menus e submenus
# ======================================================================
def executar(acao, *argumentos):
    """Roda uma ação tratando os erros previstos, para o programa nunca fechar por causa deles."""
    try:
        acao(*argumentos)
    except banco.ErroBanco as erro:
        print(f"\n[!] {erro}")
    except api_externa.ErroApi as erro:
        print(f"\n[!] Não foi possível consultar a API externa: {erro}")
    except KeyboardInterrupt:
        print("\nOperação cancelada.")


def menu_usuarios(sessao):
    opcao = exibir_menu("SUBMENU | USUÁRIOS (CRUD)", SUBMENU_USUARIOS)
    while opcao != "0":
        match opcao:
            case "1":
                executar(cadastrar_usuario, sessao)
            case "2":
                executar(listar_usuarios, sessao)
            case "3":
                executar(buscar_usuario, sessao)
            case "4":
                executar(alterar_usuario, sessao)
            case "5":
                executar(excluir_usuario, sessao)
            case _:
                print("Opção inválida! Tente novamente.")
        opcao = exibir_menu("SUBMENU | USUÁRIOS (CRUD)", SUBMENU_USUARIOS)


def menu_pontos(sessao):
    opcao = exibir_menu("SUBMENU | GERENCIAR PONTOS", SUBMENU_PONTOS)
    while opcao != "0":
        match opcao:
            case "1":
                executar(consultar_pontos, sessao)
            case "2":
                executar(adicionar_pontos, sessao)
            case "3":
                executar(atualizar_pontos, sessao)
            case "4":
                executar(excluir_pontos, sessao)
            case "5":
                executar(converter_bilhetes, sessao)
            case _:
                print("Opção inválida! Tente novamente.")
        opcao = exibir_menu("SUBMENU | GERENCIAR PONTOS", SUBMENU_PONTOS)


def menu_consultas(sessao):
    opcao = exibir_menu("SUBMENU | CONSULTAS", SUBMENU_CONSULTAS)
    while opcao != "0":
        match opcao:
            case "1":
                executar(mostrar_ranking, sessao)
            case "2":
                executar(mostrar_vouchers_do_usuario, sessao)
            case "3":
                executar(mostrar_vouchers, sessao)
            case "4":
                executar(mostrar_resumo_vouchers, sessao)
            case "5":
                executar(mostrar_impactos, sessao)
            case _:
                print("Opção inválida! Tente novamente.")
        opcao = exibir_menu("SUBMENU | CONSULTAS", SUBMENU_CONSULTAS)


def menu_exportar(sessao):
    opcao = exibir_menu("SUBMENU | EXPORTAR PARA JSON", SUBMENU_EXPORTAR)
    while opcao != "0":
        match opcao:
            case "1":
                executar(lambda: exportar(sessao, "usuarios", banco.listar_usuarios()))
            case "2":
                executar(lambda: exportar(sessao, "ranking_pontos", banco.ranking_pontos(10)))
            case "3":
                executar(lambda: exportar(sessao, "vouchers", banco.listar_vouchers()))
            case "4":
                executar(lambda: exportar(sessao, "impacto_ambiental", banco.listar_impactos()))
            case "5":
                executar(lambda: exportar(sessao, "historico_sessao", sessao["historico"]))
            case _:
                print("Opção inválida! Tente novamente.")
        opcao = exibir_menu("SUBMENU | EXPORTAR PARA JSON", SUBMENU_EXPORTAR)


def main():
    sessao = {
        "historico": [],
        "adicionados": [],
        "atualizados": [],
        "excluidos": [],
    }

    print(" - - - - - - - - - - - - - - - - - - - ")
    print("|         U R B A N   L I N K         |")
    print(" - - - - - - - - - - - - - - - - - - - ")

    opcao = exibir_menu("MENU PRINCIPAL", MENU_PRINCIPAL)

    while opcao != "0":
        match opcao:
            case "1":
                menu_usuarios(sessao)
            case "2":
                menu_pontos(sessao)
            case "3":
                menu_consultas(sessao)
            case "4":
                executar(consultar_clima, sessao)
            case "5":
                menu_exportar(sessao)
            case "6":
                consultar_historico(sessao)
            case _:
                print("Opção inválida! Tente novamente.")

        opcao = exibir_menu("MENU PRINCIPAL", MENU_PRINCIPAL)

    print("\nSaindo do sistema...")
    pausar()


if __name__ == "__main__":
    main()
