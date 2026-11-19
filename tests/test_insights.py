import pytest

from etl.acumulado import acumulado_12m
from etl.insights import alinhar, correlacao, extremos, media_por_ano, melhor_defasagem


def test_correlacao_perfeita():
    assert correlacao([1, 2, 3, 4], [2, 4, 6, 8]) == 1.0
    assert correlacao([1, 2, 3, 4], [8, 6, 4, 2]) == -1.0


def test_correlacao_sem_variancia():
    assert correlacao([1, 1, 1], [2, 3, 4]) is None
    assert correlacao([1, 2], [1, 2]) is None  # amostra pequena


def test_alinhar_com_defasagem():
    a = [("2024-01", 1.0), ("2024-02", 2.0), ("2024-03", 3.0)]
    b = [("2024-01", 10.0), ("2024-02", 20.0), ("2024-03", 30.0)]
    xs, ys = alinhar(a, b, 1)
    assert xs == [1.0, 2.0]
    assert ys == [20.0, 30.0]


def test_melhor_defasagem_escolhe_o_mais_forte():
    selic = [("2023-%02d" % m, float(m)) for m in range(1, 13)]
    ipca = [("2023-%02d" % m, float(13 - m)) for m in range(1, 13)]
    achado = melhor_defasagem(selic, ipca, maximo=3)
    assert achado is not None
    defasagem, r = achado
    assert abs(r) > 0.9


def test_acumulado_12m():
    serie = [("2024-%02d" % m, 1.0) for m in range(1, 13)]
    resultado = acumulado_12m(serie)
    assert len(resultado) == 1
    assert resultado[0][0] == "2024-12"
    assert resultado[0][1] == pytest.approx((1.01 ** 12 - 1) * 100, rel=1e-3)


def test_extremos_e_media_por_ano():
    serie = [("2024-01", 0.5), ("2024-02", -0.2), ("2025-01", 1.2)]
    assert extremos(serie, True, 1)[0] == ("2025-01", 1.2)
    assert extremos(serie, False, 1)[0] == ("2024-02", -0.2)
    assert media_por_ano(serie)[0] == ("2024", 0.15)
