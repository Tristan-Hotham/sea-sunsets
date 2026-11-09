"""House style for the static figures: the ink look of The Inked World on parchment. Black coasts with blue ripple lines,
red and black lettering in IM Fell and MedievalSharp, Natural Earth outlines."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Polygon as MPoly, PathPatch
from matplotlib.path import Path
import numpy as np
from pyproj import Transformer
from shapely.geometry import shape, box, mapping
from shapely.ops import transform as stransform, unary_union
from common import *

for f in ("IMFeENrm28P.ttf", "IMFeENsc28P.ttf", "IMFeGPit28P.ttf", "MedievalSharp.ttf"):
    fm.fontManager.addfont(f"{INKFONTS}/{f}")
for f in ("IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf"):
    fm.fontManager.addfont(f"{FONTS}/{f}")
FELL = fm.FontProperties(fname=f"{INKFONTS}/IMFeENrm28P.ttf")
FELLSC = fm.FontProperties(fname=f"{INKFONTS}/IMFeENsc28P.ttf")
FELLIT = fm.FontProperties(fname=f"{INKFONTS}/IMFeGPit28P.ttf")
HAND = fm.FontProperties(fname=f"{INKFONTS}/MedievalSharp.ttf")
MONO = "IBM Plex Mono"
plt.rcParams.update({"font.family": "IM FELL English PRO", "font.size": 13, "axes.edgecolor": "#6E604E", "axes.labelcolor": "#2B2119",
                     "xtick.color": "#6E604E", "ytick.color": "#6E604E", "axes.facecolor": "none", "axes.unicode_minus": False})
try:
    plt.rcParams["font.family"] = FELL.get_name()
except Exception:
    pass
PAPER, PAPER2, INKC, MUT, RED, BLUE, RIPPLE, LANDC = "#F6EED8", "#F3E5BF", "#2B2119", "#6E604E", "#A3261B", "#3D6E9E", "#6F9DC6", "#F1E2B8"
CHART_COL = {"pisana": "#A3261B", "catalan": "#3D6E9E"}
SEPIA = "#8C6A43"
NE_LAND = jload(f"{GEO}/ne_50m_land.geojson")["features"]
NE_C50 = jload(f"{GEO}/ne_50m_admin_0_countries.geojson")["features"]


def projector(crs):
    tr = Transformer.from_crs(4326, crs, always_xy=True)
    return lambda x, y, z=None: tr.transform(x, y)


def project_geoms(feats, crs, clip=None):
    f = projector(crs)
    out = []
    for ft in feats:
        g = shape(ft["geometry"])
        if clip is not None:
            g = g.intersection(clip)
            if g.is_empty: continue
        pg = stransform(f, g)
        if not pg.is_valid: pg = pg.buffer(0)
        out.append((ft["properties"], pg))
    return out


def patches(ax, g, **kw):
    polys = g.geoms if g.geom_type == "MultiPolygon" else [g] if g.geom_type == "Polygon" else []
    for p in polys:
        verts, codes = [], []
        for ring in [p.exterior] + list(p.interiors):
            cs = np.asarray(ring.coords)
            verts += cs.tolist(); codes += [Path.MOVETO] + [Path.LINETO] * (len(cs) - 2) + [Path.CLOSEPOLY]
        ax.add_patch(PathPatch(Path(verts, codes), **kw))


def lines(ax, g, **kw):
    if g.is_empty: return
    gs = g.geoms if hasattr(g, "geoms") else [g]
    for x in gs:
        if x.geom_type == "Polygon":
            for ring in [x.exterior] + list(x.interiors):
                cs = np.asarray(ring.coords); ax.plot(cs[:, 0], cs[:, 1], **kw)
        elif x.geom_type in ("LineString", "LinearRing"):
            cs = np.asarray(x.coords); ax.plot(cs[:, 0], cs[:, 1], **kw)
        elif hasattr(x, "geoms"):
            lines(ax, x, **kw)


def ink_base(ax, crs, extent_ll, ripple_m=(9e3, 22e3, 40e3), land_fc=LANDC, coast_lw=0.9, countries=True, country_fc=None, simplify=None,
             min_area=0):
    """Parchment sea, land with a black coast and blue ripple lines out to sea, country borders as fine dashes.
    country_fc: function(iso) -> colour or None. Returns the projected extent."""
    lon0, lon1, lat0, lat1 = extent_ll
    clip = box(max(-180, lon0 - 30), max(-89, lat0 - 15), min(180, lon1 + 30), min(89, lat1 + 15))
    land = [g for _, g in project_geoms(NE_LAND, crs, clip)]
    land = unary_union(land)
    if not land.is_valid: land = land.buffer(0)
    if simplify: land = land.simplify(simplify)
    if min_area:
        land = unary_union([p for p in (land.geoms if hasattr(land, "geoms") else [land]) if p.area >= min_area])
    f = projector(crs)
    xs, ys = f(np.array([lon0, lon1, lon0, lon1, (lon0 + lon1) / 2, (lon0 + lon1) / 2]), np.array([lat0, lat0, lat1, lat1, lat0, lat1]))
    ext = (min(xs), max(xs), min(ys), max(ys))
    ax.set_facecolor(PAPER)
    for k, d in enumerate(ripple_m):
        lines(ax, land.buffer(d, resolution=4).boundary, color=RIPPLE, lw=0.55 - 0.12 * k, alpha=0.75 - 0.2 * k, zorder=1)
    patches(ax, land, fc=land_fc, ec="none", zorder=2)
    if countries:
        for p, g in project_geoms(NE_C50, crs, clip):
            iso = p["ADM0_A3"]
            c = country_fc(iso) if country_fc else None
            if c:
                patches(ax, g, fc=c, ec="none", zorder=2.5, alpha=0.85)
            lines(ax, g.boundary if hasattr(g, "boundary") else g, color=INKC, lw=0.25, alpha=0.45, ls=(0, (3, 2)), zorder=3)
    lines(ax, land, color=INKC, lw=coast_lw, zorder=4)
    ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3]); ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values(): s.set_visible(False)
    return ext, f


def parchment(fig, seed=3, alpha=0.06):
    """faint mottling over the whole sheet, as on old paper"""
    rng = np.random.default_rng(seed)
    n = 48
    z = rng.normal(size=(n, int(n * fig.get_figwidth() / fig.get_figheight()) + 1))
    from scipy.ndimage import gaussian_filter
    z = gaussian_filter(z, 2.5)
    ax = fig.add_axes([0, 0, 1, 1], zorder=-10); ax.axis("off")
    ax.imshow(z, cmap=matplotlib.colors.LinearSegmentedColormap.from_list("p", ["#E9D9AE", PAPER]), alpha=1, aspect="auto", interpolation="bicubic")
    fig.patch.set_facecolor(PAPER)
    return ax


def save(fig, path, dpi=200):
    fig.savefig(path, dpi=dpi, facecolor=fig.get_facecolor())
    plt.close(fig)

