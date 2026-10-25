"""Build tidy CSVs from raw INE JSON in data/raw/.

Outputs (data/tidy/):
  housing_quarterly.csv        - IPH Total/Novos/Existentes YoY, QoQ, index
                                 Base 2025, sales count (12m, 2026 only)
  housing_annual_medians.csv   - median selling price EUR/m2 (2019-),
                                 median rent of new contracts EUR/m2 (2020-)
  salaries_annual.csv          - average monthly base earnings detail 2021-2024
                                 (Portugal rows: sex x age-group)
  salaries_annual_rem.csv      - average ANNUAL remuneration per employee
                                 (Base 2021), 1995-, Portugal, total sector
  immigration_annual.csv       - long detail (one row per dim combination;
                                 67k rows: flows by sex/age/nationality,
                                 stock by sex/nationality)
  immigration_totals.csv       - compact: migratory balance, foreign resident
                                 stock (total), permanent immigrant inflow
  inequality_annual.csv        - income Gini and S80/S20 (EU-SILC/ICV)
  _indicators.json             - indicator descriptions fetched for audit
"""

import csv
import json
import os

from common import (TIDY_DIR, load_series, norm_quarter, num, periods_of,
                    pt_records)


def write_csv(name, cols, rows):
    path = os.path.join(TIDY_DIR, name)
    with open(path, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction='ignore')
        w.writeheader()
        w.writerows(rows)
    print(f'{name}: {len(rows)} rows')


def housing():
    yoy = load_series('0014767')
    qoq = load_series('0014766')
    idx = load_series('0014765')
    sales = load_series('0014764')

    def records(series, pq):
        for raw_p in series['dados']:
            if norm_quarter(raw_p) == pq:
                return series['dados'][raw_p]
        return []

    def pt_float(records_list, extra_dims=False):
        vals = [num(r.get('valor')) for r in pt_records(records_list)]
        vals = [v for v in vals if v != '']
        return vals[0] if len(vals) == 1 else ''

    all_pq = sorted({norm_quarter(p) for p in yoy['dados']} |
                    {norm_quarter(p) for p in idx['dados']} |
                    {norm_quarter(p) for p in qoq['dados']})

    rows = []
    for pq in all_pq:
        ymap = {r['dim_3']: num(r.get('valor')) for r in records(yoy, pq)}
        qmap = {r['dim_3']: num(r.get('valor')) for r in records(qoq, pq)}
        imap = {r['dim_3']: num(r.get('valor')) for r in records(idx, pq)}
        rows.append({
            'periodo': pq,
            'yoy_total_pct': ymap.get('H1', ''),
            'yoy_novos_pct': ymap.get('H11', ''),
            'yoy_existentes_pct': ymap.get('H12', ''),
            'qoq_total_pct': qmap.get('H1', ''),
            'iph_index_base2025': imap.get('H1', ''),
            'vendas_12m': pt_float(records(sales, pq)),
        })
    write_csv('housing_quarterly.csv',
              ['periodo', 'yoy_total_pct', 'yoy_novos_pct', 'yoy_existentes_pct',
               'qoq_total_pct', 'iph_index_base2025', 'vendas_12m'], rows)

    # annual medians: sales EUR/m2 (0012254, by tipologia; total = dim_3 'T')
    # and rents EUR/m2 (0014698, no extra dims)
    vs = load_series('0012254')
    rn = load_series('0014698')
    vmap = {}
    for pq, recs in periods_of(vs):
        for r in pt_records(recs):
            if r.get('dim_3_t') == 'Total' and num(r.get('valor')) != '':
                vmap[pq] = num(r['valor'])
    rmap = {}
    for pq, recs in periods_of(rn):
        vals = [num(r.get('valor')) for r in pt_records(recs) if num(r.get('valor')) != '']
        if vals:
            rmap[pq] = vals[0] if len(vals) == 1 else ''
    years = sorted(set(vmap) | set(rmap))
    rows2 = [{'ano': y, 'mediano_vendas_eur_m2': vmap.get(y, ''),
              'mediano_rendas_novos_contratos_eur_m2': rmap.get(y, '')}
             for y in years]
    write_csv('housing_annual_medians.csv',
              ['ano', 'mediano_vendas_eur_m2', 'mediano_rendas_novos_contratos_eur_m2'], rows2)


