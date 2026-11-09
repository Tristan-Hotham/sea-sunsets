"""Step 6: figures for the page (img/*.jpg), the blog (release/blog/b_*.png), the paper (release/paper/f_*.png), and header.png."""
import pickle
import numpy as np
from PIL import Image
import matplotlib.patheffects as pe
from matplotlib.colors import LinearSegmentedColormap
from figstyle import *

R = jload(f"{DATA}/results.json")
rows = [x for x in pickle.load(open(f"{SCR}/results_rows.pkl", "rb")) if x["status"] == "coast"]
BLOG, PAPERD = f"{ROOT}/release/blog", f"{ROOT}/release/paper"
for d in (BLOG, PAPERD):
    os.makedirs(d, exist_ok=True)
HALO = [pe.withStroke(linewidth=3, foreground=PAPER)]
SEQ = ["#BDB8AE", "#F1DCA0", "#E6C27A", "#EDB457", "#E89A3C", "#D9782C", "#B95424"]
BOUNDS = [0, 1, 60, 120, 180, 240, 330, 366]
SEA, RISE, LANDG = "#E8962E", "#3D7EA6", "#8C8577"
DIP = math.degrees(math.sqrt(2 * EYE_M / R_EFF))


def out(fig, name, page=True, blog=True, paper=True, dpi=200):
    fig.savefig(f"{SCR}/{name}.png", dpi=dpi, facecolor=fig.get_facecolor())
    plt.close(fig)
    im = Image.open(f"{SCR}/{name}.png").convert("RGB")
    if page:
        w = min(1600, im.size[0]); im.resize((w, round(im.size[1] * w / im.size[0])), Image.LANCZOS).save(f"{IMG}/{name}.jpg", quality=84, optimize=True)
    if blog:
        w = 1800; im.resize((w, round(im.size[1] * w / im.size[0])), Image.LANCZOS).save(f"{BLOG}/b_{name}.png", optimize=True)
    if paper:
        w = min(2000, im.size[0]); im.resize((w, round(im.size[1] * w / im.size[0])), Image.LANCZOS).save(f"{PAPERD}/f_{name}.png", optimize=True)
    os.remove(f"{SCR}/{name}.png")


def col(days):
    for i in range(len(BOUNDS) - 1):
        if BOUNDS[i] <= days < BOUNDS[i + 1]:
            return SEQ[i]
    return SEQ[-1]


def seq_key(ax, x, y, title, tr):
    labs = ["no", "1 to 59", "60 to 119", "120 to 179", "180 to 239", "240 to 329", "330 to 365"]
    ax.text(x, y + 0.035, title, transform=tr, fontproperties=FELLSC, fontsize=12, color=RED)
    for i, (c, l) in enumerate(zip(SEQ, labs)):
        ax.scatter([x + 0.012], [y - i * 0.028], s=55, c=[c], edgecolors=INKC, linewidths=0.5, transform=tr, clip_on=False)
        ax.text(x + 0.03, y - i * 0.028, l + " days", transform=tr, fontproperties=FELL, fontsize=11, color=INKC, va="center")


# ---------- 1. two maps: sea sunsets and sea sunrises
crs = "+proj=tmerc +lat_0=54.5 +lon_0=-4.5 +k=1 +datum=WGS84 +units=m"
fig = plt.figure(figsize=(14, 9.0)); parchment(fig)
fig.text(0.03, 0.965, "Where the sun sets into the sea, and where it rises out of it", fontproperties=FELL, fontsize=24, color=INKC, va="center")
fig.text(0.03, 0.932, f"{R['n']['coast']:,} named beaches in Britain and Ireland (OpenStreetMap), by the number of days a year the Sun's last or first light meets open sea",
         fontproperties=FELL, fontsize=12.5, color=MUT, va="center")
for k, (ev, ttl) in enumerate((("sea_set_days", "Sea sunsets"), ("sea_rise_days", "Sea sunrises"))):
    ax = fig.add_axes([0.01 + k * 0.40, 0.01, 0.40, 0.90])
    ext, f = ink_base(ax, crs, (-10.8, 2.0, 49.8, 60.9), ripple_m=(8e3, 20e3), coast_lw=0.5)
    order = sorted(rows, key=lambda x: x[ev])
    xs, ys = f(np.array([x["olon"] for x in order]), np.array([x["olat"] for x in order]))
    ax.scatter(xs, ys, s=10, c=[col(x[ev]) for x in order], edgecolors=INKC, linewidths=0.25, zorder=6)
    ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3])
    ax.text(0.03, 0.97, ttl, transform=ax.transAxes, fontproperties=HAND, fontsize=22, color=RED, va="top", path_effects=HALO)
