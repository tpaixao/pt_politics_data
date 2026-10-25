"""Shared helpers for fetching INE indicator series.

All scripts here are stdlib-only (host Python has no pandas).
INE API: https://www.ine.pt/ine/json_indicador/pindica.jsp?op=2&varcd=<code>&Dim1=T&lang=PT
INE licence: CC BY 4.0 (reutilizável com atribuição).
"""

import json
import os
import re
import time
import urllib.request

UA = {'User-Agent': 'Mozilla/5.0 (pt-politics-data project)'}
HERE = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(HERE, 'data', 'raw')
TIDY_DIR = os.path.join(HERE, 'data', 'tidy')

QUARTER_RE = re.compile(r'^(\d).{0,3}Trimestre de (\d{4})$')
YEAR_RE = re.compile(r'^(?:Ano de )?(\d{4})$')


def fetch_json(url, timeout=60, retries=6):
    """INE API is intermittently 503/timeout; always fetch through this."""
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=UA)
            return json.loads(urllib.request.urlopen(req, timeout=timeout).read())
        except Exception as e:
            last = e
            time.sleep(4 * (attempt + 1))
    raise RuntimeError(f'failed after {retries} attempts: {last}')


def inel_url(var, dim1='T', extra=''):
    dims = f'&Dim1={dim1}' if dim1 else ''
    return (f'https://www.ine.pt/ine/json_indicador/pindica.jsp'
            f'?op=2&varcd={var}{dims}{extra}&lang=PT')


def fetch_series(var, dim1='T', extra=''):
    """Return {'varcd':..,'indicador':..,'dados':{period:[records]},'extracao':..}."""
    d = fetch_json(inel_url(var, dim1, extra))
    item = d[0]
    return {'varcd': var,
            'indicador': item['IndicadorDsg'],
            'extracao': item.get('DataExtracao'),
            'dados': item['Dados']}


def fetch_topic(codes, subdir_prefix='ine'):
    """codes: {varcd: short comment}. Saves data/raw/ine_{code}.json each."""
    os.makedirs(RAW_DIR, exist_ok=True)
    out = {}
    for var, comment in codes.items():
        try:
            print(f'fetch {var} ({comment}) ...', end=' ', flush=True)
            s = fetch_series(var)
            path = os.path.join(RAW_DIR, f'{subdir_prefix}_{var}.json')
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(s, f, ensure_ascii=False, indent=1)
            n = len(s['dados'])
            out[var] = {'indicador': s['indicador'], 'n': len(s['dados'])}
            print(f'ok {n} periods')
        except Exception as e:
            print('FAILED:', e)
            out[var] = {'indicador': comment, 'error': str(e)}
    return out


def load_series(var, subdir_prefix='ine'):
    with open(os.path.join(RAW_DIR, f'{subdir_prefix}_{var}.json'), encoding='utf-8') as f:
        return json.load(f)


# ---- period parsing -------------------------------------------------------

def norm_quarter(p):
    m = QUARTER_RE.match(p.replace('\xBA', 'o'))
    if not m:
        raise ValueError(f'unparsed quarter: {p!r}')
    return f'{m.group(2)}Q{m.group(1)}'


def norm_year(p):
    p2 = p.replace('\xBA', 'o').strip()
    m = YEAR_RE.match(p2)
    if m:
        return m.group(1)
    m = re.match(r'^(\d{4})', p2)
    if m:
        return m.group(1)
    raise ValueError(f'unparsed year: {p!r}')


def num(v):
    """INE 'valor' -> float or '' (missing/flagged)."""
    if v in (None, '', 'F', 'N', False):
        return ''
    try:
        return float(v)
    except (TypeError, ValueError):
        return ''


def periods_of(series):
    """Yield (normalized 'YYYYQn' or 'YYYY', records) sorted."""
    dados = series['dados']
    is_quarterly = any('Trimestre' in k for k in dados)
    norm = norm_quarter if is_quarterly else norm_year
    return [(norm(p), dados[p]) for p in sorted(dados, key=norm)]


def pt_records(records):
    """Records where geographic dimension isnational Portugal."""
    r = []
    for rec in (records or []):
        if rec.get('geodsg') == 'Portugal' or rec.get('geocod') == 'PT':
            r.append(rec)
    return r