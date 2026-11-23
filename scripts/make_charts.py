"""README charts: one message per chart, one highlight colour, direct labels."""
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
RES, OUT = ROOT / "results", ROOT / "charts"
OUT.mkdir(exist_ok=True)
SURFACE, INK, INK2 = "#ffffff", "#1a1a1a", "#6b6a66"
HIGHLIGHT, CONTEXT = "#14946a", "#d9d8d3"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "text.color": INK,
                     "figure.facecolor": SURFACE, "axes.facecolor": SURFACE})


def clean(ax, keep_x_labels=False):
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_yticks([])
    ax.tick_params(axis="x", length=0, pad=6, labelsize=11, colors=INK)


def titles(fig, title, subtitle):
    fig.text(0.03, 0.97, title, fontsize=15, fontweight="bold", va="top")
    fig.text(0.03, 0.895, subtitle, fontsize=10.5, color=INK2, va="top")


# Chart 1: churn falls as protection add-ons rise
c = pd.read_csv(RES / "churn_by_protection_count.csv")
fig, ax = plt.subplots(figsize=(9, 5.2))
colors = [HIGHLIGHT if n == 0 else CONTEXT for n in c["protection_addons"]]
ax.bar(c["protection_addons"].astype(str), c["churn_rate"] * 100, width=0.62, color=colors)
for x, (rate, n) in enumerate(zip(c["churn_rate"], c["customers"])):
    hi = x == 0
    ax.text(x, rate * 100 + 1.5, f"{rate:.0%}", ha="center", fontsize=12,
            fontweight="bold" if hi else "normal", color=INK if hi else INK2)
ax.set_xticks(range(len(c)))
ax.set_xticklabels([f"{n} add-on{'s' if n != 1 else ''}" for n in c["protection_addons"]])
clean(ax)
titles(fig, "No protection add-ons: 57% churn. All four: 5%.",
       "Churn rate of internet subscribers by number of protection add-ons (security, backup,\n"
       "device protection, tech support). 1,267 customers have none.")
fig.subplots_adjust(left=0.03, right=0.97, top=0.76, bottom=0.08)
fig.savefig(OUT / "01_churn_by_protection.png", dpi=200)
plt.close(fig)

# Chart 2: value per customer won, by offer type
v = pd.read_csv(RES / "value_per_win_tier1.csv").set_index("offer_type")
stream = v.loc["Streaming", "new_revenue_annual"]
prot_new, prot_ret = v.loc["Protection", "new_revenue_annual"], v.loc["Protection", "retention_value_annual"]
fig, ax = plt.subplots(figsize=(9, 4.0))
ax.barh([1], [stream], height=0.5, color=HIGHLIGHT)
ax.barh([0], [prot_new + prot_ret], height=0.5, color=CONTEXT)
ax.text(stream + 2, 1, f"${stream:.0f} a year", va="center", fontsize=12, fontweight="bold")
pn, pr = round(prot_new), round(prot_ret)
ax.text(prot_new + prot_ret + 2, 0, f"${pn + pr} a year (${pn} new + ${pr} kept)",
        va="center", fontsize=11, color=INK2)
ax.set_yticks([0, 1])
ax.set_yticklabels(["Protection add-on", "Streaming add-on"], fontsize=11)
for lbl, col in zip(ax.get_yticklabels(), [INK2, INK]):
    lbl.set_color(col)
for s in ax.spines.values():
    s.set_visible(False)
ax.set_xticks([])
ax.tick_params(axis="y", length=0, pad=8)
ax.set_xlim(0, 175)
titles(fig, "A streaming upsell is worth 1.6x a protection add-on",
       "Annual value per customer won. Protection includes revenue kept through lower churn,\n"
       "counting half of the observed churn effect.")
fig.subplots_adjust(left=0.2, right=0.97, top=0.68, bottom=0.05)
fig.savefig(OUT / "02_value_per_win.png", dpi=200)
plt.close(fig)
print("Charts saved to charts/")