seq_key(fig.axes[-1], 0.815, 0.62, "Days a year", fig.transFigure)
fig.text(0.815, 0.36, "From the water's edge at each beach,\neye 3 m above the sea; land that\nshows above the horizon blocks\nthe Sun (terrain, refraction and\nthe Earth's curve included).",
         fontproperties=FELL, fontsize=10.5, color=MUT, va="top")
out(fig, "maps")

# ---------- 2. four roses
def rose(ax, x, title, sub):
    ax.set_xlim(-1.35, 1.35); ax.set_ylim(-1.45, 1.35); ax.set_aspect("equal"); ax.axis("off")
    ax.add_patch(plt.Circle((0, 0), 1.0, fc="#FBF5E4", ec="#9C8656", lw=0.8))
    ax.add_patch(plt.Circle((0, 0), 0.62, fc="none", ec="#E2D3AE", lw=0.6))
    for t, a in (("N", 0), ("E", 90), ("S", 180), ("W", 270)):
        ax.text(1.15 * math.sin(math.radians(a)), 1.15 * math.cos(math.radians(a)), t, ha="center", va="center", fontproperties=FELL, fontsize=11, color=MUT)
    doy = np.arange(1, 366); ar, as_ = rise_set_az(x["olat"], declination(doy), H0 - DIP)
    ss, rs = x["_set_str"][::2], x["_rise_str"][::2]
    for d in range(365):
        r0, r1 = (0.78, 0.97) if (d < 171 or d > 354) else (0.64, 0.77)
        for az, s, c in ((as_[d], ss[d], SEA), (ar[d], rs[d], RISE)):
            if np.isfinite(az):
                cc = c if s == "." else LANDG
                ax.plot([r0 * math.sin(math.radians(az)), r1 * math.sin(math.radians(az))], [r0 * math.cos(math.radians(az)), r1 * math.cos(math.radians(az))], color=cc, lw=1.0)
    ax.plot([0], [0], "o", color=INKC, ms=3)
    ax.text(0, 1.33, title, ha="center", va="bottom", fontproperties=HAND, fontsize=16, color=RED)
    ax.text(0, -1.25, sub, ha="center", va="top", fontproperties=FELL, fontsize=11, color=INKC)


def find(name, county):
    return next(x for x in rows if x["name"] == name and x["county"] == county)


ex = [("Sennen Cove", "Cornwall"), ("Longsands", "North Tyneside"), ("Troon", "South Ayrshire"), ("Woolacombe Sands", "Devon")]
fig = plt.figure(figsize=(14, 5.6)); parchment(fig)
fig.text(0.03, 0.94, "A year of sunsets and sunrises at four beaches", fontproperties=FELL, fontsize=22, color=INKC, va="center")
fig.text(0.03, 0.875, "Each tick is one day's sunset (left half) or sunrise (right half) bearing: gold or blue over open sea, grey behind land. Outer ring December to June, inner June to December.",
         fontproperties=FELL, fontsize=11.5, color=MUT, va="center")
for i, (n, c) in enumerate(ex):
    x = find(n, c); ax = fig.add_axes([0.02 + i * 0.245, 0.02, 0.23, 0.78])
    isl = ", ".join(f"{k} {v} days" for k, v in sorted(x["set_islands"].items(), key=lambda t: -t[1])[:1])
    rose(ax, x, f"{n}, {c}", f"{x['sea_set_days']} sea sunsets, {x['sea_rise_days']} sea sunrises" + (f"\nsunset behind {isl}" if isl else ""))
out(fig, "roses")

# ---------- 3. through the year: share of beaches with a sea sunset / sunrise each day
doy = np.arange(1, 366)
ss = np.array([[c == "." for c in x["_set_str"][::2]] for x in rows]).mean(0) * 100
rs = np.array([[c == "." for c in x["_rise_str"][::2]] for x in rows]).mean(0) * 100
fig = plt.figure(figsize=(14, 6.2)); parchment(fig)
fig.text(0.04, 0.94, "Sea sunrises belong to winter; sea sunsets come all year", fontproperties=FELL, fontsize=22, color=INKC, va="center")
fig.text(0.04, 0.88, "Share of the beaches where the Sun sets into, or rises out of, open sea on each day of the year", fontproperties=FELL, fontsize=12.5, color=MUT, va="center")
ax = fig.add_axes([0.07, 0.13, 0.9, 0.67])
ax.plot(doy, ss, color=SEA, lw=2.4, label="sunset into the sea"); ax.plot(doy, rs, color=RISE, lw=2.4, label="sunrise out of the sea")
starts = np.cumsum([0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30])
ax.set_xticks(starts + 15); ax.set_xticklabels(MON, fontproperties=FELL, fontsize=12); ax.set_xlim(1, 365)
ax.set_ylim(0, max(ss.max(), rs.max()) * 1.15); ax.set_ylabel("per cent of beaches", fontproperties=FELL, fontsize=12.5)
for sp in ("top", "right"): ax.spines[sp].set_visible(False)
ax.legend(prop=FELL, frameon=False, fontsize=12, loc="upper center", ncol=2)
for d in (171, 354):
    ax.axvline(d + 1, color=MUT, lw=0.6, ls=":")
