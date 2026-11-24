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

# Chart 1: where churned revenue comes from
c = pd.read_csv(RES / "churned_revenue_by_group.csv")
total_customers = c.customers.sum()
c = c.sort_values("share_of_churned_revenue", ascending=False)
target = "First-year month-to-month, fiber"
short = {"Month-to-month, 12+ months": "Monthly, year 2+", "First-year month-to-month, fiber": "Monthly fiber, year 1",
         "Annual or two-year contract": "Annual contracts", "First-year month-to-month, DSL": "Monthly DSL, year 1"}
fig, ax = b.chart(height=4.2, label_in=1.75)
b.hbar(ax, [short.get(g, g) for g in c.churn_group], (c.share_of_churned_revenue * 100).tolist(),
       {list(c.churn_group).index(target)}, lambda v: f"{v:.0f}%", HL)
share = c.loc[c.churn_group == target, "customers"].iloc[0] / total_customers
b.titles(fig, f"First-year fiber customers are {share:.0%} of the base but 37% of lost revenue",
         "Share of churned revenue by customer group. Monthly means a month-to-month plan")
b.credit(fig, "IBM Telco Customer Churn sample, 5,517 internet customers")
b.save(fig, OUT / "01_where_churned_revenue_comes_from.png")

# Chart 2: the offers on the table are small next to the churn problem
up = pd.read_csv(RES / "pipeline_forecast_by_offer.csv")
upsell = up.loc[up.motion == "Streaming upsell", "value_base"].sum()
bundle = pd.read_csv(RES / "bundle_scenarios.csv").annual_value.max()
contract = pd.read_csv(RES / "contract_offer_scenarios.csv").annual_net_value.max()
fiber_lost = c.loc[c.churn_group == target, "revenue_churned"].iloc[0]
vals = [fiber_lost / 1e3, upsell / 1e3, bundle / 1e3, contract / 1e3]
fig, ax = b.chart(height=4.2, label_in=1.75)
b.hbar(ax, ["Year-1 fiber churn", "Streaming upsell", "Protection bundle", "Contract discount"], vals, {0},
       lambda v: f"-${abs(v):,.0f}K" if v < 0 else f"${v:,.0f}K", HL)
b.titles(fig, "The offers on the table are tiny next to the churn problem",
         "Annual value in dollars: revenue lost to churn against the best case for each offer")
b.credit(fig, "IBM Telco Customer Churn sample; offer values use the planning assumptions in the README")
b.save(fig, OUT / "02_offers_are_small.png")
print("charts saved")
