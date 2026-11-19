"""Indicadores derivados: IPCA acumulado em 12 meses."""
from __future__ import annotations

Pares = list[tuple[str, float]]


def acumulado_12m(serie: Pares, janela: int = 12) -> Pares:
    """Compoe a variacao mensal em 12 meses. Devolve [(mes, %)]."""
    saida: Pares = []
    for i in range(len(serie) - janela + 1):
        produto = 1.0
        for _, valor in serie[i : i + janela]:
            produto *= 1 + valor / 100
        saida.append((serie[i + janela - 1][0], round((produto - 1) * 100, 3)))
    return saida
