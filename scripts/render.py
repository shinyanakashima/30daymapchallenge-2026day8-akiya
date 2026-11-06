"""Render the map images (English and Japanese) from data/results.csv.

Usage:
    python scripts/render.py
Outputs:
    output/day8-akiya-en.png, output/day8-akiya-ja.png  (1080 x 1350)
"""
import pathlib

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.font_manager import FontProperties  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402
import pandas as pd  # noqa: E402
from shapely.geometry import box  # noqa: E402

from fonts import ensure_fonts  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output"
LCC = "+proj=lcc +lat_0=37 +lon_0=137 +lat_1=33 +lat_2=43 +datum=WGS84 +units=m +no_defs"

PAPER = "#f4f1ea"
INK = "#000000"
DPI = 200  # 1080 x 1350 px at 5.4 x 6.75 in

FONTS = ensure_fonts()


def fp(name, size):
    return FontProperties(fname=str(FONTS[name]), size=size)


# ---------------------------------------------------------------- classes
CLASSES = [  # key, hatch, facecolor
    ("new", None, INK),
    ("lt1980", "x" * 13, PAPER),
    ("1980", "x" * 8, PAPER),
    ("2005", "\\" * 12, PAPER),
    ("2015", "/" * 7, PAPER),
]


def classify(v):
    if v in ("New record", "Record low"):
        return "new" if v == "New record" else "lt1980"
    y = int(v)
    if y >= 2015:
        return "2015"
    if y >= 2005:
        return "2005"
    if y >= 1980:
        return "1980"
    return "lt1980"


# ---------------------------------------------------------------- text
TEXT = {
    "en": {
        "title": "If people moved into Japan’s akiya,\nwhat year would each place go back to?",
        "subtitle": "空き家に移住したら、あの頃に戻れるか？",
        "A": "A  From abroad",
        "B": "B  From Tokyo",
        "C": "C  From the big cities",
        "Csub": "Tokyo, Kanagawa, Saitama, Chiba, Aichi, Osaka",
        "Bsub": "Tokyo’s own akiya not counted",
        "Asub": "Everyone added to today’s population",
        "natA": "Japan: {nat_en}\nmillion people,\na new record",
        "natA2": "above the {peak_year} census peak of {peak_en} million",
        "natB": "Japan: no change",
        "natC": "Japan: no change",
        "legend_title": "Population returns to the level of",
        "legend": {"2015": "2015–2020", "2005": "2005–2010", "1980": "1980–2000",
                   "lt1980": "Before 1980", "new": "New record"},
        "send": "In B and C the prefectures people leave shrink. For them the year is the latest census with no more people than after the move.",
        "okinawa": "Okinawa (inset)",
        "record": "record",
        "notes_h": "Assumptions",
        "notes": [
            "Akiya here are vacant dwellings with no specific use (2023). Dwellings held for rent or "
            "sale and second homes are not included.",
            "Some of these homes need repairs before anyone can live in them. The numbers assume "
            "all of them are lived in; they are not a forecast.",
            "People per home is each prefecture's average household size in the 2020 census.",
            "The year is the last census year (every five years, 1920–2020; 1945 not used) in "
            "which the prefecture had at least the new population. Years in between are not estimated.",
            "In B and C the population of Japan as a whole does not change. In C the people leaving "
            "are split among the six prefectures by population.",
            "Okinawa is shown in an inset box, not in its true position. The Ogasawara Islands "
            "(Tokyo) are not shown.",
        ],
        "src_h": "Sources",
        "src": "Statistics Bureau of Japan (via e-Stat): 2023 Housing and Land Survey; Population "
               "Census 2025 preliminary counts; Population Census time series 1920–2020 "
               "(population; households 2020). Boundaries: MLIT National Land Numerical Information, "
               "Administrative Areas (2025).",
        "credit": "#30DayMapChallenge 2026 · Day 8: Utopia",
        "font_title": "SourceSerif4-Display-Semibold",
        "font_body": "SourceSerif4-Text-Regular",
        "font_bold": "SourceSerif4-Text-Semibold",
        "font_ital": "SourceSerif4-Text-Italic",
        "font_big": "SourceSerif4-Display-Italic",
    },
    "ja": {
        "title": "空き家に移住したら、\nあの頃に戻れるか？",
        "subtitle": "If people moved into Japan’s akiya, what year would each place go back to?",
        "A": "A  海外から",
        "B": "B  東京から",
        "C": "C  大都市から",
        "Csub": "東京・神奈川・埼玉・\n千葉・愛知・大阪",
        "Bsub": "東京都内の空き家は\n数えない",
        "Asub": "今の人口にそのまま上乗せ",
        "natA": "日本全体：\n{nat_ja}、\n過去最多",
        "natA2": "{peak_year}年の国勢調査\n（{peak_ja}）を上回る",
        "natB": "日本全体：\n変わらない",
        "natC": "日本全体：\n変わらない",
        "legend_title": "人口が戻る年",
        "legend": {"2015": "2015–2020年", "2005": "2005–2010年",
                   "1980": "1980–2000年", "lt1980": "1980年より前",
                   "new": "過去最多を更新"},
        "send": "BとCで人が出ていく都府県は人口が減る。その場合は、移動後の人口以下だった最も新しい国勢調査の年を示す。",
        "okinawa": "沖縄県（位置をずらして表示）",
        "record": "過去最多",
        "notes_h": "計算の前提",
        "notes": [
            "対象は2023年の「使用目的のない空き家」"
            "（賃貸・売却用及び二次的住宅を除く空き家）。"
            "賃貸用・売却用・別荘などは含まない。",
            "空き家には、修理しないと住めない家も含まれる。"
            "すべてに人が住んだと仮定して計算したもので、"
            "将来の予測ではない。",
            "1戸に住む人数は、2020年国勢調査の都道府県"
            "別「一般世帯の1世帯当たり人員」を使った。",
            "戻る年は、移動後の人口以上だった最後の"
            "国勢調査の年とした（1920〜2020年、5年ごと。1945年は"
            "使わない）。間の年は推計しない。",
            "BとCでは日本全体の人口は変わらない。"
            "Cの転出者は6都府県の人口の割合で分けた。",
            "沖縄県は別枠で、実際の位置とは違う場所に"
            "表示している。小笠原諸島（東京都）は表示していない。",
        ],
        "src_h": "出典",
        "src": "総務省統計局（e-Stat）：令和5年住宅・土地"
               "統計調査、令和7年国勢調査 人口速報集計、"
               "国勢調査 時系列データ（1920〜2020年の人口、2020"
               "年の世帯）。境界：国土交通省 国土数値情報"
               "（行政区域データ 2025年）。",
        "credit": "#30DayMapChallenge 2026 · Day 8: Utopia",
        "font_title": "NotoSerifJP-SemiBold",
        "font_body": "NotoSerifJP-Regular",
        "font_bold": "NotoSerifJP-SemiBold",
        "font_ital": "NotoSerifJP-Regular",
        "font_big": "NotoSerifJP-SemiBold",
    },
}

