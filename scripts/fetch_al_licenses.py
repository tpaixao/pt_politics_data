"""Download the RNAL (Alojamento Local) open-data register.

Source: Turismo de Portugal open-data portal (ArcGIS Hub)
  https://dadosabertos.turismodeportugal.pt/datasets/4e62eb1977564991bd01e61d7aa8266f_6/explore
Backend feature service:
  https://geo.turismodeportugal.pt/server/rest/services/TDP/OpenData_AL/MapServer/6

Saves the CSV export to data/raw/rnal_al_registos.csv and a small
data/raw/rnal_snapshot.json with the download stamp and row count.

Run from the repo root:  python3 scripts/fetch_al_licenses.py
"""
import csv
import json
import os
import sys
import time
import urllib.request
import urllib.error

DATASET_ID = "4e62eb1977564991bd01e61d7aa8266f_6"
DOWNLOADS_URL = (
    "https://dadosabertos.turismodeportugal.pt/api/v3/datasets/"
    + DATASET_ID + "/downloads"
)
UA = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:131.0) "
                  "Gecko/20100101 Firefox/131.0"
}
RAW_PATH = os.path.join("data", "raw", "rnal_al_registos.csv")
SNAP_PATH = os.path.join("data", "raw", "rnal_snapshot.json")


def fetch_bytes(url, timeout=60):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def fetch_csv_url(retries=3, pause=5):
    """Resolve the Hub download link for the CSV export."""
    last = None
    for attempt in range(retries):
        try:
            data = json.loads(fetch_bytes(DOWNLOADS_URL))
        except (urllib.error.URLError, OSError) as exc:
            last = exc
            time.sleep(pause)
            continue
        for entry in data.get("data", []):
            if entry.get("attributes", {}).get("format") == "csv":
                stamp = entry["attributes"].get("lastModified", "")
                return entry["links"]["content"], stamp
        raise RuntimeError("csv download entry not found in Hub API")
    raise RuntimeError(f"cannot resolve downloads API: {last}")


def download(url, retries=3, pause=5):
    last = None
    for attempt in range(retries):
        try:
            return fetch_bytes(url, timeout=120)
        except (urllib.error.URLError, OSError) as exc:
            last = exc
            time.sleep(pause)
    raise RuntimeError(f"download failed after {retries} attempts: {last}")


def main():
    csv_url, stamp = fetch_csv_url()
    print("csv url:", csv_url)
    print("snapshot stamp:", stamp)
    blob = download(csv_url)
    os.makedirs(os.path.dirname(RAW_PATH), exist_ok=True)
    with open(RAW_PATH, "wb") as f:
        f.write(blob)
    text = blob.decode("utf-8-sig", "replace")
    rows = list(csv.DictReader(text.splitlines()))
    fields = list(rows[0].keys()) if rows else []
    snap = {
        "source": csv_url,
        "dataset_id": DATASET_ID,
        "last_modified": stamp,
        "downloaded_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "rows": len(rows),
        "fields": fields,
    }
    with open(SNAP_PATH, "w", encoding="utf-8") as f:
        json.dump(snap, f, ensure_ascii=False, indent=1)
    print("rows:", len(rows))
    print("fields:", fields)
    print("saved:", RAW_PATH)


if __name__ == "__main__":
    sys.exit(main())
