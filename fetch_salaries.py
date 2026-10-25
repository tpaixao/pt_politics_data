"""Fetch salary series: average monthly base earnings (Quadros de Pessoal, GEP)."""
from common import fetch_topic

CODES = {
    '0014410': 'Average monthly base remuneration (EUR), annual, by NUTS-2024/sex/age group',
    '0014111': 'Average annual remuneration per employee (Base 2021, EUR), 1995-, by NUTS/sector',
}
# note: 0014758 (gross monthly avg) currently has only one period published; skip

if __name__ == '__main__':
    fetch_topic(CODES)