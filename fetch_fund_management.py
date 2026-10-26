"""Fetch BdP/BPstat real-estate investment fund (FII) series and build tidy CSVs.

Source: BPstat API (https://bpstat.bportugal.pt/api), BdP domain 24
"Balanço dos fundos de investimento" (Investment fund balance sheets).
Replacement for the CMVM monthly-indicator tables, which moved behind a
client-rendered portal redesign (as of 2026-10-26 only placeholders there).

BPstat data licence: free reuse with attribution to Banco de Portugal.

Monthly stock series (M€), domain 24:
  12520315  UP emitidas por fundos imobiliários - total - stock   (VGM)
  12520355  Ativo total dos fundos imobiliários
  12520313  Ativos não financeiros (largely physical real estate)
  12520362  Ações e outras participações
  12520261  Numerário e depósitos
  12520257  Outros ativos
  12520341  Empréstimos concedidos (liability)
  12520342  Outros passivos
  12520354  Passivo total
"""

import csv
import json
import os

from common import RAW_DIR, TIDY_DIR, fetch_json  # reuse retry UA helpers

BASE = "https://bpstat.bportugal.pt/api"

SERIES = {
    "12520315": ("vgm_meur", "UP emitidas (valor global mobiliário)"),
    "12520355": ("assets_total_meur", "Ativo total"),
    "12520313": ("nonfinancial_assets_meur", "Ativos nao financeiros"),
    "12520362": ("equities_meur", "Ações e outras participações"),
    "12520261": ("cash_deposits_meur", "Numerário e depósitos"),
    "12520257": ("other_assets_meur", "Outros ativos"),
    "12520341": ("loans_meur", "Empréstimos concedidos"),
    "12520342": ("other_liabilities_meur", "Outros passivos"),
    "12520354": ("liabilities_total_meur", "Passivo total"),
}


def fetch_series(sid):
    url = f"{BASE}/observations/?series_ids={sid}&lang=PT"
    try:
        d = fetch_json(url)
        obs = d.get("data", [])
    except Exception as e:
        print(f"  FAILED: {e}")
        return []
    # audit copy
    out = os.path.join(RAW_DIR, f"bpstat_fii_{sid}.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False)
    print(f"  ok {len(obs)} obs -> {os.path.basename(out)}")
    return obs


def observations_by_month(obs):
    """Series observations (monthly stock) -> {YYYY-MM: float}."""
    m = {}
    for o in obs:
        rd = o["reference_date"][:7]
        v = o.get("value")
        if v in (None, ""):
            continue
    for o in obs:
        rd = o["reference_date"][:7]
        v = o.get("value")
        if v in (None, ""):
            continue
        f = float(v)
        pub = str(o.get("pub_date") or "")
        cur = m.get(rd)
        if cur is None or pub > cur[0]:
            m[rd] = (pub, f)
    # keep the latest published revision per reference date
    return {rd: v for rd, (pub, v) in m.items()}


def main():
    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(TIDY_DIR, exist_ok=True)

    data = {}
    for sid, (col, label) in SERIES.items():
        print(f"fetch {sid} ({label}) ...", flush=True)
        obs = fetch_series(sid)
        data[col] = observations_by_month(obs)

    months = sorted(set().union(*[set(m) for m in data.values()]))
    rows = []
    for mo in months:
        row = {"month": mo}
        for col in data:
            row[col] = data[col].get(mo, "")
        # portfolio shares over total assets (when present)
        at = row.get("assets_total_meur")
        if at not in ("", None) and at:
            for src, out_col in [
                ("nonfinancial_assets_meur", "share_nonfinancial"),
                ("equities_meur", "share_equities"),
                ("cash_deposits_meur", "share_cash"),
                ("other_assets_meur", "share_other_assets"),
            ]:
                v = row.get(src)
                row[out_col] = round(v / at, 4) if v not in ("", None) else ""
        rows.append(row)

    cols = ["month", "vgm_meur", "assets_total_meur", "nonfinancial_assets_meur",
            "equities_meur", "cash_deposits_meur", "other_assets_meur",
            "loans_meur", "other_liabilities_meur", "liabilities_total_meur",
            "share_nonfinancial", "share_equities", "share_cash",
            "share_other_assets"]
    path = os.path.join(TIDY_DIR, "funds_management_monthly.csv")
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print(f"funds_management_monthly.csv: {len(rows)} rows ({months[0]}..{months[-1]})")
    last = rows[-1]
    print("last row:", json.dumps(last, ensure_ascii=False))


if __name__ == "__main__":
    main()