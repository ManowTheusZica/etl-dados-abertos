"""Dashboard que le do banco carregado pelo ETL. Graficos em SVG, sem CDN."""
from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from etl.acumulado import acumulado_12m
from etl.config import BANCO_PADRAO
from etl.insights import correlacao, extremos, melhor_defasagem
from etl.load import conectar, ler_serie

app = FastAPI(title="Indicadores - Dashboard")
BANCO = os.getenv("BANCO", BANCO_PADRAO)


def _svg_linhas(series: dict[str, list[tuple[str, float]]], largura=880, altura=280, padding=40) -> str:
    todas = [valor for pontos in series.values() for _, valor in pontos]
    if not todas:
        return "<p>sem dados</p>"
    minimo, maximo = min(todas), max(todas)
    faixa = (maximo - minimo) or 1
    meses = sorted({mes for pontos in series.values() for mes, _ in pontos})

    def x(i):
        return padding + (largura - 2 * padding) * i / max(len(meses) - 1, 1)

    def y(valor):
        return altura - padding - (altura - 2 * padding) * (valor - minimo) / faixa

    cores = ["#2563eb", "#dc2626", "#16a34a"]
    partes = ['<svg viewBox="0 0 %d %d" class="grafico">' % (largura, altura)]
    partes.append('<rect x="0" y="0" width="%d" height="%d" fill="#fff"/>' % (largura, altura))
    for indice, (nome, pontos) in enumerate(series.items()):
        mapa = dict(pontos)
        caminho = " ".join(
            "%s%.1f,%.1f" % ("M" if i == 0 else "L", x(i), y(mapa[mes]))
            for i, mes in enumerate(meses)
            if mes in mapa
        )
        partes.append(
            '<path d="%s" fill="none" stroke="%s" stroke-width="2.5"/>' % (caminho, cores[indice % 3])
        )
    for indice, nome in enumerate(series):
        partes.append(
            '<text x="%d" y="%d" font-size="13" fill="%s">&#9632; %s</text>'
            % (padding + indice * 190, 20, cores[indice % 3], nome)
        )
    partes.append(
        '<text x="%d" y="%d" font-size="11" fill="#64748b">%s</text>'
        % (padding, altura - 8, meses[0])
    )
    partes.append(
        '<text x="%d" y="%d" font-size="11" fill="#64748b" text-anchor="end">%s</text>'
        % (largura - padding, altura - 8, meses[-1])
    )
    partes.append("</svg>")
    return "".join(partes)


@app.get("/api/dados")
def dados():
    conexao = conectar(BANCO)
    ipca = ler_serie(conexao, "ipca")
    selic = ler_serie(conexao, "selic")
    dolar = ler_serie(conexao, "dolar")
    ac12 = acumulado_12m(ipca)
    return {
        "ipca_12m": {"ultimo_mes": ac12[-1][0] if ac12 else None, "valor": ac12[-1][1] if ac12 else None},
        "selic": {"ultimo_mes": selic[-1][0] if selic else None, "valor": selic[-1][1] if selic else None},
        "dolar": {"ultimo_mes": dolar[-1][0] if dolar else None, "valor": dolar[-1][1] if dolar else None},
        "correlacao_selic_ipca": melhor_defasagem(selic, ac12),
        "maiores_ipca": extremos(ipca, True, 5),
        "meses_carregados": {"ipca": len(ipca), "selic": len(selic), "dolar": len(dolar)},
    }


@app.get("/", response_class=HTMLResponse)
def pagina():
    conexao = conectar(BANCO)
    ipca = ler_serie(conexao, "ipca")
    selic = ler_serie(conexao, "selic")
    dolar = ler_serie(conexao, "dolar")
    ac12 = acumulado_12m(ipca)

    ultimos = ac12[-24:]
    selic_ultimos = [(mes, valor) for mes, valor in selic if mes >= ultimos[0][0]] if ultimos else []
    grafico = _svg_linhas({"IPCA 12m (%)": ultimos, "Selic (% a.a.)": selic_ultimos})

    melhor = melhor_defasagem(selic, ac12)

    if melhor:
        texto_achado = (
            "Correlacao entre Selic e IPCA 12 meses: <strong>%.3f</strong> com defasagem de "
            "<strong>%d meses</strong>. Juros altos hoje aparecem no IPCA varios meses depois."
            % (melhor[1], melhor[0])
        )
    else:
        texto_achado = "Serie curta ou sem variacao suficiente para calcular a correlacao."
    linhas = "".join(
        "<tr><td>%s</td><td>%+.2f%%</td><td>%.2f%%</td></tr>" % (mes, valor, dict(selic).get(mes, float("nan")))
        for mes, valor in ac12[-12:][::-1]
    )
    dolar_medio = round(sum(v for _, v in dolar[-12:]) / 12, 2) if dolar else None

    return f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<title>Indicadores - IPCA, Selic e Dolar</title>
<style>
 body{{font-family:system-ui,sans-serif;background:#f1f5f9;color:#0f172a;margin:0;padding:32px}}
 .wrap{{max-width:960px;margin:0 auto}}
 h1{{font-size:22px;margin:0 0 4px}}
 .sub{{color:#64748b;font-size:14px;margin-bottom:24px}}
 .cards{{display:flex;gap:16px;flex-wrap:wrap;margin-bottom:24px}}
 .card{{background:#fff;border-radius:14px;padding:16px 20px;flex:1;min-width:180px;
        box-shadow:0 1px 3px rgba(15,23,42,.08)}}
 .card span{{display:block;color:#64748b;font-size:12px;text-transform:uppercase;letter-spacing:.04em}}
 .card strong{{font-size:26px}}
 .box{{background:#fff;border-radius:14px;padding:16px;box-shadow:0 1px 3px rgba(15,23,42,.08);margin-bottom:24px}}
 .grafico{{width:100%;height:auto}}
 table{{width:100%;border-collapse:collapse;font-size:14px}}
 th,td{{text-align:left;padding:8px 10px;border-bottom:1px solid #e2e8f0}}
 th{{color:#64748b;font-weight:600;font-size:12px;text-transform:uppercase}}
 .destaque{{color:#b91c1c}}
 footer{{color:#94a3b8;font-size:12px;margin-top:24px}}
</style></head><body><div class="wrap">
<h1>IPCA, Selic e Dolar</h1>
<div class="sub">Serie historica do Banco Central, tratada por ETL proprio. Atualiza com
<code>python -m etl.cli run</code>.</div>

<div class="cards">
  <div class="card"><span>IPCA 12 meses</span><strong>{ac12[-1][1]:+.2f}%</strong>
    <small>{ac12[-1][0]}</small></div>
  <div class="card"><span>Selic</span><strong>{selic[-1][1]:.2f}%</strong>
    <small>{selic[-1][0]}</small></div>
  <div class="card"><span>Dolar (media 12m)</span><strong>R$ {dolar_medio}</strong>
    <small>ultimo: R$ {dolar[-1][1]:.2f}</small></div>
</div>

<div class="box">{grafico}</div>

<div class="box">
  <h2 style="font-size:16px;margin:0 0 12px">Ultimos 12 meses</h2>
  <table><thead><tr><th>Mes</th><th>IPCA 12m</th><th>Selic</th></tr></thead>
  <tbody>{linhas}</tbody></table>
</div>

<div class="box">
  <h2 style="font-size:16px;margin:0 0 8px">Achado</h2>
  <p style="margin:0">{texto_achado}</p>
</div>

<footer>Fonte: API SGS do Banco Central do Brasil. {len(ipca)} meses carregados.</footer>
</div></body></html>"""