ax.text(172, 2, "21 June", fontproperties=FELLIT, fontsize=11, color=MUT, ha="center"); ax.text(355, 2, "21 Dec", fontproperties=FELLIT, fontsize=11, color=MUT, ha="center")
out(fig, "calendar")

# ---------- 4. nations
N = R["nations"]; names = [k for k in ("England", "Wales", "Scotland", "Northern Ireland", "Ireland") if k in N]
fig = plt.figure(figsize=(13, 5.6)); parchment(fig)
fig.text(0.04, 0.93, "Wales faces the sunset, the east coasts the sunrise", fontproperties=FELL, fontsize=22, color=INKC, va="center")
fig.text(0.04, 0.865, "Share of named beaches with at least one sea sunset, at least one sea sunrise, and both, in a year", fontproperties=FELL, fontsize=12.5, color=MUT, va="center")
ax = fig.add_axes([0.07, 0.12, 0.9, 0.66]); x = np.arange(len(names)); w = 0.26
for j, (key, c, l) in enumerate((("set_any_pc", SEA, "sea sunset"), ("rise_any_pc", RISE, "sea sunrise"), ("both_pc", "#6E604E", "both"))):
    v = [N[n][key] for n in names]
    ax.bar(x + (j - 1) * w, v, width=w * 0.92, color=c, edgecolor=INKC, lw=0.5, label=l)
    for i, vv in enumerate(v):
        ax.text(x[i] + (j - 1) * w, vv + 1, f"{vv:.0f}%", ha="center", fontproperties=FELL, fontsize=10.5, color=INKC)
ax.set_xticks(x); ax.set_xticklabels([f"{n}\n({N[n]['n']} beaches)" for n in names], fontproperties=FELL, fontsize=12)
ax.set_ylim(0, 80); ax.set_yticks([]); [ax.spines[s].set_visible(False) for s in ("top", "right", "left")]
ax.legend(prop=FELL, frameon=False, fontsize=12, loc="upper right", ncol=3)
out(fig, "nations")

# ---------- 5. islands in the way
IS = [i for i in R["islands"] if i["name"]][:14]
fig = plt.figure(figsize=(13, 7.4)); parchment(fig)
fig.text(0.04, 0.95, "The islands that get in the way", fontproperties=FELL, fontsize=22, color=INKC, va="center")
fig.text(0.04, 0.905, "Beaches where an island hides the Sun at sunset or sunrise on at least one day, by island", fontproperties=FELL, fontsize=12.5, color=MUT, va="center")
ax = fig.add_axes([0.25, 0.08, 0.72, 0.78]); y = np.arange(len(IS))
ax.barh(y, [i["set_beaches"] for i in IS], color=SEA, edgecolor=INKC, lw=0.5, label="hides a sunset")
ax.barh(y, [i["rise_beaches"] for i in IS], left=[i["set_beaches"] for i in IS], color=RISE, edgecolor=INKC, lw=0.5, label="hides a sunrise")
ax.set_yticks(y); ax.set_yticklabels([i["name"] for i in IS], fontproperties=FELL, fontsize=12.5); ax.invert_yaxis()
for sp in ("top", "right"): ax.spines[sp].set_visible(False)
ax.set_xlabel("beaches", fontproperties=FELL, fontsize=12.5); ax.legend(prop=FELL, frameon=False, fontsize=12, loc="lower right")
out(fig, "islands")

# ---------- 6. the Firth of Clyde at the equinox: rays from the Ayrshire beaches, Arran in the way (drawn on the sea mask itself)
fig = plt.figure(figsize=(12, 10.6)); parchment(fig)
fig.text(0.04, 0.965, "Arran stands in the sunset", fontproperties=FELL, fontsize=22, color=INKC, va="center")
fig.text(0.04, 0.932, "The Firth of Clyde: the line of sunset from each beach on 20 March, gold to the open horizon, grey to the land that hides the Sun",
         fontproperties=FELL, fontsize=12, color=MUT, va="center")
LO0, LO1, LA0, LA1 = -5.80, -4.50, 55.18, 55.92
xa, yb = tile_of(LO0, LA0); xb, ya = tile_of(LO1, LA1)
M = np.zeros(((yb - ya + 1) * MPX, (xb - xa + 1) * MPX), np.uint8)
for tx in range(xa, xb + 1):
    for ty in range(ya, yb + 1):
        fn = f"{MASKS}/{tx}_{ty}.npy"
        if os.path.exists(fn):
            M[(ty - ya) * MPX:(ty - ya + 1) * MPX, (tx - xa) * MPX:(tx - xa + 1) * MPX] = np.unpackbits(np.load(fn))[:MPX * MPX].reshape(MPX, MPX)
