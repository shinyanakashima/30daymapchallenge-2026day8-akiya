"""Compute, for each prefecture and scenario, the census year whose population
the prefecture would return to if people moved into its vacant dwellings
"with no specific use" (akiya).

Inputs : data/raw/*.xlsx (see scripts/fetch_data.py)
Outputs: data/inputs.csv   - cleaned inputs per prefecture
         data/results.csv  - new population and return year per scenario
         data/national.csv - the same for Japan as a whole

Usage:
    python scripts/compute.py
"""
import html
import pathlib
import re
import zipfile

import openpyxl
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data"

CENSUS_YEARS = [y for y in range(1920, 2021, 5) if y != 1945]
SOURCE_REGIONS_C = [11, 12, 13, 14, 23, 27]  # Saitama, Chiba, Tokyo, Kanagawa, Aichi, Osaka
TOKYO = 13

PREF_EN = [
    "Hokkaido", "Aomori", "Iwate", "Miyagi", "Akita", "Yamagata", "Fukushima",
    "Ibaraki", "Tochigi", "Gunma", "Saitama", "Chiba", "Tokyo", "Kanagawa",
    "Niigata", "Toyama", "Ishikawa", "Fukui", "Yamanashi", "Nagano", "Gifu",
    "Shizuoka", "Aichi", "Mie", "Shiga", "Kyoto", "Osaka", "Hyogo", "Nara",
    "Wakayama", "Tottori", "Shimane", "Okayama", "Hiroshima", "Yamaguchi",
    "Tokushima", "Kagawa", "Ehime", "Kochi", "Fukuoka", "Saga", "Nagasaki",
    "Kumamoto", "Oita", "Miyazaki", "Kagoshima", "Okinawa",
]


def pref_code(label):
    """'01000_北海道' -> (1, '北海道') for prefecture-level rows, else None."""
    m = re.match(r"^(\d{2})000_(.+)$", str(label or ""))
    if not m or m.group(1) == "00":
        return None
    return int(m.group(1)), m.group(2)


def num(v):
    if v is None:
        return None
    s = str(v).strip().replace(",", "")
    if s in ("", "-", "…", "x", "X"):
        return None
    return float(s)


def read_xlsx_rows(path):
    """Rows of the first sheet. Falls back to a minimal reader for workbooks
    saved in Strict Open XML, which openpyxl cannot open."""
    try:
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        if wb.worksheets:
            return [list(r) for r in wb.worksheets[0].iter_rows(values_only=True)]
    except Exception:
        pass
    z = zipfile.ZipFile(path)
    shared = [
        html.unescape("".join(re.findall(r"<t[^>]*>(.*?)</t>", si, re.S)))
        for si in re.findall(r"<si>(.*?)</si>", z.read("xl/sharedStrings.xml").decode(), re.S)
    ]
    sheet = z.read("xl/worksheets/sheet1.xml").decode()
    rows = []
    for r in re.findall(r"<row[^>]*>(.*?)</row>", sheet, re.S):
        cells = {}
        for col, attrs, inner in re.findall(
                r'<c r="([A-Z]+)\d+"([^>]*?)(?:/>|>(.*?)</c>)', r, re.S):
            v = re.search(r"<v>(.*?)</v>", inner or "")
            if v is None:
                continue
            val = shared[int(v.group(1))] if 't="s"' in attrs else v.group(1)
            idx = 0
            for ch in col:
                idx = idx * 26 + ord(ch) - 64
            cells[idx - 1] = val
        rows.append([cells.get(i) for i in range(max(cells) + 1)] if cells else [])
    return rows


def load_akiya():
    rows = read_xlsx_rows(RAW / "hlss2023_table1-1.xlsx")
    hdr = next(r for r in rows if r and any(str(c).startswith("221_") for c in r if c))
    col = next(i for i, c in enumerate(hdr) if c and str(c).startswith("221_"))
    out = {}
    for r in rows:
        if len(r) > 1 and r[0] == "a" and (p := pref_code(r[1])):
            out[p[0]] = num(r[col])
        if len(r) > 1 and r[1] == "00000_全国":
            out[0] = num(r[col])
    return out


def load_household_size_2020():
    rows = read_xlsx_rows(RAW / "census_timeseries_households_se0101.xlsx")
    year_row = next(r for r in rows if r and r[0] == "地域")
    start = next(i for i, c in enumerate(year_row) if c == "2020年")
    sub = rows[rows.index(year_row) + 2]
    # columns in the 2020 block: total hh, total persons, private hh,
    # private persons, persons per private household, ...
    col = next(i for i in range(start, len(sub)) if sub[i] and "１世帯当たり人員" in str(sub[i]))
    out, check = {}, {}
    for r in rows:
        if r and (p := pref_code(r[0])):
            out[p[0]] = num(r[col])
            check[p[0]] = num(r[col - 1]) / num(r[col - 2])
    for k in out:
        assert abs(out[k] - check[k]) < 1e-4, k
    return out


def load_population_2025():
    rows = read_xlsx_rows(RAW / "census2025_prelim_a01.xlsx")
    hdr = next(r for r in rows if r and "表章項目" in [str(c) for c in r])
    col = hdr.index("人口")
    out, names = {}, {}
    for r in rows:
        if len(r) > 2 and r[0] == "a" and (p := pref_code(r[2])):
            out[p[0]] = num(r[col])
            names[p[0]] = p[1]
        if len(r) > 2 and r[2] == "00000_全国":
            out[0] = num(r[col])
    return out, names


