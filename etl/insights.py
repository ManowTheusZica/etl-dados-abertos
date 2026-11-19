"""Analises sobre o que foi carregado. Numeros reais, sem enfeite."""
from __future__ import annotations

import math
from statistics import mean
from typing import Iterable

Pares = list[tuple[str, float]]


def correlacao(a: Iterable[float], b: Iterable[float]) -> float | None:
    va, vb = list(a), list(b)
    if len(va) != len(vb) or len(va) < 3:
        return None
    ma, mb = mean(va), mean(vb)
    cov = sum((x - ma) * (y - mb) for x, y in zip(va, vb))
    soma_a = sum((x - ma) ** 2 for x in va)
    soma_b = sum((y - mb) ** 2 for y in vb)
    if soma_a == 0 or soma_b == 0:
        return None
    return round(cov / math.sqrt(soma_a * soma_b), 3)


def alinhar(serie_a: Pares, serie_b: Pares, defasagem: int = 0) -> tuple[list[float], list[float]]:
    """Alinha duas series por mes. defasagem>0 atrasa a serie b."""
    mapa_a = dict(serie_a)
    mapa_b = dict(serie_b)
    if defasagem:
        meses_b = sorted(mapa_b)
        if defasagem >= len(meses_b):
            return [], []
        mapa_b = {meses_b[i]: mapa_b[meses_b[i + defasagem]] for i in range(len(meses_b) - defasagem)}
    meses = sorted(set(mapa_a) & set(mapa_b))
    return [mapa_a[mes] for mes in meses], [mapa_b[mes] for mes in meses]


def melhor_defasagem(serie_a: Pares, serie_b: Pares, maximo: int = 12) -> tuple[int, float] | None:
    melhor: tuple[int, float] | None = None
    for defasagem in range(0, maximo + 1):
        xs, ys = alinhar(serie_a, serie_b, defasagem)
        r = correlacao(xs, ys)
        if r is None:
            continue
        if melhor is None or abs(r) > abs(melhor[1]):
            melhor = (defasagem, r)
    return melhor


def extremos(serie: Pares, maiores: bool = True, quantidade: int = 5) -> list[tuple[str, float]]:
    return sorted(serie, key=lambda item: item[1], reverse=maiores)[:quantidade]


def media_por_ano(serie: Pares) -> list[tuple[str, float]]:
    por_ano: dict[str, list[float]] = {}
    for mes, valor in serie:
        por_ano.setdefault(mes[:4], []).append(valor)
    return sorted((ano, round(mean(valores), 3)) for ano, valores in por_ano.items())