ox, oy = xa * MPX, ya * MPX
P = lambda lo, la: (lambda p: (p[0] - ox, p[1] - oy))(lonlat_to_px(np.asarray(lo), np.asarray(la), Z, MPX))
(c0, r1), (c1, r0) = P(LO0, LA0), P(LO1, LA1)
ax = fig.add_axes([0.03, 0.03, 0.94, 0.88])
rgb = np.where(M[..., None] > 0, np.array([0.96, 0.93, 0.85]), np.array([0.945, 0.886, 0.722]))
ax.imshow(rgb, interpolation="nearest")
ax.contour(M, levels=[0.5], colors=[INKC], linewidths=0.6)
d0 = 78
for x in rows:
    if not (LO0 < x["olon"] < LO1 and LA0 < x["olat"] < LA1): continue
    az = rise_set_az(x["olat"], declination(d0 + 1), H0 - DIP)[1]
    cc = x["_set_str"][2 * d0:2 * d0 + 2]; c = cc[0]
    A_ = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    dm = 60000 if c == "." else min(50 * (A_.index(cc[0]) * 62 + A_.index(cc[1])), 60000)
    lo, la = destination(x["olon"], x["olat"], az, np.linspace(0, dm, 60))
    px, py = P(lo, la)
    ax.plot(px, py, color=SEA if c == "." else "#6E604E", lw=1.8 if c == "." else 1.3, ls="-" if c == "." else (0, (3, 2)), zorder=5)
    bx, by = P(x["olon"], x["olat"])
    ax.scatter([bx], [by], s=34, c=[col(x["sea_set_days"])], edgecolors=INKC, linewidths=0.7, zorder=7)
for nm, lo, la, big in (("Isle of Arran", -4.982, 55.655, 1), ("Ayrshire", -4.96, 55.30, 0), ("Kintyre", -5.42, 55.33, 0), ("Bute", -4.954, 55.826, 0), ("Ailsa Craig", -5.117, 55.215, 0), ("Cumbrae", -4.926, 55.797, 0)):
    px, py = P(lo, la)
    ax.text(px, py, nm, fontproperties=HAND if big else FELLIT, fontsize=16 if big else 12, color=RED if big else INKC, ha="center", zorder=8, path_effects=HALO)
ax.set_xlim(c0, c1); ax.set_ylim(r1, r0); ax.set_xticks([]); ax.set_yticks([])
for sp in ax.spines.values(): sp.set_color(INKC)
out(fig, "clyde")

# ---------- header
fig = plt.figure(figsize=(12, 6.3)); parchment(fig)
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 12); ax.set_ylim(0, 6.3); ax.axis("off")
for k in range(9):
    ax.add_patch(plt.Rectangle((6.6, 2.0 - k * 0.06), 5.4, 0.06, fc=["#F6D38A", "#F2C46A", "#EDB457", "#E89A3C", "#D9782C"][min(k, 4)], ec="none", alpha=0.25))
ax.add_patch(plt.Circle((9.3, 2.0), 0.85, fc="#E8962E", ec="none", alpha=0.9))
ax.add_patch(plt.Rectangle((6.2, 0), 5.8, 2.0, fc="#7FA7C2", ec="none"))
for k in range(12):
    yy = 1.85 - k * 0.15
    ax.plot([6.4 + (k % 3) * 0.3, 11.8 - (k % 2) * 0.4], [yy, yy], color="#F3E5BF", lw=0.9, alpha=0.7)
ax.add_patch(plt.Rectangle((6.2, 1.96), 5.8, 0.05, fc="#E8962E", ec="none", alpha=0.9))
ax.text(0.6, 4.9, "Where the sun sets", fontproperties=FELL, fontsize=44, color=INKC, va="center")
ax.text(0.6, 3.95, "into the sea", fontproperties=HAND, fontsize=58, color=RED, va="center")
ax.text(0.62, 2.9, f"{R['n']['coast']:,} beaches in Britain and Ireland, day by day:", fontproperties=FELL, fontsize=17, color=INKC, va="center")
ax.text(0.62, 2.45, f"{R['set']['any_pc']:.0f}% see a sea sunset, {R['rise']['any_pc']:.0f}% a sea sunrise.", fontproperties=FELL, fontsize=17, color=INKC, va="center")
ax.text(0.62, 0.55, "maps.tristanhotham.com/sea-sunsets", fontproperties=FELL, fontsize=13, color=MUT, va="center")
fig.savefig(f"{ROOT}/header.png", dpi=100, facecolor=fig.get_facecolor()); plt.close(fig)
assert Image.open(f"{ROOT}/header.png").size == (1200, 630)
print("figures done")
