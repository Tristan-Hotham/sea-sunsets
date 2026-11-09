"""Step 8: the paper. Fills code/paper_template.tex from data/results.json, adds tables, compiles with xelatex.
Output: release/paper/Hotham_Sea_Sunsets.pdf and .tex beside the f_*.png figures.
The DOI stays a placeholder (https://doi.org/10.5281/zenodo.24089892 printed) unless DOI is set: DOI=10.5281/zenodo.N python3 code/08_paper.py"""
import subprocess
from common import *

R = jload(f"{DATA}/results.json")
OUT = os.path.join(ROOT, "release", "paper"); NAME = "Hotham_Sea_Sunsets"
tex = lambda s: str(s).replace("\\", "").replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#").replace("$", "\\$")


def tfmt(v, f):
    if f == "int": return f"{int(round(float(v))):,}"
    if f == "f0": return f"{float(v):.0f}"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    if f == "f3": return f"{float(v):.3f}"
    return tex(str(v))


N = R["nations"]
rows = "".join(f"{k} & {v['n']:,} & {v['set_any_pc']:.1f} & {v['set_all_pc']:.1f} & {v['rise_any_pc']:.1f} & {v['both_pc']:.1f} & {v['mean_set']:.0f} & {v['mean_rise']:.0f}\\\\\n" for k, v in N.items())
TN = ("\\begin{table}[tbp]\\centering\\footnotesize\\caption{By nation: beaches, share with at least one sea sunset (\\%), every day (\\%), at least one sea sunrise (\\%), both (\\%), and mean days a year with a sea sunset and sunrise.}\\label{tab:nations}"
      "\\begin{tabular}{lrrrrrrr}\\toprule Nation & Beaches & Sunset & All year & Sunrise & Both & Sunset days & Sunrise days\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
IS = [i for i in R["islands"] if i["name"]][:15]
rows = "".join(f"{tex(i['name'])} & {i['set_beaches']} & {i['set_days']:,} & {i['rise_beaches']} & {i['rise_days']:,} & {tex(i['examples'][0]['beach'])} ({i['examples'][0]['days']})\\\\\n" for i in IS)
TI = ("\\begin{table}[tbp]\\centering\\footnotesize\\caption{Islands that hide the Sun: beaches and beach-days at sunset and sunrise, and the beach most affected (days).}\\label{tab:islands}"
      "\\begin{tabular}{lrrrrl}\\toprule Island & Sunset beaches & Days & Sunrise beaches & Days & Most affected\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
yn = lambda b: "yes" if b else "no"
rows = "".join(f"{tex(c['name'])} & {tex(c['county'])} & {c['sea_set_days']} & {c['sea_rise_days']} & {yn(c['set_jun21'])} & {yn(c['set_dec21'])} & {yn(c['rise_jun21'])} & {yn(c['rise_dec21'])}\\\\\n" for c in R["cases"].values())
TC = ("\\begin{table}[tbp]\\centering\\scriptsize\\caption{Some well-known beaches: days of 2026 with a sea sunset and sunrise, and whether the Sun sets or rises over the sea on the solstices.}\\label{tab:cases}"
      "\\begin{tabular}{llrrcccc}\\toprule Beach & County & Sunsets & Sunrises & Set 21 Jun & Set 21 Dec & Rise 21 Jun & Rise 21 Dec\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
t = open(os.path.join(ROOT, "code", "paper_template.tex"), encoding="utf-8").read()
t = t.replace("{{AI}}", AI).replace("{{PAGE}}", PAGE).replace("{{REPO}}", REPO)
for k, v in (("TABLE_NATIONS", TN), ("TABLE_ISLANDS", TI), ("TABLE_CASES", TC)):
    t = t.replace("{{" + k + "}}", v)
t = re.sub(r"\{\{(?!TABLE_|DOI)([^}|]+)(\|(\w+))?\}\}", lambda m: tfmt(get(R, m.group(1)), m.group(3) or "raw"), t)
DOI = os.environ.get("DOI")
t = t.replace("https://doi.org/10.5281/zenodo.24089892", f"\\url{{https://doi.org/{DOI}}}" if DOI else "\\{\\{DOI\\_URL\\}\\}")
assert "{{" not in t and "--" not in t and "—" not in t and "–" not in t
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME + ".tex"), "w", encoding="utf-8").write(t)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
log = open(os.path.join(OUT, NAME + ".log"), encoding="utf-8", errors="ignore").read()
print([l for l in log.splitlines() if "Missing character" in l or "undefined" in l.lower() or "Overfull" in l][:12])
for ext in (".aux", ".log", ".out", ".bbl", ".blg"):
    q = os.path.join(OUT, NAME + ext)
    if os.path.exists(q): os.remove(q)
txt = subprocess.run(["pdftotext", os.path.join(OUT, NAME + ".pdf"), "-"], capture_output=True, text=True).stdout
pages = subprocess.run(["pdfinfo", os.path.join(OUT, NAME + ".pdf")], capture_output=True, text=True).stdout
print("paper", r.returncode, len(txt.split()), "words;", [l for l in pages.splitlines() if l.startswith("Pages")], "dashes:", txt.count("—") + txt.count("–"))
