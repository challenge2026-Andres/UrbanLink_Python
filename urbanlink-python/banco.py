"""Acesso ao banco Oracle do UrbanLink (o MESMO banco usado pela API Java).

Tudo o que for inserido, alterado ou excluído aqui aparece no sistema web (front-end React)
e vice-versa, porque os dois usam as mesmas tabelas: usuario, transporte, voucher e impacto_ambiental.

Credenciais ficam em variáveis de ambiente (nunca no código):
    DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_SID
"""
import os
from contextlib import contextmanager

import oracledb


class ErroBanco(Exception):
    """Erro de banco já traduzido para uma mensagem que o usuário entende."""


def _traduzir_erro(erro):
    """Converte erros do Oracle (ORA-xxxxx) em mensagens amigáveis."""
    detalhe = erro.args[0] if erro.args else None
    codigo = getattr(detalhe, "code", None)
    if codigo == 1:
        return "Já existe um registro com este id, e-mail ou CPF."
    if codigo == 2291:
        return "Referência inválida: o registro relacionado não existe."
    if codigo == 2292:
        return "O registro possui vouchers ou impactos vinculados e não pode ser excluído."
    if codigo in (12899, 1438):
        return "Algum valor informado excede o tamanho permitido."
    return f"Erro no banco de dados: {erro}"


@contextmanager
def conectar():
    """Abre a conexão, confirma (commit) se tudo deu certo, desfaz (rollback) se falhar e sempre fecha."""
    try:
        conexao = oracledb.connect(
            user=os.getenv("DB_USER", "RM569432"),
            password=os.getenv("DB_PASSWORD", "170408"),
            dsn=oracledb.makedsn(
                os.getenv("DB_HOST", "oracle.fiap.com.br"),
                int(os.getenv("DB_PORT", "1521")),
                sid=os.getenv("DB_SID", "ORCL"),
            ),
        )
    except oracledb.Error as erro:
        raise ErroBanco(f"Não foi possível conectar ao banco de dados: {erro}") from erro

    try:
        yield conexao
        conexao.commit()
    except oracledb.Error as erro:
        conexao.rollback()
        raise ErroBanco(_traduzir_erro(erro)) from erro
    finally:
        conexao.close()


def _linhas_para_dicts(cursor):
    """Transforma as linhas do SELECT em uma lista de dicionários {coluna: valor}."""
    colunas = [coluna[0].lower() for coluna in cursor.description]
    return [dict(zip(colunas, linha)) for linha in cursor.fetchall()]


# ---------------------------------------------------------------- CREATE
def inserir_usuario(usuario):
    sql = ("INSERT INTO usuario (id, nome, email, cpf, saldo_pontos, tipo) "
           "VALUES (:id, :nome, :email, :cpf, 0, 'COMUM')")
    with conectar() as conexao:
        conexao.cursor().execute(sql, usuario)


# ---------------------------------------------------------------- READ
def listar_usuarios():
    with conectar() as conexao:
        cursor = conexao.cursor()
        cursor.execute("SELECT id, nome, email, cpf, saldo_pontos, tipo FROM usuario ORDER BY nome")
        return _linhas_para_dicts(cursor)


def buscar_usuario(id_usuario):
    with conectar() as conexao:
        cursor = conexao.cursor()
        cursor.execute("SELECT id, nome, email, cpf, saldo_pontos, tipo FROM usuario WHERE id = :id",
                       {"id": id_usuario})
        linhas = _linhas_para_dicts(cursor)
    return linhas[0] if linhas else None


def ranking_pontos(limite=5):
    sql = ("SELECT id, nome, saldo_pontos FROM usuario "
           "ORDER BY saldo_pontos DESC FETCH FIRST :limite ROWS ONLY")
    with conectar() as conexao:
        cursor = conexao.cursor()
        cursor.execute(sql, {"limite": limite})
        return _linhas_para_dicts(cursor)


def listar_vouchers(id_usuario=None):
    colunas = "codigo, usuario_id, transporte_id, valor_credito, pontos_usados, status, data_geracao"
    with conectar() as conexao:
        cursor = conexao.cursor()
        if id_usuario is None:
            cursor.execute(f"SELECT {colunas} FROM voucher ORDER BY data_geracao DESC")
        else:
            cursor.execute(f"SELECT {colunas} FROM voucher WHERE usuario_id = :id ORDER BY data_geracao DESC",
                           {"id": id_usuario})
        return _linhas_para_dicts(cursor)


def listar_impactos():
    sql = ("SELECT i.usuario_id, u.nome, i.total_co2, i.total_viagens, i.equiv_arvores, i.pontos_investidos "
           "FROM impacto_ambiental i JOIN usuario u ON u.id = i.usuario_id ORDER BY i.total_co2 DESC")
    with conectar() as conexao:
        cursor = conexao.cursor()
        cursor.execute(sql)
        return _linhas_para_dicts(cursor)


def resumo_vouchers_por_status():
    """Quantidade de vouchers e total de pontos por status (consulta com GROUP BY)."""
    sql = ("SELECT status, COUNT(*) AS quantidade, SUM(pontos_usados) AS total_pontos "
           "FROM voucher GROUP BY status ORDER BY quantidade DESC")
    with conectar() as conexao:
        cursor = conexao.cursor()
        cursor.execute(sql)
        return _linhas_para_dicts(cursor)


# ---------------------------------------------------------------- UPDATE
def atualizar_dados_usuario(id_usuario, nome, email):
    with conectar() as conexao:
        cursor = conexao.cursor()
        cursor.execute("UPDATE usuario SET nome = :nome, email = :email WHERE id = :id",
                       {"nome": nome, "email": email, "id": id_usuario})
        return cursor.rowcount > 0


def adicionar_pontos(id_usuario, quantidade):
    with conectar() as conexao:
        cursor = conexao.cursor()
        cursor.execute("UPDATE usuario SET saldo_pontos = saldo_pontos + :qtd WHERE id = :id",
                       {"qtd": quantidade, "id": id_usuario})
        return cursor.rowcount > 0


def definir_saldo(id_usuario, novo_saldo):
    with conectar() as conexao:
        cursor = conexao.cursor()
        cursor.execute("UPDATE usuario SET saldo_pontos = :saldo WHERE id = :id",
                       {"saldo": novo_saldo, "id": id_usuario})
        return cursor.rowcount > 0


def retirar_pontos(id_usuario, quantidade):
    """Só retira se o saldo for suficiente (a condição vai no próprio UPDATE, então é atômico)."""
    with conectar() as conexao:
        cursor = conexao.cursor()
        cursor.execute("UPDATE usuario SET saldo_pontos = saldo_pontos - :qtd "
                       "WHERE id = :id AND saldo_pontos >= :qtd",
                       {"qtd": quantidade, "id": id_usuario})
        return cursor.rowcount > 0


# ---------------------------------------------------------------- DELETE
def excluir_usuario(id_usuario):
    with conectar() as conexao:
        cursor = conexao.cursor()
        cursor.execute("DELETE FROM usuario WHERE id = :id", {"id": id_usuario})
        return cursor.rowcount > 0


def proximo_id_usuario():
    with conectar() as conexao:
        cursor = conexao.cursor()
        cursor.execute("SELECT seq_usuario.NEXTVAL FROM dual")
        numero = cursor.fetchone()[0]
    return f"USR-{numero:03d}"
