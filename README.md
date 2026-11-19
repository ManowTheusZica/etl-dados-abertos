# ETL de indicadores publicos + dashboard

![CI](https://github.com/ManowTheusZica/etl-dados-abertos/actions/workflows/ci.yml/badge.svg) ![Python](https://img.shields.io/badge/python-3.12+-3776AB?logo=python&logoColor=white)


Pipeline que coleta series do Banco Central (API SGS, sem chave), trata os dados,
carrega em SQLite de forma idempotente e serve um dashboard com graficos e analise
de correlacao com defasagem.

## Rodando

```bash
pip install -r requirements.txt
python -m etl.cli run --desde 01/01/2019        # coleta, trata, carrega e imprime insights
python -m etl.cli status                        # o que ja esta no banco
uvicorn dashboard.app:app --port 8010           # dashboard em http://localhost:8010
```

## Series coletadas

- `ipca` (SGS 433) - variacao mensal do IPCA
- `selic` (SGS 432) - meta Selic
- `dolar` (SGS 1) - dolar comercial, agregado em media mensal

## Resultado de uma execucao real (2019 a nov/2026)

```
carregados 285 registros mensais

IPCA - meses com maior variacao:
  2022-03  +1.62%
  2020-12  +1.35%
  2025-02  +1.31%
  2021-10  +1.25%
  2021-09  +1.16%
IPCA - media por ano:
  2022  +0.49%
  2023  +0.38%
  2024  +0.37%
  2025  +0.43%
  2026  +0.38%

Selic x IPCA: melhor defasagem = 12 mes(es), r = -0.859
Dolar x IPCA: melhor defasagem = 4 mes(es), r = +0.359
```

Leitura: a correlacao entre a Selic e o IPCA acumulado em 12 meses e **-0.86** quando
a Selic e deslocada em 12 meses. Juro alto hoje aparece como inflacao menor um ano
depois - o sinal negativo e a forca batem com o que a politica monetaria espera.
O dolar tem correlacao positiva e mais fraca (+0.36) com 4 meses de defasagem.

## Arquitetura

```
etl/
  config.py    series e endpoint
  extract.py   coleta com retry e backoff (urllib puro, sem dependencia)
  transform.py data dd/mm/aaaa, numero nos dois formatos, dedupe, agregacao mensal
  load.py      upsert idempotente + log de execucoes
  acumulado.py IPCA acumulado em 12 meses
  insights.py  Pearson, alinhamento com defasagem, extremos, media por ano
  cli.py       comandos run e status
dashboard/app.py  FastAPI + SVG gerado no servidor (sem CDN, funciona offline)
tests/            16 testes
```

## Decisoes que valem explicar em entrevista

- **Idempotencia**: `INSERT ... ON CONFLICT DO UPDATE` na chave (serie, mes). Rodar
  duas vezes nao duplica e ainda corrige valor se a fonte revisar.
- **Log de execucao**: tabela `execucoes` guarda inicio, fim, quantidade e erro -
  sem isso nao se sabe se a falha foi na coleta ou na carga.
- **Numero nos dois formatos**: a API do Bacen manda `0.53`; planilha brasileira manda
  `1.234,56`. O parser aceita os dois (bug que ja apareceu em producao).
- **Correlacao com defasagem**: alinhar series por mes e varrer 0..12 meses. Correlacao
  sem defasagem da ~0 e engana; com 12 meses o sinal aparece.
- **Validacao numerica**: `correlacao([1,2,3,4],[2,4,6,8])` tem que dar exatamente 1.0 -
  tem teste para isso, porque a primeira versao dividia a covariancia por n e devolvia 0.25.