NAME_JA = {"Hokkaido": "北海道", "Akita": "秋田", "Tokyo": "東京",
           "Osaka": "大阪", "Kagoshima": "鹿児島", "Aichi": "愛知",
           "Shimane": "島根", "Okinawa": "沖縄", "Kanagawa": "神奈川"}

# Labels per map: prefecture, anchor (lon, lat), text offset in pixels
# (dx right, dy up), horizontal alignment.
LABELS = {
    "A": [("Hokkaido", (142.6, 43.5), (-150, 30), "right"),
          ("Akita", (140.3, 39.7), (-95, 10), "right"),
          ("Tokyo", (139.45, 35.72), (85, 22), "left"),
          ("Osaka", (135.55, 34.65), (-80, 62), "right"),
          ("Kagoshima", (130.6, 31.6), (-40, -38), "right"),
          ("Okinawa", None, (0, 0), "left")],
    "B": [("Hokkaido", (142.6, 43.5), (-62, -6), "right"),
          ("Akita", (140.3, 39.7), (-48, 6), "right"),
          ("Tokyo", (139.45, 35.72), (42, -12), "left"),
          ("Osaka", (135.55, 34.65), (-40, 34), "right")],
    "C": [("Hokkaido", (142.6, 43.5), (-62, -6), "right"),
          ("Akita", (140.3, 39.7), (-48, 6), "right"),
          ("Tokyo", (139.45, 35.72), (42, -2), "left"),
          ("Aichi", (137.1, 35.1), (30, -46), "left"),
          ("Osaka", (135.55, 34.65), (-40, 34), "right")],
}


# Frame of the main map in LCC metres (Ogasawara Islands fall outside).
FRAME = (-880000, -1085000, 950000, 1020000)
INSET_LL = (132.2, 28.0)  # where the lower-left corner of the Okinawa inset goes
FIG_W, FIG_H = 1080, 1350


def fx(px):
    return px / FIG_W


def fy(px):
    """figure fraction from a y position given in pixels from the top"""
    return 1 - px / FIG_H


