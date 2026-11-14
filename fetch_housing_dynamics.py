"""Fetch housing-dynamics series for the vacancy residual estimate.

INE annual series (all from INE, CC BY 4.0):
  0013248 - Fogos concluidos (N.) em construcoes novas para habitacao
            familiar, NUTS-2024, Tipologia do fogo; Anual
            (Estatisticas das obras concluidas)
  0013247 - Edificios concluidos (N.), NUTS-2024, Tipo de obra e Destino
            da obra; Anual (Estatisticas das obras concluidas)
            (Tipo de obra is where demolitions may be reported)
  0011724 - Fogos concluidos (Serie longa, inicio 1975 - N.); Anual,
            Portugal (Inquerito aos projetos de obras)
  0013356 - Populacao residente (N.), NUTS-2024, Sexo, Tipologia de areas
            urbanas; Anual (Estimativas anuais da populacao residente)
"""
from common import fetch_topic

INE_CODES = {
    '0013248': 'dwellings completed, new construction, NUTS-2024 (annual)',
    '0013247': 'buildings completed by work type and destination, NUTS-2024 (annual)',
    '0011724': 'dwellings completed, long series from 1975, Portugal (annual)',
    '0013356': 'resident population estimates, NUTS-2024 by sex (annual)',
}

if __name__ == '__main__':
    res = fetch_topic(INE_CODES)
    for var, info in res.items():
        print(var, info)
