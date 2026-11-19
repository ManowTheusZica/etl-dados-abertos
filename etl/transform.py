"""Tratamento: data brasileira, numero com virgula, agregacao mensal, dedupe."""
from __future__ import annotations

import re
from datetime import date
from statistics import mean

DATA_RE = re.compile(r"^(\d{2})/(\d{2})/(\d{4})$")


def para_data(texto: str) -> date:
    achado = DATA_RE.match((texto or "").strip())
    if not achado:
        raise ValueError("data invalida: %r" % texto)
    dia, mes, ano = (int(parte) for parte in achado.groups())
    return date(ano, mes, dia)


def para_numero(texto: str) -> float:
    """Aceita 0.53 (padrao do Bacen) e 1.234,56 (padrao brasileiro)."""
    bruto = str(texto).strip()
    try:
        if "," in bruto:
            bruto = bruto.replace(".", "").replace(",", ".")
        return float(bruto)
    except (TypeError, ValueError) as exc:
        raise ValueError("numero invalido: %r" % texto) from exc


def normalizar(registros: list[dict]) -> list[dict]:
    """Devolve [{serie, data(iso), valor, mes(AAAA-MM)}], sem duplicata."""
    vistos: set[tuple[str, str]] = set()
    saida: list[dict] = []
    for registro in registros:
        try:
            dia = para_data(registro["data"])
            valor = para_numero(registro["valor"])
        except (KeyError, ValueError):
            continue
        chave = (registro["serie"], dia.isoformat())
        if chave in vistos:
            continue
        vistos.add(chave)
        saida.append(
            {
                "serie": registro["serie"],
                "data": dia.isoformat(),
                "mes": "%04d-%02d" % (dia.year, dia.month),
                "valor": valor,
            }
        )
    return sorted(saida, key=lambda item: (item["serie"], item["data"]))


def agregar_mensal(registros: list[dict]) -> list[dict]:
    """Series diarias (dolar) viram media mensal; series mensais passam direto."""
    por_serie_mes: dict[tuple[str, str], list[float]] = {}
    for registro in registros:
        por_serie_mes.setdefault((registro["serie"], registro["mes"]), []).append(registro["valor"])

    saida = [
        {"serie": serie, "mes": mes, "valor": round(mean(valores), 4), "obs": len(valores)}
        for (serie, mes), valores in por_serie_mes.items()
    ]
    return sorted(saida, key=lambda item: (item["serie"], item["mes"]))