def rect(x, y, w, h):
    """axes rectangle from pixel box (top-left origin)"""
    return [fx(x), fy(y + h), w / FIG_W, h / FIG_H]


def pt(lon, lat):
    s = gpd.GeoSeries.from_xy([lon], [lat], crs=4326).to_crs(LCC)
    return s.x.iloc[0], s.y.iloc[0]


def text_width_px(s, prop):
    from matplotlib.textpath import TextPath
    tp = TextPath((0, 0), s, prop=prop)
    return tp.get_extents().width * DPI / 72


def wrap(s, prop, width_px, cjk=False):
    """Greedy line wrap by measured width. Explicit newlines are kept. In
    Japanese text, runs of Latin letters and digits are not split, and closing
    punctuation is not moved to the start of a line."""
    import re as _re
    out = []
    for para in s.split("\n"):
        tokens = _re.findall(r"[0-9A-Za-z,.\-\u2013]+|.", para) if cjk else para.split(" ")
        lines, cur = [], ""
        for tok in tokens:
            cand = (cur + tok) if cjk else (cur + " " + tok if cur else tok)
            if cur and text_width_px(cand, prop) > width_px:
                if cjk and tok in "\u3001\u3002\uff09\u300d\u30fb":
                    cur = cand
                    continue
                lines.append(cur)
                cur = tok
            else:
                cur = cand
        if cur:
            lines.append(cur)
        out.extend(lines)
    return out


def load():
    g = gpd.read_file(ROOT / "data" / "geo" / "prefectures.geojson")
    r = pd.read_csv(ROOT / "data" / "results.csv",
                    dtype={"year_A": str, "year_B": str, "year_C": str})
    g = g.merge(r, on="pref_ja", how="left")
    assert g["pref_en"].notna().all()
    g = g.to_crs(LCC)
    # Drop the Ogasawara Islands (south of the frame) from Tokyo's outline.
    tk = g["pref_en"] == "Tokyo"
    parts = gpd.GeoSeries([g.loc[tk, "geometry"].iloc[0]], crs=LCC).explode(index_parts=False)
    parts = parts[parts.bounds["maxy"] > -900000]
    g.loc[tk, "geometry"] = parts.union_all()
    # Move Okinawa into the inset position (same scale).
    oki = g["pref_en"] == "Okinawa"
    ox0, oy0, ox1, oy1 = g.loc[oki].total_bounds
    ix, iy = pt(*INSET_LL)
    from shapely.affinity import translate
    g.loc[oki, "geometry"] = g.loc[oki, "geometry"].apply(
        lambda geom: translate(geom, xoff=ix - ox0, yoff=iy - oy0))
    inset = (ix, iy, ix + (ox1 - ox0), iy + (oy1 - oy0))
    return g, inset


def draw_map(ax, g, key, inset, lw=1.0):
    ax.set_aspect("equal")
    ax.axis("off")
    gg = g.copy()
    gg["cls"] = gg[f"year_{key}"].map(classify)
    for cls, hatch, face in CLASSES:
        sub = gg[gg["cls"] == cls]
        if len(sub):
            sub.plot(ax=ax, facecolor=face, edgecolor=INK, hatch=hatch, linewidth=0)
    gg.boundary.plot(ax=ax, color=INK, linewidth=0.28 * lw)
    # Light lines on borders shared by two black prefectures keep them apart.
    blk = gg[gg["cls"] == "new"].reset_index(drop=True)
    shared = []
    for i, geom in enumerate(blk.geometry):
        others = blk.geometry.drop(i).union_all().buffer(600)
        shared.append(geom.boundary.intersection(others))
    if shared:
        gpd.GeoSeries(shared, crs=LCC).plot(ax=ax, color=PAPER, linewidth=0.5 * lw)
    x0, y0, x1, y1 = inset
    pad = 22000
    ax.add_patch(Rectangle((x0 - pad, y0 - pad), (x1 - x0) + 2 * pad, (y1 - y0) + 2 * pad,
                           fill=False, edgecolor=INK, linewidth=0.45))
    return gg


def fit(ax, box_px, center_px=None):
    """Set limits so that FRAME is drawn at the scale that fits the axes height,
    with the frame centred horizontally unless center_px is given."""
    x0, y0, x1, y1 = FRAME
    w_px, h_px = box_px
    scale = h_px / (y1 - y0)  # px per metre
    span = w_px / scale
    cx = (x0 + x1) / 2 if center_px is None else center_px
    ax.set_xlim(cx - span / 2, cx + span / 2)
    ax.set_ylim(y0, y1)
    return scale


