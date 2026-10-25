"""Fetch housing series: IPH (Base 2025) + sales count + median EUR/m2."""
from common import fetch_topic

CODES = {
    '0014765': 'IPH index level, Base 2025=100, quarterly, by housing category',
    '0014766': 'IPH quarterly rate (%), Base 2025, by housing category',
    '0014767': 'IPH homolog rate YoY (%), Base 2025, by housing category',
    '0014764': 'Sales of family housing, last 12 months (N.), 2022 Methodology',
    '0014759': 'Median selling price of family housing, last 12 months (EUR/m2)',
    '0012254': 'Median selling price of family housing, annual (EUR/m2), 2022 Methodology',
    '0014698': 'Median rent of new rental contracts for family housing, annual (EUR/m2)',
}

if __name__ == '__main__':
    fetch_topic(CODES)