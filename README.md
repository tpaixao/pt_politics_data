# pt_politics_data

Official-source datasets behind a planned series of infographics about
current topics in Portuguese politics. One fetch script per topic, one
shared tidy builder. All stdlib-only Python 3.11+ (host has no pandas).

## Usage

```bash
python3 fetch_housing.py && python3 fetch_salaries.py      # ~2-4 min each, API retries built in
python3 fetch_immigration.py && python3 fetch_wealth.py
python3 fetch_housing_stock.py                             # Censos stock/tenure + Eurostat tenure
python3 build_tidy.py
python3 fetch_fund_management.py                           # BdP/BPstat real-estate funds (standalone)
```

## Topics

### Housing (INE)
- `housing_quarterly.csv` — 2009Q1–2026Q2: IPH YoY (total / Novos / Existentes),
  QoQ, index Base 2025=100, 12-month sales count (2022 Methodology, 2026 only so far)
- `housing_annual_medians.csv` — median selling price EUR/m² (2019–2025) and
  median rent of new contracts EUR/m² (2020–2025)

### Housing stock and tenure (INE Censos, Eurostat EU-SILC)
- `housing_census_occupation.csv` — classic family dwellings by occupation
  status, decennial 1950–2021. 2021: 4,142,581 habitual (69.4%), 1,104,881
  seasonal/secondary (18.5%), 696,194 vacant, total 5,970,677.
  Caveat: in the historical series the 2021 rows leave a 27,021-dwelling gap
  between Total and the sum of the parts (INE's own historical-series
  categorization); the Censos 2021 stock indicator (`housing_census_stock.csv`)
  puts vacant at 723,215 (348,097 for sale/rent + 375,118 other reasons).
  Prefer the Censos 2021 splits for 2021; use this series for the long view.
- `housing_census_tenure.csv` — habitually-occupied residences by tenure,
  Censos 2011 + 2021 in INE's comparable grouping: 2021 owner 2,900,093
  (70.0%), rented 922,810 (22.3%), other (cedido sem renda etc.) 319,678
  (7.7%). The 2011 row is INE's recategorized version (cooperative ownership
  counted under propriedade), not the original 2011 detail.
- `housing_census_tenure_2011.csv` — Censos 2011 regime-of-occupation detail
  (fixed-term vs indefinite lease, social rent, cooperative, etc.)
- `housing_census_stock.csv` — Censos 2021 stock, long form: total
  5,981,482 dwellings, of which classic family 5,970,677, non-classic
  4,042, collective 6,763; plus building-type and vacancy splits.
- `housing_eusilc_tenure.csv` — tenure status of the POPULATION (Eurostat
  ilc_lvho02, EU-SILC), 2004–2025, % of population: owner 71.2% in 2025
  (peak 78.3% in 2021), market-rent tenants 16.3% in 2025 vs 10.9% in 2021.
  Person-weighted survey shares — NOT comparable with the census dwelling
  counts above; cite one or the other, never mix.

### Housing vacancy estimate, 2025 (residual model, INE)
- `housing_completions.csv` — dwellings completed per year: the INE long
  series 0011724 (`fogos_concluidos`, 1969–2025) alongside 0013248
  (`fogos_concluidos_construcoes_novas_hab_familiar`, 2011–2025). The two
  INE sources disagree (2025: 19,971 vs 27,301; 2022: 19,379 vs 21,047):
  they come from different survey universes — "Inquérito aos projetos de
  obras de edificação e de demolição de edifícios" vs "Estatísticas das
  obras concluídas". The vacancy model uses the conservative long series
  0011724; the residual estimate is therefore slightly biased toward fewer
  new dwellings (lower vacancy) if 0013248 is the truer count.
- Raw-data note: `data/raw/ine_0013247.json` and `ine_0013248.json` are
  stored as PT-level extracts (same schema plus a `_note` field); the full
  NUTS-2024 responses behind them are 56–135 MB, beyond GitHub's file limits
  (50 MB warn, 100 MB hard). Rerunning `fetch_housing_dynamics.py`
  regenerates the full-size files — run `python3 scripts/slice_pt_raws.py`
  before any recommit.
- `housing_vacancy_decomposition.csv` + `housing_vacancy_scenarios.csv` —
  residual estimate of habitually vacant dwellings after Censos 2021
  (indicators: 0012499 baseline, 0011724 completions, 0013356 population
  estimates). Method: vacant stock evolves from the Censos 2021 baseline
  (723,215 vacant of 5,981,482 dwellings) adding completions and
  subtracting estimated household growth at constant average household
  size (Censos 2021 resident population 10,347,892 / 4,149,096
  households = 2.494 people per household). Because the revised
  31-Dec-2021 population estimate (10,599,117) is +251,225 above the
  census count, two anchor variants are published:
  `estimates` (households base scaled up with the revised population,
  internally consistent Dec-2021 → Dec-2025 change) and `census`
  (unscaled census households base; attributes the whole census→2025
  population change to 2022–2025 household growth and lands low). 2025
  results: census anchor 368,294; estimates anchor 469,025, central
  (estimates anchor, demolitions 2,000/yr) 461,025; scenario band low
  290,529 – high 494,259 (`housing_vacancy_scenarios.csv`).
- Assumptions: (1) no annual household-count series exists in the INE
  API (every Agregados domésticos indicator is Decenal), so household
  size is constant per census, with 2.40–2.70 sensitivity; (2) the INE
  API has no demolition series — monthly licensed-works indicators
  (e.g. 0012096/0012097) report only "Construções novas" / "Outras
  obras" / a total that includes demolition with no split — so
  demolitions enter as an assumed 0–4,000/yr constant; (3) secondary/
  seasonal dwellings (1,104,881 in 2021) are held constant except in
  the low scenario (+1%/yr); (4) the model cannot distinguish where new
  households settle or that some of the +825k population 2022–2025
  (immigration-driven) live in collective or non-private arrangements,
  which would reduce the needed dwelling stock and make the vacancy
  estimate an upper bound on that margin. Census-to-census vacancy fell
  543,777 (2001) → 735,128 (2011) → 723,215 (2021); this model puts the
  2025 vacancy near 460–470k (7.7–7.8% of ~6.06M dwellings), i.e. a drop
  of roughly a quarter of a million dwellings in four years, mostly
  absorbed by immigrant household formation against only ~77k
  completions. (An earlier rough "700–800k" band assumed smaller
  household growth from a census-vintage population; it is superseded
  by the live-data decomposition above.)

### Salaries (INE / MTSSS-GEP Quadros de Pessoal)
- `salaries_annual.csv` — average monthly base remuneration EUR, Portugal,
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
- Eurostat: ilc series for EU comparisons (ilc_di12 Gini, ilc_di11 S80/S20), prc_hpi_q;
  ilc_lvho02 (tenure of population) is fetched (`fetch_housing_stock.py`)

## Refresh
Re-run the five fetch scripts then `build_tidy.py`. Most recent INE values
can be provisional (flagged 'd'/'provisório' by INE); refetching picks up
revisions. The API is flaky (503/timeouts) — fetch scripts retry with backoff;
allow ~5–10 min for a full refresh.