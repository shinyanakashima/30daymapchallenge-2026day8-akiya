"""Write the data used by the interactive web page (docs/).

Outputs:
    docs/data/prefectures.geojson - prefecture outlines in the map projection
                                    (metres), Okinawa moved into the inset
    docs/data/akiya.json          - inputs and census series per prefecture

Usage:
    python scripts/build_web.py
"""
import json
import pathlib

import pandas as pd

from render import load, pt, FRAME

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "data"
YEARS = [y for y in range(1920, 2021, 5) if y != 1945]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    g, inset = load()
    g = g[["code", "geometry"]].copy()
    centers = {}
    for _, r in g.iterrows():
        geom = r.geometry
        main = max(geom.geoms, key=lambda x: x.area) if geom.geom_type == "MultiPolygon" else geom
        c = main.representative_point()
        centers[str(int(r["code"]))] = [round(c.x), round(c.y)]
    g["geometry"] = g.geometry.simplify(1200, preserve_topology=True)
    g["geometry"] = g.geometry.set_precision(100)
    (OUT / "prefectures.geojson").write_text(g.to_json(drop_id=True), encoding="utf-8")
    # coastline of Japan (with the Okinawa inset), drawn on every year layer
    coast = g.union_all().buffer(0).simplify(2500).boundary
    lines = list(coast.geoms) if hasattr(coast, "geoms") else [coast]
    lines = [[[round(x), round(y)] for x, y in ln.coords] for ln in lines if ln.length > 20000]
    (OUT / "coast.json").write_text(json.dumps(lines, separators=(",", ":")), encoding="utf-8")

    inp = pd.read_csv(ROOT / "data" / "inputs.csv")
    nat = pd.read_csv(ROOT / "data" / "national.csv").set_index("scenario")
    series_nat = pd.read_csv(ROOT / "data" / "national_series.csv")
    prefs = []
    for _, r in inp.iterrows():
        prefs.append({
            "code": int(r["code"]),
            "en": r["pref_en"],
            "ja": r["pref_ja"],
            "akiya": int(r["akiya_2023"]),
            "pph": float(r["persons_per_household_2020"]),
            "movers": int(r["movers"]),
            "pop2025": int(r["pop_2025"]),
            "series": {str(y): (None if pd.isna(r[f"pop_{y}"]) else int(r[f"pop_{y}"]))
                       for y in YEARS},
        })
    data = {
        "years": YEARS,
        "sources_c": [11, 12, 13, 14, 23, 27],
        "tokyo": 13,
        "inset": [round(v) for v in inset],
        "frame": list(FRAME),
        "centers": centers,
        # label anchors (map metres) for a few prefectures
        "anchors": {str(c): [round(v) for v in pt(*ll)] for c, ll in {
            1: (142.6, 43.5), 5: (140.3, 39.7), 13: (139.45, 35.72),
            27: (135.55, 34.65), 46: (130.6, 31.6)}.items()},
        "national": {
            "pop2025": int(nat.loc["A", "pop_2025"]),
            "series": {str(int(r["year"])): int(r["pop"]) for _, r in series_nat.iterrows()
                       if int(r["year"]) in YEARS},
        },
        "prefs": prefs,
    }
    (OUT / "akiya.json").write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")),
                                    encoding="utf-8")
    for p in OUT.iterdir():
        print(p, f"{p.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
