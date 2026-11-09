"""Step 7: index.html from code/page_template.html, filled from data/results.json, with the full-screen snippet.
10.5281/zenodo.24089892, https://doi.org/10.5281/zenodo.24089892 and https://blog.tristanhotham.com/2026/10/31/sea-sunsets/ stay as placeholders for the publisher."""
from common import *

R = jload(f"{DATA}/results.json")
KEEP = {"DOI", "DOI_URL", "BLOG_URL"}
C = R["cases"]
# facts stated in words, checked against the data
assert C["sennen_cove"]["sea_set_days"] == 365 and C["fistral_beach"]["set_dec21"] is False and C["fistral_beach"]["set_jun21"]
assert C["longsands"]["sea_rise_days"] == 365 and C["killiney_beach"]["sea_rise_days"] == 365
assert R["set"]["dec21"] > R["set"]["jun21"] and R["rise"]["dec21"] > R["rise"]["jun21"]
assert max(R["nations"], key=lambda k: R["nations"][k]["set_any_pc"]) == "Wales"
assert R["island_top"] == ["Isle of Mull", "Isle of Wight"] and "Isle of Man" in C["fleswick_bay"]["set_islands"]
assert R["both_counties"][0]["county"] == "Essex" and R["both_counties"][1]["county"] == "Kent"
assert C["half_moon_bay"]["set_jun21"] is False and C["half_moon_bay"]["set_dec21"] is True
assert sum(R["all_year_set_counties"].get(k, 0) for k in ("Cornwall",)) == 43
assert C["crosby_beach"]["sea_set_days"] > 200 and C["crosby_beach"]["set_dec21"] is False
assert 15 < R["neither_pc"] < 25
t = open(os.path.join(ROOT, "code", "page_template.html"), encoding="utf-8").read()
t = t.replace("{{FULLSCREEN}}", open(os.path.join(ROOT, "code", "fullscreen_snippet.html"), encoding="utf-8").read())
t = t.replace("{{REPO}}", REPO).replace("{{AI}}", AI).replace("{{BYLINE}}", BYLINE).replace("{{VERSION}}", "20261109")
t = re.sub(r"\{\{([^{}|]+)(\|(\w+))?\}\}", lambda m: m.group(0) if m.group(1) in KEEP else fmt(get(R, m.group(1)), m.group(3)), t)
assert set(re.findall(r"\{\{([^}]+)\}\}", t)) <= KEEP, set(re.findall(r"\{\{([^}]+)\}\}", t))
vis = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", t, flags=re.S)
for bad in ("—", "–", "--", "DSIT", "DCMS"):
    assert bad not in vis, bad
open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(t)
print("index.html", len(t) // 1024, "KB")
