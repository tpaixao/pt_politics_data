"""Fetch income inequality series (INE, Inquerito as Condicoes de Vida / EU-SILC).

IMPORTANT methodology note (README): official annual inequality stats for
Portugal are *income* inequality. There is NO official annual wealth-distribution
series; net-wealth distribution only exists via Banco de Portugal's HFCS survey
(waves 2013, 2017, 2020...) and must be downloaded manually from:
https://www.bportugal.pt/estatisticas/inquerito-financas-consumo-hfc (Inquerito
a Situacao Financeira dos Agregados Domesticos). That data is NOT automated here.
"""
from common import fetch_topic

CODES = {
    '0004212': 'Gini coefficient of net monetary income per equivalent adult (%)',
    '0004213': 'Income distribution inequality S80/S20 (N.)',
}

if __name__ == '__main__':
    fetch_topic(CODES)