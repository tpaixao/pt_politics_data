#!/usr/bin/env python3
"""Slice oversized INE raws down to PT-level records.

fetch_housing_dynamics.py stores the full INE API responses; for the
freguesia-level NUTS-2024 series (0013247 buildings, 0013248 dwellings) these
are 50-135 MB and exceed GitHub file limits (100 MB hard, 50 MB warn). The
downstream build only reads PT-level records, so this script replaces the raw
files with compact extracts carrying the same schema plus a _note field.

Run after (re)fetching those series and before committing:

    python3 scripts/slice_pt_raws.py

The full responses are regenerable via fetch_housing_dynamics.py; do not
recommit the unsliced blobs.
"""
import json
import os

RAW = 'data/raw'
OVERSIZED = ('0013247', '0013248')


def main():
    for var in OVERSIZED:
        path = os.path.join(RAW, f'ine_{var}.json')
        with open(path, encoding='utf-8') as f:
            d = json.load(f)
        if '_note' in d:
            print(var, 'already sliced, skipping')
            continue
        out = {
            'varcd': d['varcd'],
            'indicador': d['indicador'],
            'extracao': d.get('extracao'),
            '_note': ('Compact extract of the INE API response (PT-level records'
                      ' only); full NUTS-2024 territorial detail was dropped for'
                      ' repository size limits and is refetchable with'
                      ' fetch_housing_dynamics.py'),
            'dados': {},
        }
        n_rows = 0
        for period, recs in d['dados'].items():
            pt_recs = [r for r in recs if r.get('geocod') == 'PT']
            if pt_recs:
                out['dados'][period] = pt_recs
                n_rows += len(pt_recs)
        tmp = path + '.slice_tmp'
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(out, f, ensure_ascii=False, indent=1)
        os.replace(tmp, path)
        print(var, 'sliced:', len(out['dados']), 'periods,', n_rows, 'PT rows')


if __name__ == '__main__':
    main()