def load_population_series():
    rows = read_xlsx_rows(RAW / "census_timeseries_population_da01.xlsx")
    hdr = next(r for r in rows if r and r[0] == "地域")
    cols = {int(str(c)[:4]): i for i, c in enumerate(hdr)
            if c and re.match(r"^\d{4}年$", str(c))}
    out = {}
    for r in rows:
        if not r or not r[0]:
            continue
        key = 0 if r[0] == "00000_全国" else (pref_code(r[0]) or (None,))[0]
        if key is None:
            continue
        out[key] = {y: num(r[cols[y]]) for y in sorted(cols)}
    return out


def return_year(new_pop, now_pop, series):
    """Census year the population returns to.

    Gaining population: the latest census year whose population was at least
    the new population ("New record" if none).
    Losing population: the latest census year whose population was at most
    the new population ("Record low" if none).
    Years without data (1945 everywhere, and any blank) are skipped.
    """
    if new_pop == now_pop:
        return "No change"
    years = [y for y in CENSUS_YEARS if series.get(y) is not None]
    if new_pop > now_pop:
        hit = [y for y in years if series[y] >= new_pop]
        return str(max(hit)) if hit else "New record"
    hit = [y for y in years if series[y] <= new_pop]
    return str(max(hit)) if hit else "Record low"


def main():
    akiya = load_akiya()
    hh = load_household_size_2020()
    pop25, names = load_population_2025()
    series = load_population_series()

    prefs = list(range(1, 48))
    assert all(p in akiya and p in hh and p in pop25 and p in series for p in prefs)

    df = pd.DataFrame({
        "code": prefs,
        "pref_en": PREF_EN,
        "pref_ja": [names[p] for p in prefs],
        "akiya_2023": [akiya[p] for p in prefs],
        "persons_per_household_2020": [hh[p] for p in prefs],
        "pop_2025": [pop25[p] for p in prefs],
    })
    df["akiya_2023"] = df["akiya_2023"].astype(int)
    df["pop_2025"] = df["pop_2025"].astype(int)
    df["movers"] = (df["akiya_2023"] * df["persons_per_household_2020"]).round().astype(int)
    for y in CENSUS_YEARS:
        df[f"pop_{y}"] = pd.array([series[p][y] for p in prefs], dtype="Int64")

    assert abs(df["akiya_2023"].sum() - akiya[0]) < 1000, "prefecture sum vs national akiya"
    assert abs(df["pop_2025"].sum() - pop25[0]) < 1, "prefecture sum vs national population"

    add = df.set_index("code")["movers"]
    now = df.set_index("code")["pop_2025"]

    # Scenario A: from abroad
    newA = now + add
    # Scenario B: from Tokyo
    newB = now + add
    newB[TOKYO] = now[TOKYO] - add.drop(TOKYO).sum()
    # Scenario C: from the six big-city prefectures, split by population share
    src = SOURCE_REGIONS_C
    newC = now + add
    outflow = add.drop(src).sum()
    # Allocate the outflow in whole persons (largest remainder), so that the
    # national total is unchanged exactly.
    exact = outflow * now[src] / now[src].sum()
    alloc = exact.astype(int)
    rest = int(outflow - alloc.sum())
    for p in (exact - alloc).sort_values(ascending=False).index[:rest]:
        alloc[p] += 1
    for p in src:
        newC[p] = now[p] - alloc[p]

    res = df[["code", "pref_en", "pref_ja", "akiya_2023",
              "persons_per_household_2020", "movers", "pop_2025"]].copy()
    for key, new in (("A", newA), ("B", newB), ("C", newC)):
        new = new.round().astype(int)
        res[f"pop_{key}"] = new.values
        res[f"year_{key}"] = [return_year(new[p], now[p], series[p]) for p in prefs]

    nat_now = int(pop25[0])
    nat = pd.DataFrame([
        {"scenario": "A", "pop_2025": nat_now, "new_pop": int(newA.round().sum()),
         "return_year": return_year(int(newA.round().sum()), nat_now, series[0])},
        {"scenario": "B", "pop_2025": nat_now, "new_pop": int(newB.round().sum()),
         "return_year": "No change"},
        {"scenario": "C", "pop_2025": nat_now, "new_pop": int(newC.round().sum()),
         "return_year": "No change"},
    ])
    nat["movers_total"] = int(add.sum())
    nat["national_peak"] = int(max(v for v in series[0].values() if v))
    nat["national_peak_year"] = max(series[0], key=lambda y: series[0][y] or 0)

    pd.DataFrame({"year": CENSUS_YEARS, "pop": [series[0][y] for y in CENSUS_YEARS]}).astype(
        {"pop": "Int64"}).to_csv(OUT / "national_series.csv", index=False)
    df.to_csv(OUT / "inputs.csv", index=False)
    res.to_csv(OUT / "results.csv", index=False)
    nat.to_csv(OUT / "national.csv", index=False)
    pd.set_option("display.width", 200)
    print(res[["pref_en", "movers", "pop_2025", "pop_A", "year_A",
               "pop_B", "year_B", "pop_C", "year_C"]].to_string(index=False))
    print(nat.to_string(index=False))


if __name__ == "__main__":
    main()
