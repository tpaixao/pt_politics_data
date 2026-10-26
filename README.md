# pt_politics_data

Official-source datasets behind a planned series of infographics about
current topics in Portuguese politics. One fetch script per topic, one
shared tidy builder. All stdlib-only Python 3.11+ (host has no pandas).

## Usage

```bash
python3 fetch_housing.py && python3 fetch_salaries.py      # ~2-4 min each, API retries built in
python3 fetch_immigration.py && python3 fetch_wealth.py
python3 build_tidy.py
python3 fetch_fund_management.py                           # BdP/BPstat real-estate funds (standalone)
```

## Topics

### Housing (INE)
- `housing_quarterly.csv` — 2009Q1–2026Q2: IPH YoY (total / Novos / Existentes),
  QoQ, index Base 2025=100, 12-month sales count (2022 Methodology, 2026 only so far)
- `housing_annual_medians.csv` — median selling price EUR/m² (2019–2025) and
  median rent of new contracts EUR/m² (2020–2025)

### Salaries (INE / MTSSS-GEP Quadros de Pessoal)
- `salaries_annual.csv` — average monthly base remuneration EUR, Portugal,
  by sex and age group (2021–2024, current methodology)
- `salaries_annual_rem.csv` — average ANNUAL remuneration per employee
  (Base 2021), 1995–2023, Portugal total. The long series; use for trend plots.

### Immigration (INE)
- `immigration_totals.csv` — **the headline numbers**: migratory balance,
  foreign resident stock (total), permanent immigrant inflows (total),
  annual. 2023: ~462k permanent immigrants; 2024: ~395k; 2025: ~254k.
- `immigration_annual.csv` — full long detail (67k rows: flows by sex/age/
  nationality or country of birth; stock by sex 1980–2023; stock by
  NUTS-2024 and nationality 2021–2023)
- Caveat for any graphic: the 2022–2024 surge in the legal resident stock is
  partly the extraordinary regularizations (declaratory regime /
  'manifestação de interesse', ended 2024), so stock and flow tell
  different stories. INE flow estimates (2008–2025) are the cleaner series.

### Wealth / inequality (INE, EU-SILC / Inquérito às Condições de Vida)
- `inequality_annual.csv` — income Gini and S80/S20 ratio of net monetary
  income, 2003–2024. 2024: Gini 30.9 (lowest of the series), S80/S20 4.9.
- **There is no official annual wealth-distribution series for Portugal.**
  Net-wealth distribution exists only in Banco de Portugal's HFCS survey
  (Inquérito à Situação Financeira dos Agregados Domésticos; waves 2013,
  2017, 2020), which must be downloaded manually from bportugal.pt and is
  not automated here. Any "wealth inequality" infographic must either use
  income inequality + an HFCS snapshot, or state the caveat explicitly.

### Real-estate investment funds (Banco de Portugal, BPstat domain 24)
- `funds_management_monthly.csv` — monthly stocks (EUR millions), 2000-12 to
  date: UP emitidas (VGM, the fund value under management), total assets, and
  asset composition (non-financial assets, i.e. physical real estate; equities;
  cash/deposits; other), plus the liability side (bank loans, other).
  Portfolio shares over total assets included. Aug 2026: VGM 21,673 M EUR.
- Source: BPstat API `https://bpstat.bportugal.pt/api/observations/?series_ids=<id>&lang=PT`
  (no auth, JSON, full history in one call; retry via `common.fetch_json`).
  Series ids and a 140-series index of domain-24 "fundos imobiliários" series
  in `data/raw/bpstat_domain24_series_index.md`.
- Caveat: BdP balance-sheet series do NOT split real-estate holdings between
  residential (habitação) and commercial. That split exists only in CMVM's
  "Indicadores mensais sobre fundos de investimento imobiliário" tables, which
  vanished from the public web with the cmvm.pt portal redesign
  (www.cmvm.pt/PInstitucional/PeriodicStatistics showed placeholder content as
  of late Oct 2026; the OutSystems single-page app cannot be rendered
  server-side or via Jina). Until CMVM restores the tables, automated
  housing-vs-commercial composition is not fetchable; the BdP series are the
  automated source. BdP and CMVM vehicle scopes (FII/FEII/FUNGEPI) differ, so
  never mix the two in one chart without stating the definition.

## Sources and licence
All INE indicators via the INE JSON API
(`json_indicador/pindica.jsp?op=2&varcd=<code>&Dim1=T&lang=PT`); descriptions
of every fetched indicator in `data/tidy/_indicators.json`.
INE data licence: CC BY 4.0 (reutilizável com atribuição).
Quadros de Pessoal indicators are MTSSS/GEP, carried by INE's API.
BdP/BPstat statistics: free reuse with attribution to Banco de Portugal.

Complementary non-INE sources for context (not fetched):
- Pordata: same INE data repackaged + per-m² from escrituras
- Banco de Portugal: housing statistics, HFCS; investment-fund balance sheets are fetched via BPstat in this repo
- Eurostat: ilc series for EU comparisons (ilc_di12 Gini, ilc_di11 S80/S20), prc_hpi_q

## Refresh
Re-run the four fetch scripts then `build_tidy.py`. Most recent INE values
can be provisional (flagged 'd'/'provisório' by INE); refetching picks up
revisions. The API is flaky (503/timeouts) — fetch scripts retry with backoff;
allow ~5–10 min for a full refresh.