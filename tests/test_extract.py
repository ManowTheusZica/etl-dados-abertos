from etl.extract import url_da_serie


def test_url_sem_filtro():
    assert url_da_serie(433) == "https://api.bcb.gov.br/dados/serie/bcdata.sgs.433/dados"


def test_url_com_periodo():
    url = url_da_serie(433, "01/01/2024", "01/06/2024")
    assert "dataInicial=01/01/2024" in url
    assert "dataFinal=01/06/2024" in url
