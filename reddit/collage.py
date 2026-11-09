"""Reddit collage (r/dataisbeautiful style), light parchment: the two maps of sea sunsets and sea sunrises, four beach roses and
the Firth of Clyde. Builds on the blog figures from code/06_figures.py. Output: reddit/sea_sunsets_collage.png (2700 x 3900)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "code"))
from figstyle import *
from PIL import Image

R = jload(f"{DATA}/results.json")
B = os.path.join(ROOT, "release", "blog")
fig = plt.figure(figsize=(9, 13), dpi=300); parchment(fig, seed=4, alpha=0.05)
fig.text(0.05, 0.975, "Where the sun sets into the sea", fontproperties=HAND, fontsize=32, color=RED, va="center")
fig.text(0.05, 0.950, f"{R['n']['coast']:,} named beaches in Britain and Ireland: on how many days of the year does the Sun set into (or rise out of)",
         fontproperties=FELL, fontsize=11, color=INKC, va="center")
fig.text(0.05, 0.936, f"open sea? {R['set']['any_pc']:.0f}% get a sea sunset on some day, {R['rise']['any_pc']:.0f}% a sea sunrise; only {R['set']['all_year']} get a sea sunset every day.",
         fontproperties=FELL, fontsize=11, color=INKC, va="center")


def panel(fn, box, crop=None):
    im = Image.open(f"{B}/{fn}").convert("RGB")
    if crop:
        w, h = im.size; im = im.crop((int(crop[0] * w), int(crop[1] * h), int(crop[2] * w), int(crop[3] * h)))
    ax = fig.add_axes(box); ax.imshow(im); ax.axis("off")
    return im.size


w, h = Image.open(f"{B}/b_maps.png").size
hh = 0.98 * 9 * (h * 0.89 / w) / 13
panel("b_maps.png", [0.01, 0.925 - hh, 0.98, hh], crop=(0, 0.11, 1, 1))
w, h = Image.open(f"{B}/b_roses.png").size
hr = 0.98 * 9 * (h * 0.8 / w) / 13
y1 = 0.925 - hh - 0.01 - hr
panel("b_roses.png", [0.01, y1, 0.98, hr], crop=(0, 0.2, 1, 1))
fig.text(0.05, y1 + hr + 0.002, "A year of sunset (left) and sunrise (right) bearings at four beaches: gold or blue over open sea, grey behind land",
         fontproperties=FELLSC, fontsize=10, color=RED, va="bottom")
C = R["cases"]
fig.text(0.05, y1 - 0.025, f"Winter is better: {R['rise']['dec21']} beaches see a sea sunrise on 21 December, {R['rise']['jun21']} on 21 June. Islands take a bite: Arran hides",
         fontproperties=FELL, fontsize=10.5, color=INKC, va="center")
fig.text(0.05, y1 - 0.040, f"{C['troon']['set_islands']['Isle of Arran']} sunsets a year from Troon, Lundy {C['woolacombe_sands']['set_islands']['Lundy']} from Woolacombe. Land farther than about 50 km hides below the curve of the sea.",
         fontproperties=FELL, fontsize=10.5, color=INKC, va="center")
ax = fig.add_axes([0.02, 0.035, 0.40, 0.215]); ax.imshow(Image.open(f"{B}/b_clyde.png").convert("RGB").crop((0, 175, 1800, 1590))); ax.axis("off")
fig.text(0.05, 0.247, "The Firth of Clyde, 20 March: sunset lines end on Arran", fontproperties=FELLSC, fontsize=9.5, color=RED, va="bottom")
im = Image.open(f"{B}/b_islands.png").convert("RGB"); w, h = im.size; im = im.crop((0, int(0.11 * h), w, h))
ax = fig.add_axes([0.43, 0.05, 0.55, 0.55 * 9 * (im.size[1] / im.size[0]) / 13]); ax.imshow(im); ax.axis("off")
fig.text(0.45, 0.247, "Islands that hide the Sun from the most beaches", fontproperties=FELLSC, fontsize=9.5, color=RED, va="bottom")
fig.text(0.05, 0.02, "Data: OpenStreetMap contributors (ODbL) via QLever and OpenFreeMap; AWS Terrain Tiles. Eye 3 m, refraction k = 0.13.   maps.tristanhotham.com/sea-sunsets",
         fontproperties=FELL, fontsize=8, color=MUT)
fig.savefig(os.path.join(ROOT, "reddit", "sea_sunsets_collage.png"), dpi=300, facecolor=fig.get_facecolor())
print(Image.open(os.path.join(ROOT, "reddit", "sea_sunsets_collage.png")).size)
