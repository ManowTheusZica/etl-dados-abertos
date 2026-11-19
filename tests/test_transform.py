import pytest

from etl.transform import agregar_mensal, normalizar, para_data, para_numero


def test_data_brasileira():
    assert para_data("05/03/2022").isoformat() == "2022-03-05"
    with pytest.raises(ValueError):
        para_data("2022-03-05")
    with pytest.raises(ValueError):
        para_data("")


def test_numero_aceita_os_dois_formatos():
    assert para_numero("0.53") == pytest.approx(0.53)      # padrao Bacen
    assert para_numero("1.234,56") == pytest.approx(1234.56)  # padrao brasileiro
    assert para_numero("-0.32") == pytest.approx(-0.32)


def test_normalizar_joga_fora_o_que_nao_parseia():
    registros = [
        {"serie": "ipca", "data": "01/02/2024", "valor": "0.83"},
        {"serie": "ipca", "data": "01/02/2024", "valor": "0.83"},  # duplicata
        {"serie": "ipca", "data": "data ruim", "valor": "1.0"},
        {"serie": "ipca", "data": "01/03/2024", "valor": "abc"},
    ]
    limpos = normalizar(registros)
    assert len(limpos) == 1
    assert limpos[0]["mes"] == "2024-02"
    assert limpos[0]["valor"] == pytest.approx(0.83)


def test_agregar_mensal_faz_media_do_diario():
    registros = [
        {"serie": "dolar", "mes": "2024-01", "valor": 5.0},
        {"serie": "dolar", "mes": "2024-01", "valor": 6.0},
        {"serie": "ipca", "mes": "2024-01", "valor": 0.4},
    ]
    mensal = {(item["serie"], item["mes"]): item for item in agregar_mensal(registros)}
    assert mensal[("dolar", "2024-01")]["valor"] == pytest.approx(5.5)
    assert mensal[("dolar", "2024-01")]["obs"] == 2
    assert mensal[("ipca", "2024-01")]["valor"] == pytest.approx(0.4)
