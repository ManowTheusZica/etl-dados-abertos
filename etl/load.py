"""Carga idempotente em SQLite: rodar duas vezes nao duplica."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ESQUEMA = """
CREATE TABLE IF NOT EXISTS indicadores (
    serie TEXT NOT NULL,
    mes   TEXT NOT NULL,
    valor REAL NOT NULL,
    obs   INTEGER NOT NULL DEFAULT 1,
    atualizado_em TEXT NOT NULL,
    PRIMARY KEY (serie, mes)
);

CREATE TABLE IF NOT EXISTS execucoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inicio TEXT NOT NULL,
    fim TEXT,
    registros INTEGER,
    situacao TEXT,
    detalhe TEXT
);
"""


def conectar(caminho: str) -> sqlite3.Connection:
    Path(caminho).parent.mkdir(parents=True, exist_ok=True)
    conexao = sqlite3.connect(caminho)
    conexao.executescript(ESQUEMA)
    return conexao


def iniciar_execucao(conexao: sqlite3.Connection) -> int:
    cursor = conexao.execute(
        "INSERT INTO execucoes (inicio, situacao) VALUES (?, 'rodando')",
        (datetime.now(timezone.utc).isoformat(timespec="seconds"),),
    )
    conexao.commit()
    return int(cursor.lastrowid)


def carregar(conexao: sqlite3.Connection, registros_mensais: list[dict]) -> int:
    agora = datetime.now(timezone.utc).isoformat(timespec="seconds")
    linhas = [
        (item["serie"], item["mes"], item["valor"], item.get("obs", 1), agora)
        for item in registros_mensais
    ]
    conexao.executemany(
        """
        INSERT INTO indicadores (serie, mes, valor, obs, atualizado_em)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(serie, mes) DO UPDATE SET
            valor = excluded.valor,
            obs = excluded.obs,
            atualizado_em = excluded.atualizado_em
        """,
        linhas,
    )
    conexao.commit()
    return len(linhas)


def finalizar_execucao(
    conexao: sqlite3.Connection, execucao_id: int, registros: int, situacao: str, detalhe: str = ""
) -> None:
    conexao.execute(
        "UPDATE execucoes SET fim = ?, registros = ?, situacao = ?, detalhe = ? WHERE id = ?",
        (datetime.now(timezone.utc).isoformat(timespec="seconds"), registros, situacao, detalhe, execucao_id),
    )
    conexao.commit()


def ler_serie(conexao: sqlite3.Connection, serie: str) -> list[tuple[str, float]]:
    return list(
        conexao.execute(
            "SELECT mes, valor FROM indicadores WHERE serie = ? ORDER BY mes", (serie,)
        )
    )
