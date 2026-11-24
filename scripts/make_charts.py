"""README charts in the portfolio chart style: one message per chart, one highlight colour, direct labels."""
from pathlib import Path
import sys
import pandas as pd
sys.path.insert(0, str(Path(__file__).parent))
import brand_style as b

ROOT = Path(__file__).resolve().parents[1]
RES, OUT = ROOT / "results", ROOT / "charts"
OUT.mkdir(exist_ok=True)
HL = b.PROJECT["saas-cross-sell-playbook"]
SRC = "IBM Telco Customer Churn sample (7,043 customers; 5,517 with internet service)"

# Chart 1: where churned revenue comes from -------------------------------------------------
c = pd.read_csv(RES / "churned_revenue_by_group.csv")
total_customers = c.customers.sum()
c = c.sort_values("share_of_churned_revenue")
fig, ax = b.figure(8, 4.4)
target = "First-year month-to-month, fiber"
colors = [HL if g == target else b.CONTEXT for g in c.churn_group]
bars = ax.barh(c.churn_group, c.share_of_churned_revenue * 100, color=colors, height=0.55)
for bar, (_, r) in zip(bars, c.iterrows()):
    hi = r.churn_group == target
    ax.text(bar.get_width() + 0.8, bar.get_y() + bar.get_height() / 2,
            f"{r.share_of_churned_revenue:.0%}  (${r.revenue_churned / 1e3:,.0f}K, {r.churn_rate:.0%} churn)",
            va="center", fontsize=10.5, color=b.INK if hi else b.MUTED)
ax.set_xlim(0, 75)
ax.set_xticks([])
b.clean(ax, keep="y")
share = c.loc[c.churn_group == target, "customers"].iloc[0] / total_customers
b.headline(fig, f"First-year fiber customers are {share:.0%} of the base but 37% of lost revenue",
           "Share of annual revenue that churned, by customer group (internet customers)")
b.source(fig, SRC)
b.finish(fig, OUT / "01_where_churned_revenue_comes_from.png", top=0.80, bottom=0.12, left=0.33)

# Chart 2: the levers on the table are small ------------------------------------------------
up = pd.read_csv(RES / "pipeline_forecast_by_offer.csv")
upsell = up.loc[up.motion == "Streaming upsell", "value_base"].sum()
bundle = pd.read_csv(RES / "bundle_scenarios.csv").annual_value.max()
contract = pd.read_csv(RES / "contract_offer_scenarios.csv").annual_net_value.max()
fiber_lost = c.loc[c.churn_group == target, "revenue_churned"].iloc[0]
rows = [("Revenue lost from first-year fiber customers", fiber_lost), ("Streaming upsell (base case)", upsell),
        ("Protection bundle (if fully causal)", bundle), ("One-year contract at 10% off (if fully causal)", contract)]
fig, ax = b.figure(8, 4.6)
labels, vals = [r[0] for r in rows][::-1], [r[1] / 1e3 for r in rows][::-1]
colors = [HL if l.startswith("Revenue lost") else b.CONTEXT for l in labels]
bars = ax.barh(labels, vals, color=colors, height=0.55)
for bar, v, l in zip(bars, vals, labels):
    txt = (f"-${abs(v):,.0f}K" if v < 0 else f"${v:,.0f}K") + " a year"
    ax.text(max(v, 0) + 8, bar.get_y() + bar.get_height() / 2, txt, va="center", fontsize=10.5,
            color=b.INK if l.startswith("Revenue lost") else b.MUTED)
ax.axvline(0, color=b.HAIRLINE, linewidth=1)
ax.set_xlim(-10, max(vals) * 1.35)
ax.set_xticks([])
b.clean(ax, keep=None)
b.headline(fig, "The offers on the table are tiny next to the churn problem",
           "Annual value of each offer, compared with the revenue first-year fiber customers take with them")
b.source(fig, "IBM Telco Customer Churn sample; offer values use the stated planning assumptions")
b.finish(fig, OUT / "02_offers_are_small.png", top=0.80, bottom=0.12, left=0.40)
print("charts saved")