def salaries():
    # detail: monthly base remuneration 2021-2024 (0014410)
    s = load_series('0014410')
    rows = []
    for pq, recs in periods_of(s):
        for rec in pt_records(recs):
            rows.append({
                'ano': pq,
                'sexo': rec.get('dim_3_t', ''),
                'grupo_etario': rec.get('dim_4_t', ''),
                'rem_media_base_eur_mensal': num(rec.get('valor')),
            })
    write_csv('salaries_annual.csv',
              ['ano', 'sexo', 'grupo_etario', 'rem_media_base_eur_mensal'], rows)

    # long series: average ANNUAL remuneration per employee, Base 2021 (0014111)
    s2 = load_series('0014111')
    rows2 = []
    for pq, recs in periods_of(s2):
        for rec in pt_records(recs):
            if rec.get('dim_3_t') == 'Total':
                rows2.append({'ano': pq,
                              'rem_media_anual_eur': num(rec.get('valor'))})
    write_csv('salaries_annual_rem.csv',
              ['ano', 'rem_media_anual_eur'], rows2)


def immigration():
    rows = []
    meta = {}
    for var, label in [('0013179', 'saldo_migratorio'),
                       ('0006054', 'imigrantes_permanentes'),   # by sex, age groups, nationality groups
                       ('0006056', 'imigrantes_permanentes'),   # by sex, age groups, country of birth
                       ('0006055', 'imigrantes_permanentes'),   # by sex, single-year age, country of birth
                       ('0006057', 'imigrantes_permanentes'),   # by sex, single-year age, nationality
                       ('0001274', 'pop_estrangeira_residente'),  # stock by sex, 1980-
                       ('0013219', 'pop_estrangeira_residente')]:  # stock by NUTS/nationality, 2021-
        try:
            s = load_series(var)
        except FileNotFoundError:
            continue
        meta[var] = {'label': label, 'indicador': s['indicador']}
        for pq, recs in periods_of(s):
            for rec in pt_records(recs):
                row = {'serie': label, 'varcd': var, 'ano': pq,
                       'sexo': rec.get('dim_3_t', ''),
                       'dim_a': rec.get('dim_4_t', ''),
                       'dim_b': rec.get('dim_5_t', ''),
                       'valor': num(rec.get('valor'))}
                rows.append(row)
    write_csv('immigration_annual.csv',
              ['serie', 'varcd', 'ano', 'sexo', 'dim_a', 'dim_b', 'valor'], rows)

    # compact totals
    tot_rows = []
    saldo = load_series('0013179')
    for pq, recs in periods_of(saldo):
        for rec in pt_records(recs):
            if num(rec.get('valor')) != '':
                tot_rows.append({'serie': 'saldo_migratorio', 'ano': pq,
                                 'valor': num(rec['valor'])})
    stock = load_series('0001274')
    for pq, recs in periods_of(stock):
        for rec in pt_records(recs):
            if rec.get('dim_3_t') == 'HM' and num(rec.get('valor')) != '':
                tot_rows.append({'serie': 'pop_estrangeira_residente_HM', 'ano': pq,
                                 'valor': num(rec['valor'])})
    flow = load_series('0006054')
    for pq, recs in periods_of(flow):
        for rec in pt_records(recs):
            if (rec.get('dim_3_t') == 'HM' and rec.get('dim_4_t') == 'Total'
                    and rec.get('dim_5_t', '').startswith('Total')
                    and num(rec.get('valor')) != ''):
                tot_rows.append({'serie': 'imigrantes_permanentes_HM', 'ano': pq,
                                 'valor': num(rec['valor'])})
    write_csv('immigration_totals.csv', ['serie', 'ano', 'valor'], tot_rows)


def inequality():
    def year_values(var, total_rule):
        s = load_series(var)
        out = {}
        for pq, recs in periods_of(s):
            vals = [num(r.get('valor')) for r in pt_records(recs)
                    if num(r.get('valor')) != '' and total_rule(r)]
            if vals:
                out[pq] = vals[0] if len(vals) == 1 else ''
        return out

    gini = year_values('0004212', lambda r: r.get('dim_3_t', '') in ('', 'Total'))
    s80 = year_values('0004213', lambda r: r.get('dim_4_t') == 'Total'
                      and r.get('dim_3_t') in ('HM', 'T'))
    years = sorted(set(gini) | set(s80))
    rows = [{'ano': y, 'gini_rendimento_liquido': gini.get(y, ''),
             's80s20_rendimento_liquido': s80.get(y, '')} for y in years]
    write_csv('inequality_annual.csv',
              ['ano', 'gini_rendimento_liquido', 's80s20_rendimento_liquido'], rows)


def main():
    os.makedirs(TIDY_DIR, exist_ok=True)
    housing()
    salaries()
    immigration()
    inequality()
    meta = {}
    for var in ('0014765', '0014766', '0014767', '0014764', '0012254', '0014698',
                '0014410', '0014111',
                '0013179', '0006054', '0006055', '0006056', '0006057', '0001274',
                '0013219', '0004212', '0004213'):
        p = os.path.join('data', 'raw', f'ine_{var}.json')
        if os.path.exists(p):
            s = load_series(var)
            meta[var] = s['indicador']
    with open(os.path.join(TIDY_DIR, '_indicators.json'), 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    print('indicators:', len(meta))


if __name__ == '__main__':
    main()