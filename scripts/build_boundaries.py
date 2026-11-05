"""Build simplified prefecture boundaries from MLIT National Land Numerical
Information, Administrative Areas (国土数値情報 行政区域データ N03, 2025-01-01).

The source archive (about 630 MB) is downloaded to a cache directory outside
the repository; only the simplified result is kept in data/geo/.

Usage:
    python scripts/build_boundaries.py [--cache DIR]
"""
import argparse
import pathlib
import urllib.request
import zipfile

import geopandas as gpd

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "geo" / "prefectures.geojson"
URL = "https://nlftp.mlit.go.jp/ksj/gml/data/N03/N03-2025/N03-20250101_GML.zip"
STEM = "N03-20250101_prefecture"

# Lambert conformal conic centred on Japan (metres), used for simplification
# and for drawing.
LCC = "+proj=lcc +lat_0=37 +lon_0=137 +lat_1=33 +lat_2=43 +datum=WGS84 +units=m +no_defs"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default=str(ROOT / ".cache"))
    args = ap.parse_args()
    cache = pathlib.Path(args.cache)
    cache.mkdir(parents=True, exist_ok=True)
    zpath = cache / URL.rsplit("/", 1)[1]
    if not zpath.exists():
        print("downloading", URL)
        urllib.request.urlretrieve(URL, zpath)
    shp = cache / f"{STEM}.shp"
    if not shp.exists():
        with zipfile.ZipFile(zpath) as z:
            for ext in ("shp", "shx", "dbf", "prj", "cpg"):
                z.extract(f"{STEM}.{ext}", cache)

    g = gpd.read_file(shp)
    g = g[g["N03_001"].notna()]
    g = g.to_crs(LCC)
    g = g.dissolve(by="N03_001", as_index=False)[["N03_001", "geometry"]]
    # Drop islets smaller than 2 km2 so the hatch patterns stay legible.
    g = g.explode(index_parts=False)
    g = g[g.geometry.area > 2e6]
    g["geometry"] = g.geometry.simplify(800, preserve_topology=True)
    g = g.dissolve(by="N03_001", as_index=False)
    g = g.rename(columns={"N03_001": "pref_ja"})
    g = g.to_crs(4326)
    g["geometry"] = g.geometry.set_precision(1e-4)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    g.to_file(OUT, driver="GeoJSON")
    print(OUT, len(g), "prefectures", f"{OUT.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