def label(ax, gg, key, lang, size, inset):
    t = TEXT[lang]
    for name, ll, (dx, dy), ha in LABELS[key]:
        row = gg[gg["pref_en"] == name].iloc[0]
        v = row[f"year_{key}"]
        if lang == "en":
            txt = f"{name} {t['record'] if v == 'New record' else v}"
        else:
            txt = f"{NAME_JA[name]} {t['record'] if v == 'New record' else v + chr(0x5e74)}"
        prop = fp(t["font_body"], size)
        if ll is None:  # Okinawa: written inside the inset, no leader
            x0, y0, x1, y1 = inset
            ax.annotate(txt, xy=(x1, y1), xytext=(-4, -4), textcoords="offset pixels",
                        ha="right", va="top", fontproperties=prop)
            continue
        x, y = pt(*ll)
        ax.annotate(txt, xy=(x, y), xytext=(dx, dy), textcoords="offset pixels",
                    ha=ha, va="center", fontproperties=prop, color=INK,
                    bbox=dict(boxstyle="square,pad=0.12", facecolor=PAPER, edgecolor="none"),
                    arrowprops=dict(arrowstyle="-", color=INK, linewidth=0.45,
                                    shrinkA=0, shrinkB=0, relpos=(1, 0.5) if ha == "right" else (0, 0.5)))
        ax.plot([x], [y], marker="o", markersize=2.2, color=INK, markeredgecolor=PAPER,
                markeredgewidth=0.5, zorder=5)


def put_lines(fig, x, y, lines, prop, lh, **kw):
    """Draw lines of text from pixel (x, y) (top of the first line) with a
    fixed line pitch lh in pixels. Returns the y below the last line."""
    for i, line in enumerate(lines):
        fig.text(fx(x), fy(y + i * lh), line, fontproperties=prop, va="top", ha="left", **kw)
    return y + len(lines) * lh


def ja_people(n):
    oku, man = divmod(int(round(n / 1e4)), 10000)
    return f"{oku}億{man:,}万人"


def national_strings():
    nat = pd.read_csv(ROOT / "data" / "national.csv").set_index("scenario")
    a = nat.loc["A"]
    return {
        "nat_en": f"{a['new_pop'] / 1e6:.1f}",
        "peak_en": f"{a['national_peak'] / 1e6:.1f}",
        "peak_year": int(a["national_peak_year"]),
        "nat_ja": ja_people(a["new_pop"]),
        "peak_ja": ja_people(a["national_peak"]),
        "is_record": a["return_year"] == "New record",
        "year": a["return_year"],
    }


def legend(fig, x, y, lang):
    """Legend drawn from pixel position (x, y) = top-left."""
    t = TEXT[lang]
    fig.text(fx(x), fy(y), t["legend_title"], fontproperties=fp(t["font_bold"], 6.4),
             va="top", ha="left")
    sty = {k: (h, f) for k, h, f in CLASSES}
    sw, sh, step = 40, 20, 27
    yy = y + 28
    for k in ["2015", "2005", "1980", "lt1980", "new"]:
        h, f = sty[k]
        ax = fig.add_axes(rect(x, yy, sw, sh))
        ax.axis("off")
        ax.add_patch(Rectangle((0, 0), 1, 1, facecolor=f, edgecolor=INK, hatch=h,
                               linewidth=0.6, transform=ax.transAxes, clip_on=False))
        fig.text(fx(x + sw + 10), fy(yy + sh / 2), t["legend"][k],
                 fontproperties=fp(t["font_body"], 6.2), va="center", ha="left")
        yy += step
    yy += 6
    prop = fp(t["font_body"], 5.2)
    lines = wrap(t["send"], prop, FIG_W - 44 - x, cjk=(lang == "ja"))
    put_lines(fig, x, yy, lines, prop, 16)


