"""Fetch housing-stock / occupation / tenure series.

INE Censos (decennial):
  0014378 - classic family dwellings by occupation status (1950-2021)
  0011491 - habitual residences by tenure (Regime de ocupacao), Censos 2021
  0006338 - habitual residences by tenure (Regime de ocupacao), Censos 2011
  0012499 - all dwellings by type, occupation status and building, Censos 2021
Eurostat:
  ilc_lvho02 - tenure status of the population (EU-SILC, %, annual)
               Portugal rows; top-level OWN / RENT plus sub-splits
               (OWN_L, OWN_NL, RENT_MKT, RENT_FR) kept for detail
"""
import json
import os
import urllib.request

from common import RAW_DIR, fetch_json, fetch_topic

INE_CODES = {
    '0014378': 'classic family dwellings by occupation status (Censos 1950-2021)',
    '0011491': 'habitual residences by tenure (Censos 2021, NUTS-2013)',
    '0006338': 'habitual residences by tenure (Censos 2011, NUTS-2013)',
    '0012499': 'dwellings by type, occupation status and building (Censos 2021)',
}

EUROSTAT_URL = ('https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/'
                'data/ilc_lvho02?lang=EN&geo=PT')


def fetch_eurostat_tenure():
    """Save raw Eurostat ilc_lvho02 (Portugal) for the tenure annual series.

    Fetched wholesale with geo=PT only; per-dimension filtering (rskpovth /
    hhcomp Total rows) happens in build_tidy.py against the raw JSON, so no
    code guesses are needed here.
    """
    print('fetch eurostat ilc_lvho02 (tenure of population, PT) ... ', end='',
          flush=True)
    data = fetch_json(EUROSTAT_URL)
    path = os.path.join(RAW_DIR, 'eurostat_ilc_lvho02.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    ids = list(data['dimension'].keys())
    n_values = len(data['value'])
    print(f'ok dims={ids}, value cells={n_values}, updated={data.get("updated")}')


if __name__ == '__main__':
    res = fetch_topic(INE_CODES)
    fetch_eurostat_tenure()
