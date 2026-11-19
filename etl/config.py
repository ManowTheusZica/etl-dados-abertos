"""Series do Banco Central (SGS) usadas no projeto. Sem chave de API."""
from __future__ import annotations

BASE_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados"

SERIES = {
    "ipca": {"codigo": 433, "nome": "IPCA (variacao mensal %)", "unidade": "%"},
    "selic": {"codigo": 432, "nome": "Meta Selic (% ao ano)", "unidade": "% a.a."},
    "dolar": {"codigo": 1, "nome": "Dolar comercial (venda, R$)", "unidade": "R$"},
}

BANCO_PADRAO = "dados/indicadores.db"
