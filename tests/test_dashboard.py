from fastapi.testclient import TestClient

import dashboard.app as dashboard
from etl.load import carregar, conectar


def test_dashboard_responde(tmp_path, monkeypatch):
    banco = str(tmp_path / "teste.db")
    conexao = conectar(banco)
    carregar(conexao, [
        {"serie": "ipca", "mes": "2024-%02d" % m, "valor": 0.4} for m in range(1, 13)
    ] + [
        {"serie": "selic", "mes": "2024-%02d" % m, "valor": 11.0} for m in range(1, 13)
    ] + [
        {"serie": "dolar", "mes": "2024-%02d" % m, "valor": 5.0} for m in range(1, 13)
    ])
    monkeypatch.setattr(dashboard, "BANCO", banco)

    cliente = TestClient(dashboard.app)
    pagina = cliente.get("/")
    assert pagina.status_code == 200
    assert "<svg" in pagina.text

    dados = cliente.get("/api/dados").json()
    assert dados["selic"]["valor"] == 11.0
    assert dados["meses_carregados"]["ipca"] == 12
