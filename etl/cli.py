"""Linha de comando: python -m etl.cli run --desde 01/01/2019"""
from __future__ import annotations

import argparse
import logging
import sys

from .config import BANCO_PADRAO, SERIES
from .extract import ColetaError, coletar_tudo
from .insights import melhor_defasagem, extremos, media_por_ano
from .load import carregar, conectar, finalizar_execucao, iniciar_execucao, ler_serie
from .transform import agregar_mensal, normalizar

log = logging.getLogger("etl")


def rodar(inicio: str | None, fim: str | None, banco: str) -> int:
    conexao = conectar(banco)
    execucao = iniciar_execucao(conexao)
    try:
        brutos = coletar_tudo(inicio, fim)
        if not brutos:
            finalizar_execucao(conexao, execucao, 0, "erro", "nenhum registro coletado")
            log.error("nenhum registro coletado")
            return 1
        limpos = normalizar(brutos)
        mensais = agregar_mensal(limpos)
        total = carregar(conexao, mensais)
        finalizar_execucao(conexao, execucao, total, "ok")
        print("carregados %d registros mensais" % total)
        _imprimir_insights(conexao)
        return 0
    except ColetaError as exc:
        finalizar_execucao(conexao, execucao, 0, "erro", str(exc))
        log.error("%s", exc)
        return 2


def _imprimir_insights(conexao) -> None:
    ipca = ler_serie(conexao, "ipca")
    selic = ler_serie(conexao, "selic")
    dolar = ler_serie(conexao, "dolar")

    if ipca:
        print("\nIPCA - meses com maior variacao:")
        for mes, valor in extremos(ipca, True, 5):
            print("  %s  %+.2f%%" % (mes, valor))
        print("IPCA - media por ano:")
        for ano, valor in media_por_ano(ipca)[-5:]:
            print("  %s  %+.2f%%" % (ano, valor))

    if ipca and selic:
        achado = melhor_defasagem(selic, ipca)
        if achado:
            print("\nSelic x IPCA: melhor defasagem = %d mes(es), r = %.3f" % achado)

    if ipca and dolar:
        achado = melhor_defasagem(dolar, ipca)
        if achado:
            print("Dolar x IPCA: melhor defasagem = %d mes(es), r = %.3f" % achado)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ETL de indicadores do Banco Central")
    sub = parser.add_subparsers(dest="comando", required=True)

    rodar_cmd = sub.add_parser("run", help="coleta, trata e carrega")
    rodar_cmd.add_argument("--desde", default=None, help="dd/mm/aaaa")
    rodar_cmd.add_argument("--ate", default=None, help="dd/mm/aaaa")
    rodar_cmd.add_argument("--banco", default=BANCO_PADRAO)

    status = sub.add_parser("status", help="mostra o que ja esta carregado")
    status.add_argument("--banco", default=BANCO_PADRAO)

    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    if args.comando == "run":
        return rodar(args.desde, args.ate, args.banco)

    conexao = conectar(args.banco)
    for nome in SERIES:
        linhas = ler_serie(conexao, nome)
        if linhas:
            print("%-6s %4d meses  de %s a %s" % (nome, len(linhas), linhas[0][0], linhas[-1][0]))
        else:
            print("%-6s vazio" % nome)
    return 0


if __name__ == "__main__":
    sys.exit(main())
