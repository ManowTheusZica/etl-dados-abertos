"""Coleta no SGS do Banco Central. urllib puro, com retry."""
from __future__ import annotations

import json
import logging
import time
import urllib.error
import urllib.request

from .config import BASE_URL, SERIES

log = logging.getLogger(__name__)


class ColetaError(Exception):
    pass


def url_da_serie(codigo: int, inicio: str | None = None, fim: str | None = None) -> str:
    base = BASE_URL.format(codigo=codigo)
    parametros = []
    if inicio and fim:
        parametros.append("dataInicial=%s&dataFinal=%s" % (inicio, fim))
    elif inicio:
        parametros.append("dataInicial=%s" % inicio)
    if parametros:
        base += "?" + "&".join(parametros)
    return base


def buscar_json(url: str, tentativas: int = 3, espera: float = 2.0) -> list[dict]:
    ultimo_erro: Exception | None = None
    for tentativa in range(1, tentativas + 1):
        try:
            requisicao = urllib.request.Request(
                url,
                headers={"User-Agent": "etl-dados-abertos/0.1 (+portfolio)"},
            )
            with urllib.request.urlopen(requisicao, timeout=30) as resposta:
                return json.loads(resposta.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            ultimo_erro = exc
            log.warning("tentativa %d/%d falhou: %s", tentativa, tentativas, exc)
            time.sleep(espera * tentativa)
    raise ColetaError("nao consegui buscar %s: %s" % (url, ultimo_erro))


def coletar_serie(nome: str, inicio: str | None = None, fim: str | None = None) -> list[dict]:
    if nome not in SERIES:
        raise ColetaError("serie desconhecida: %s" % nome)
    dados = buscar_json(url_da_serie(SERIES[nome]["codigo"], inicio, fim))
    return [{"serie": nome, "data": item["data"], "valor": item["valor"]} for item in dados]


def coletar_tudo(inicio: str | None = None, fim: str | None = None) -> list[dict]:
    registros: list[dict] = []
    for nome in SERIES:
        try:
            registros.extend(coletar_serie(nome, inicio, fim))
        except ColetaError as exc:
            log.error("serie %s ignorada: %s", nome, exc)
    return registros