def render(lang):
    t = dict(TEXT[lang])
    ns = national_strings()
    assert ns["is_record"], "heading text assumes scenario A sets a national record"
    for k in ("natA", "natA2"):
        t[k] = t[k].format(**ns)
    cjk = lang == "ja"
    g, inset = load()
    plt.rcParams["hatch.linewidth"] = 0.42
    fig = plt.figure(figsize=(FIG_W / DPI, FIG_H / DPI), dpi=DPI, facecolor=PAPER)
    M = 44  # side margin, px

    # ------------------------------------------------ heading
    tprop = fp(t["font_title"], 15.5 if lang == "en" else 17)
    put_lines(fig, M, 34, t["title"].split("\n"), tprop, 52 if lang == "en" else 56)
    fig.text(fx(M), fy(146), t["subtitle"],
             fontproperties=fp("NotoSerifJP-Regular" if lang == "en" else "SourceSerif4-Text-Italic",
                               7.4), va="top", ha="left")
    for yy, lw in ((182, 0.9), (186, 0.3)):
        fig.add_artist(plt.Line2D([fx(M), fx(FIG_W - M)], [fy(yy), fy(yy)], color=INK, linewidth=lw))

    # ------------------------------------------------ map A
    top, h = 196, 590
    axA = fig.add_axes(rect(M, top, FIG_W - 2 * M, h))
    fit(axA, (FIG_W - 2 * M, h), center_px=FRAME[0] + (FRAME[2] - FRAME[0]) / 2 - 40000)
    ggA = draw_map(axA, g, "A", inset, 1.0)
    label(axA, ggA, "A", lang, 6.2, inset)

    # left column: scenario heading and national value
    fig.text(fx(M), fy(top + 10), t["A"], fontproperties=fp(t["font_bold"], 10.5), va="top")
    fig.text(fx(M), fy(top + 44), t["Asub"], fontproperties=fp(t["font_ital"], 6.2), va="top")
    bigp = fp(t["font_big"], 12.5 if lang == "en" else 10.5)
    y = put_lines(fig, M, top + 78, wrap(t["natA"], bigp, 255, cjk), bigp,
                  40 if lang == "en" else 36)
    smallp = fp(t["font_body"], 5.8)
    put_lines(fig, M, y + 6, wrap(t["natA2"], smallp, 230, cjk), smallp, 18)
    legend(fig, 760, 548, lang)

    # ------------------------------------------------ maps B and C
    head_y, map_top, map_h = 800, 822, 282
    colw = (FIG_W - 2 * M - 30) / 2
    for i, key in enumerate(["B", "C"]):
        x = M + i * (colw + 30)
        fig.text(fx(x), fy(head_y), t[key], fontproperties=fp(t["font_bold"], 9.2), va="top")
        subp = fp(t["font_ital"], 5.6)
        y = put_lines(fig, x, head_y + 32, wrap(t[f"{key}sub"], subp, 170, cjk), subp, 17)
        natp = fp(t["font_big"], 8.6)
        put_lines(fig, x, y + 10, wrap(t[f"nat{key}"], natp, 170, cjk), natp, 28)
        ax = fig.add_axes(rect(x + 150, map_top, colw - 150, map_h))
        fit(ax, (colw - 150, map_h), center_px=FRAME[0] + (FRAME[2] - FRAME[0]) / 2 - 30000)
        gg = draw_map(ax, g, key, inset, 0.75)
        label(ax, gg, key, lang, 5.2, inset)

    # ------------------------------------------------ notes
    ry = 1112
    fig.add_artist(plt.Line2D([fx(M), fx(FIG_W - M)], [fy(ry), fy(ry)], color=INK, linewidth=0.3))
    fig.text(fx(M), fy(ry + 10), t["notes_h"], fontproperties=fp(t["font_bold"], 6), va="top")
    prop = fp(t["font_body"], 5.05 if lang == "en" else 4.8)
    lh = 16.5
    gap = 30
    cw = (FIG_W - 2 * M - gap) / 2
    notes = t["notes"]
    bottom = 0
    for c in range(2):
        yy = ry + 34
        x = M + c * (cw + gap)
        for n in notes[c * 3:(c + 1) * 3]:
            fig.text(fx(x), fy(yy), "–", fontproperties=prop, va="top")
            yy = put_lines(fig, x + 12, yy, wrap(n, prop, cw - 14, cjk), prop, lh) + 5
        bottom = max(bottom, yy)
    sy = bottom + 4
    fig.text(fx(M), fy(sy), t["src_h"], fontproperties=fp(t["font_bold"], 5.3), va="top")
    sx = M + (62 if lang == "en" else 40)
    put_lines(fig, sx, sy, wrap(t["src"], prop, FIG_W - M - sx, cjk), prop, lh)
    fig.text(fx(FIG_W - M), fy(FIG_H - 12), t["credit"],
             fontproperties=fp("SourceSerif4-Text-Italic", 5.0), va="bottom", ha="right")

    OUT.mkdir(exist_ok=True)
    out = OUT / f"day8-akiya-{lang}.png"
    fig.savefig(out, dpi=DPI, facecolor=PAPER)
    plt.close(fig)
    print(out)


if __name__ == "__main__":
    render("en")
    render("ja")
