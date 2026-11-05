"""Download the official statistical tables used by this map.

All tables come from e-Stat (Portal Site of Official Statistics of Japan).
The files are saved under data/raw/ and a record of each download
(URL, file name, retrieval date) is written to data/raw/sources.json.

Usage:
    python scripts/fetch_data.py
"""
import datetime
import json
import pathlib
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"

ESTAT = "https://www.e-stat.go.jp/stat-search/file-download?statInfId={}&fileKind=0"

SOURCES = [
    {
        "key": "akiya_2023",
        "file": "hlss2023_table1-1.xlsx",
        "statInfId": "000040209841",
        "survey": "2023 Housing and Land Survey (令和5年住宅・土地統計調査), "
                  "Basic tabulation on dwellings and households",
        "table": "Table 1-1: Dwellings by occupancy status (9 categories) "
                 "- Japan, prefectures, 21 major cities",
        "used": "Vacant dwellings excluding those for rent, for sale and "
                "secondary dwellings (賃貸・売却用及び二次的住宅を除く空き家)",
        "page": "https://www.e-stat.go.jp/stat-search/files?toukei=00200522&tstat=000001207800",
    },
    {
        "key": "household_size_2020",
        "file": "census_timeseries_households_se0101.xlsx",
        "statInfId": "000001086170",
        "survey": "Population Census time series data (国勢調査 時系列データ)",
        "table": "Households, Table 1 (part 1): private households and "
                 "institutional households, Japan and prefectures (1960, 1970-2020)",
        "used": "2020 members per private household (一般世帯の1世帯当たり人員)",
        "page": "https://www.e-stat.go.jp/stat-search/files?toukei=00200521&tstat=000001011777",
    },
    {
        "key": "population_2025",
        "file": "census2025_prelim_a01.xlsx",
        "statInfId": "000040454825",
        "survey": "2025 Population Census, preliminary counts (令和7年国勢調査 人口速報集計)",
        "table": "Table 1: Population by sex, number of households - Japan, "
                 "prefectures, municipalities",
        "used": "2025 total population by prefecture",
        "page": "https://www.e-stat.go.jp/stat-search/files?toukei=00200521&tstat=000001230925",
    },
    {
        "key": "population_1920_2020",
        "file": "census_timeseries_population_da01.xlsx",
        "statInfId": "000001085925",
        "survey": "Population Census time series data (国勢調査 時系列データ)",
        "table": "Sex, age and marital status, Table 1: Population by sex - "
                 "Japan and prefectures (1920-2020)",
        "used": "Total population by prefecture, every census 1920-2020",
        "page": "https://www.e-stat.go.jp/stat-search/files?toukei=00200521&tstat=000001011777",
    },
]


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    today = datetime.date.today().isoformat()
    records = []
    for s in SOURCES:
        url = ESTAT.format(s["statInfId"])
        req = urllib.request.Request(url, headers={"User-Agent": "akiya-map/1.0"})
        with urllib.request.urlopen(req, timeout=120) as r:
            data = r.read()
        (RAW / s["file"]).write_bytes(data)
        records.append({**s, "url": url, "retrieved": today, "bytes": len(data)})
        print(f"{s['file']}: {len(data):,} bytes")
    (RAW / "sources.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
