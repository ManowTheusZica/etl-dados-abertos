from etl.load import carregar, conectar, finalizar_execucao, iniciar_execucao, ler_serie


def test_carga_idempotente(tmp_path):
    banco = str(tmp_path / "teste.db")
    conexao = conectar(banco)
    registros = [
        {"serie": "ipca", "mes": "2024-01", "valor": 0.42},
        {"serie": "ipca", "mes": "2024-02", "valor": 0.83},
    ]
    assert carregar(conexao, registros) == 2
    assert carregar(conexao, registros) == 2  # de novo, mas sem duplicar
    assert ler_serie(conexao, "ipca") == [("2024-01", 0.42), ("2024-02", 0.83)]


def test_atualiza_valor_quando_a_fonte_corrige(tmp_path):
    conexao = conectar(str(tmp_path / "teste.db"))
    carregar(conexao, [{"serie": "ipca", "mes": "2024-01", "valor": 0.40}])
    carregar(conexao, [{"serie": "ipca", "mes": "2024-01", "valor": 0.42}])
    assert ler_serie(conexao, "ipca") == [("2024-01", 0.42)]


def test_registra_execucao(tmp_path):
    conexao = conectar(str(tmp_path / "teste.db"))
    execucao = iniciar_execucao(conexao)
    finalizar_execucao(conexao, execucao, 10, "ok")
    situacao, registros = conexao.execute(
        "SELECT situacao, registros FROM execucoes WHERE id = ?", (execucao,)
    ).fetchone()
    assert situacao == "ok"
    assert registros == 10
