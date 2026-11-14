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
  housing_census_occupation.csv - classic family dwellings by occupation
                                  status (habitual/secondary/empty), Censos
                                  1950-2021
  housing_census_tenure.csv     - habitual residences by tenure (owner/
                                  rented/other), Censos 2011 + 2021
  housing_census_tenure_2011.csv - Censos 2011 regime-of-occupation detail
  housing_census_stock.csv      - all dwellings by type/occupation/building,
                                  Censos 2021
  housing_eusilc_tenure.csv     - tenure status of the population (EU-SILC,
                                  % of population), annual 2004-2025
  _indicators.json             - indicator descriptions fetched for audit
"""

import csv
import json
import os

from common import (RAW_DIR, TIDY_DIR, load_series, norm_quarter, num,
                    periods_of, pt_records)


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


def housing_stock():
    # occupation status of classic family dwellings (0014378, 1950-2021)
    s = load_series('0014378')
    rows = []
    for p, recs in periods_of(s):
        m = {r.get('dim_3_t', ''): num(r.get('valor')) for r in pt_records(recs)}
        rows.append({'censo_ano': p,
                     'residencia_habitual': m.get('Residência habitual', ''),
                     'residencia_secundaria': m.get('Residência secundária', ''),
                     'vago': m.get('Vago', ''),
                     'total': m.get('Total', '')})
    write_csv('housing_census_occupation.csv',
              ['censo_ano', 'residencia_habitual', 'residencia_secundaria',
               'vago', 'total'], rows)

    # tenure of habitual residences, comparable categories (0011491: 2011
    # recategorized to match Censos 2021 grouping + 2021)
    s = load_series('0011491')
    rows = []
    for p, recs in periods_of(s):
        for r in pt_records(recs):
            rows.append({'censo_ano': p,
                         'regime_de_ocupacao': r.get('dim_3_t', ''),
                         'residencias_habituais': num(r.get('valor'))})
    rows.sort(key=lambda x: (x['censo_ano'], x['regime_de_ocupacao']))
    write_csv('housing_census_tenure.csv',
              ['censo_ano', 'regime_de_ocupacao', 'residencias_habituais'], rows)

    # Censos 2011 original regime-of-occupation detail (0006338)
    s = load_series('0006338')
    rows = []
    for p, recs in periods_of(s):
        for r in pt_records(recs):
            rows.append({'censo_ano': p,
                         'regime_de_ocupacao': r.get('dim_3_t', ''),
                         'residencias_habituais': num(r.get('valor'))})
    rows.sort(key=lambda x: (x['censo_ano'], x['regime_de_ocupacao']))
    write_csv('housing_census_tenure_2011.csv',
              ['censo_ano', 'regime_de_ocupacao', 'residencias_habituais'], rows)

    # all dwellings by type, occupation status and building (0012499, 2021)
    s = load_series('0012499')
    rows = []
    for p, recs in periods_of(s):
        for r in pt_records(recs):
            rows.append({'censo_ano': p,
                         'categoria': r.get('dim_3_t', ''),
                         'alojamentos': num(r.get('valor'))})
    rows.sort(key=lambda x: (x['censo_ano'], x['categoria']))
    write_csv('housing_census_stock.csv',
              ['censo_ano', 'categoria', 'alojamentos'], rows)

    # tenure status of the population, annual (Eurostat ilc_lvho02, EU-SILC)
    with open(os.path.join(RAW_DIR, 'eurostat_ilc_lvho02.json'),
              encoding='utf-8') as f:
        eu = json.load(f)
    order = list(eu['dimension'].keys())
    id_of = {dim: dict(eu['dimension'][dim]['category']['index'])
             for dim in order}
    strides = {}
    mult = 1
    for dim in reversed(order):
        strides[dim] = mult
        mult *= len(id_of[dim])

    def value_row(tenure, year):
        """Flat-index lookup; fixed codes verified against dimension keys:
        freq=A, rskpovth=TOTAL, hhcomp=TOTAL, unit=PC, geo=PT."""
        idx = 0
        for dim in order:
            code = {'freq': 'A', 'rskpovth': 'TOTAL', 'hhcomp': 'TOTAL',
                    'tenure': tenure, 'unit': 'PC', 'geo': 'PT',
                    'time': str(year)}[dim]
            idx += id_of[dim][code] * strides[dim]
        return eu['value'].get(str(idx))

    years = sorted(eu['dimension']['time']['category']['index'],
                   key=lambda y: int(y))
    rows = []
    for y in years:
        r = {'ano': y}
        vals = []
        for col, ten in [('owner_pct', 'OWN'),
                         ('owner_with_loan_pct', 'OWN_L'),
                         ('owner_without_loan_pct', 'OWN_NL'),
                         ('tenant_pct', 'RENT'),
                         ('tenant_market_rent_pct', 'RENT_MKT'),
                         ('tenant_reduced_or_free_pct', 'RENT_FR')]:
            v = value_row(ten, y)
            r[col] = v if v is not None else ''
            if v is not None:
                vals.append(v)
        if vals:  # drop fully-empty years (2003)
            rows.append(r)
    write_csv('housing_eusilc_tenure.csv',
              ['ano', 'owner_pct', 'owner_with_loan_pct',
               'owner_without_loan_pct', 'tenant_pct',
               'tenant_market_rent_pct', 'tenant_reduced_or_free_pct'], rows)


def housing_vacancy_estimate():
    """Residual estimate of habitually vacant dwellings after Censos 2021.

    Method (documented in README): vacant stock evolves from the Censos 2021
    baseline (0012499) by adding dwellings completed (0011724) and
    subtracting the estimated growth in households, held at constant average
    household size (Censos 2021: pop / households). Household growth is
    driven by the annual resident-population estimates (0013356). Because the
    Censos 2021 census population (10,347,892) and the revised 31-Dec-2021
    estimate (10,599,117) disagree by +251,225, two anchor variants are
    produced: 'estimates' (households base scaled upward with the revised
    population, internally consistent Dec-2021 -> Dec-2025 change) and
    'census' (unscaled census households base, change taken against the
    census population). Demolitions are an assumed constant (INE publishes
    no demolition series) and secondary-home growth is an assumed rate.
    Household growth is split into a migratory and a natural component: the
    estimated net migration (0013179, migratory component of the same
    population estimates) forms migrant households at its own size
    parameter, and the residual natural change (births - deaths plus
    statistical corrections) forms households at the base size; when the
    two sizes are equal the model is identical to the homogeneous one.
    """
    # census 2021 baseline: all dwellings by occupation status (0012499)
    s = load_series('0012499')
    vac21 = tot21 = None
    for rec in s['dados']['2021']:
        if rec.get('geocod') == 'PT':
            if rec.get('dim_3_t') == 'Vagos':
                vac21 = num(rec['valor'])
            elif rec.get('dim_3_t') == 'Total':
                tot21 = num(rec['valor'])
    if vac21 != 723215 or tot21 != 5981482:
        raise RuntimeError(
            f'0012499 census baseline drifted: vagos={vac21}, total={tot21}'
            ' (reference: 723215 / 5981482 in Censos 2021)')

    # dwellings completed, long series (0011724)
    comps = {}
    for p, recs in periods_of(load_series('0011724')):
        for r in pt_records(recs):
            v = num(r.get('valor'))
            if v != '':
                comps[p] = v

    # dwellings completed in new construction for family housing (0013248):
    # alternate INE source kept for the two-series comparison in README
    comps_new = {}
    for p, recs in periods_of(load_series('0013248')):
        for r in pt_records(recs):
            if r.get('dim_3_t') == 'Total':
                v = num(r.get('valor'))
                if v != '':
                    comps_new[p] = v

    years = sorted(set(comps) | set(comps_new))
    rows = [{'ano': y,
             'fogos_concluidos': comps.get(y, ''),
             'fogos_concluidos_construcoes_novas_hab_familiar':
                 comps_new.get(y, '')} for y in years]
    write_csv('housing_completions.csv',
              ['ano', 'fogos_concluidos',
               'fogos_concluidos_construcoes_novas_hab_familiar'], rows)

    # resident population estimates, annual (0013356): HM rows summed
    # over the three urban typologies (verified national totals:
    # 2021: 10,599,117 / 2025: 11,424,031)
    pop = {}
    for p, recs in periods_of(load_series('0013356')):
        vals = [num(r.get('valor')) for r in pt_records(recs)
                if r.get('dim_3_t') == 'HM' and num(r.get('valor')) != '']
        pop[p] = sum(vals)
    if abs(pop['2025'] - 11424031) > 1 or abs(pop['2021'] - 10599117) > 1:
        raise RuntimeError(
            f'0013356 population estimates drifted: {pop}')

    # estimated net migration (0013179): migratory component of the same
    # population estimates; 2025 figure is INE's preliminary estimate
    mig = {}
    for p, recs in periods_of(load_series('0013179')):
        for r in pt_records(recs):
            v = num(r.get('valor'))
            if v != '':
                mig[p] = v
    if mig.get('2021') != 250079 or mig.get('2022') != 371277:
        raise RuntimeError(f'0013179 net migration drift: {mig}')

    # census constants (Censos 2021 definitive results; documented in README,
    # not reproducible from the fetched series)
    cen_pop = 10347892
    cen_hh = 4149096
    size = cen_pop / cen_hh
    hh_base_scaled = cen_hh * (pop['2021'] / cen_pop)

    def decompose(anchor, size_, dem_y, sec_pct, size_mig=None):
        """Per-year vacancy path under one scenario; dict year -> fields."""
        size_mig = size_ if size_mig is None else size_mig
        out = {}
        stock_hh = cen_hh if anchor == 'census' else hh_base_scaled
        vacant = vac21
        secondary = 1104881  # Censos 2021 secondary/saasonal dwellings
        prev_pop = cen_pop if anchor == 'census' else pop['2021']
        for y in ('2022', '2023', '2024', '2025'):
            dpop = pop[y] - prev_pop
            mighh = mig[y] / size_mig
            nathh = (dpop - mig[y]) / size_
            dhh = mighh + nathh
            stock_hh += dhh
            comp = comps.get(y, 0)
            dem = dem_y
            sec_g = secondary * sec_pct
            secondary += sec_g
            vacant = vacant + comp - dhh - dem - sec_g
            prev_pop = pop[y]
            out[y] = {'ano': y,
                      'variante_ancoragem': anchor,
                      'populacao_residente_est': pop[y],
                      'variacao_populacao': dpop,
                      'tamanho_hh': round(size_, 4),
                      'saldo_migratorio': mig[y],
                      'crescimento_hh': round(dhh),
                      'crescimento_hh_migratorio': round(mighh),
                      'crescimento_hh_natural': round(nathh),
                      'stock_hh_estimado': round(stock_hh),
                      'fogos_concluidos': comps.get(y, ''),
                      'demolicoes_supostas': dem,
                      'crescimento_resid_secundarias': round(sec_g),
                      'vagos_estimados': round(vacant),
                      'vagos_censo_2021': vac21}
        out['2021'] = {'ano': '2021', 'variante_ancoragem': anchor,
                       'populacao_residente_est': pop['2021'],
                       'variacao_populacao': '', 'tamanho_hh': round(size_, 4),
                       'crescimento_hh': '',
                       'saldo_migratorio': '',
                       'crescimento_hh_migratorio': '',
                       'crescimento_hh_natural': '',
                       'stock_hh_estimado': (cen_hh if anchor == 'census'
                                             else round(hh_base_scaled)),
                       'fogos_concluidos': '', 'demolicoes_supostas': '',
                       'crescimento_resid_secundarias': '',
                       'vagos_estimados': vac21, 'vagos_censo_2021': vac21}
        return out

    # two published variants: internally-consistent estimates anchor and the
    # conservative census anchor (larger household growth, smaller vacancy)
    dec = decompose('estimates', size, 0, 0)  # raw path, no adjustments
    dec_cen = decompose('census', size, 0, 0)
    rows = []
    for variant in (dec, dec_cen):
        rows.extend(variant[y] for y in ('2021', '2022', '2023', '2024',
                                         '2025'))
    cols = ['variante_ancoragem', 'ano', 'populacao_residente_est',
            'variacao_populacao', 'tamanho_hh', 'saldo_migratorio',
            'crescimento_hh', 'crescimento_hh_migratorio',
            'crescimento_hh_natural', 'stock_hh_estimado',
            'fogos_concluidos', 'demolicoes_supostas',
            'crescimento_resid_secundarias', 'vagos_estimados',
            'vagos_censo_2021']
    rows.sort(key=lambda x: (x['variante_ancoragem'], x['ano']))
    write_csv('housing_vacancy_decomposition.csv', cols, rows)

    # scenario grid, 2025 vacancy: anchors x sizes, migration split, corners
    scen = []
    for anchor in ('estimates', 'census'):
        for s_ in (2.40, size, 2.70):
            pth = decompose(anchor, s_, 0, 0)
            scen.append({'cenario': f'{anchor}_tamanho{round(s_, 2)}',
                         'ancoragem': anchor,
                         'tamanho_hh': round(s_, 4),
                         'tamanho_hh_migratorio': round(s_, 4),
                         'demolicoes_por_ano': 0,
                         'cresc_secundarias_pct_ano': 0,
                         'vagos_2025': pth['2025']['vagos_estimados']})
        # split scenarios: national-average size for natural-growth
        # households, alternate size for migrant households (band spans
        # single adults to large families; INE publishes no immigrant
        # household-size vintage)
        for sm in (2.0, 3.0):
            pth = decompose(anchor, size, 0, 0, size_mig=sm)
            scen.append({'cenario': f'{anchor}_hh_migr{round(sm, 1)}',
                         'ancoragem': anchor,
                         'tamanho_hh': size,
                         'tamanho_hh_migratorio': sm,
                         'demolicoes_por_ano': 0,
                         'cresc_secundarias_pct_ano': 0,
                         'vagos_2025': pth['2025']['vagos_estimados']})
    v_low = decompose('census', 2.40, 4000, 0.01)['2025']['vagos_estimados']
    v_high = decompose('estimates', 2.70, 0, 0)['2025']['vagos_estimados']
    v_cen = decompose('estimates', size, 2000, 0)['2025']['vagos_estimados']
    scen.append({'cenario': 'low', 'ancoragem': 'census',
                 'tamanho_hh': 2.4, 'tamanho_hh_migratorio': 2.4,
                 'demolicoes_por_ano': 4000,
                 'cresc_secundarias_pct_ano': 1, 'vagos_2025': v_low})
    scen.append({'cenario': 'high', 'ancoragem': 'estimates',
                 'tamanho_hh': 2.7, 'tamanho_hh_migratorio': 2.7,
                 'demolicoes_por_ano': 0,
                 'cresc_secundarias_pct_ano': 0, 'vagos_2025': v_high})
    scen.append({'cenario': 'central', 'ancoragem': 'estimates',
                 'tamanho_hh': round(size, 4),
                 'tamanho_hh_migratorio': round(size, 4),
                 'demolicoes_por_ano': 2000,
                 'cresc_secundarias_pct_ano': 0, 'vagos_2025': v_cen})
    scen.sort(key=lambda x: x['vagos_2025'])
    write_csv('housing_vacancy_scenarios.csv',
              ['cenario', 'ancoragem', 'tamanho_hh', 'tamanho_hh_migratorio',
               'demolicoes_por_ano', 'cresc_secundarias_pct_ano',
               'vagos_2025'], scen)


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
    housing_stock()
    housing_vacancy_estimate()
    salaries()
    immigration()
    inequality()
    meta = {}
    for var in ('0014765', '0014766', '0014767', '0014764', '0012254', '0014698',
                '0014378', '0011491', '0006338', '0012499',
                '0011724', '0013248', '0013247', '0013356',
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
