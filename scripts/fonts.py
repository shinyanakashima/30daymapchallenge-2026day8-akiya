"""Fetch the fonts (SIL Open Font License) from the google/fonts repository and
create static instances that matplotlib can use.

Source Serif 4 (Adobe) and Noto Serif JP (Google / Adobe) are both OFL-1.1.
"""
import pathlib
import urllib.request

from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
CACHE = ROOT / ".cache" / "fonts"
BASE = "https://raw.githubusercontent.com/google/fonts/main/ofl/"
VARIABLE = {
    "SourceSerif4.ttf": BASE + "sourceserif4/SourceSerif4%5Bopsz,wght%5D.ttf",
    "SourceSerif4-Italic.ttf": BASE + "sourceserif4/SourceSerif4-Italic%5Bopsz,wght%5D.ttf",
    "NotoSerifJP.ttf": BASE + "notoserifjp/NotoSerifJP%5Bwght%5D.ttf",
}
# name -> (variable file, axis values)
INSTANCES = {
    "SourceSerif4-Text-Regular.ttf": ("SourceSerif4.ttf", {"wght": 400, "opsz": 12}),
    "SourceSerif4-Text-Semibold.ttf": ("SourceSerif4.ttf", {"wght": 600, "opsz": 12}),
    "SourceSerif4-Text-Italic.ttf": ("SourceSerif4-Italic.ttf", {"wght": 400, "opsz": 12}),
    "SourceSerif4-Display-Semibold.ttf": ("SourceSerif4.ttf", {"wght": 600, "opsz": 48}),
    "SourceSerif4-Display-Italic.ttf": ("SourceSerif4-Italic.ttf", {"wght": 400, "opsz": 36}),
    "NotoSerifJP-Regular.ttf": ("NotoSerifJP.ttf", {"wght": 400}),
    "NotoSerifJP-SemiBold.ttf": ("NotoSerifJP.ttf", {"wght": 600}),
}


def ensure_fonts():
    CACHE.mkdir(parents=True, exist_ok=True)
    for name, url in VARIABLE.items():
        p = CACHE / name
        if not p.exists():
            urllib.request.urlretrieve(url, p)
    paths = {}
    for name, (src, axes) in INSTANCES.items():
        p = CACHE / name
        if not p.exists():
            f = TTFont(CACHE / src)
            inst = instantiateVariableFont(f, axes, updateFontNames=False)
            # give each instance its own family name so matplotlib keeps them apart
            fam = name[:-4]
            for rec in inst["name"].names:
                if rec.nameID in (1, 4, 16, 6):
                    rec.string = fam if rec.nameID != 6 else fam.replace(" ", "")
                if rec.nameID in (2, 17):
                    rec.string = "Regular"
            inst.save(p)
        paths[name[:-4]] = p
    return paths


if __name__ == "__main__":
    for k, v in ensure_fonts().items():
        print(k, v)
