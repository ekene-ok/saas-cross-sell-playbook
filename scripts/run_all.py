"""Cross-sell playbook pipeline.

1. Run the SQL (DuckDB) to build clean tables, adoption and churn views, segments
2. Recover each add-on's monthly price from the billing data (linear regression)
3. Check the churn link holds after controlling for tenure and contract (logistic regression)
4. Score every active customer's propensity for each add-on they lack (look-alike models)
5. Pick a next best offer per customer and forecast the pipeline under stated assumptions

Usage (repo root):  python scripts/run_all.py
"""
from pathlib import Path
import duckdb
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results"
OUT.mkdir(exist_ok=True)
SEED = 42

# 1. SQL ---------------------------------------------------------------------
con = duckdb.connect()
con.execute(f"SET file_search_path = '{ROOT}'")
for f in sorted((ROOT / "sql").glob("*.sql")):
    con.execute(f.read_text())
for view in ["addon_adoption", "churn_by_protection_count",
             "churn_by_protection_and_contract", "active_segments"]:
    con.sql(f"SELECT * FROM {view}").write_csv(str(OUT / f"{view}.csv"))
cust = con.sql("SELECT * FROM customers").df()
inet = con.sql("SELECT * FROM internet_customers").df()

ADDONS = {
    "has_online_security": "Online Security", "has_online_backup": "Online Backup",
    "has_device_protection": "Device Protection", "has_tech_support": "Tech Support",
    "has_streaming_tv": "Streaming TV", "has_streaming_movies": "Streaming Movies",
}
PROTECTION = ["has_online_security", "has_online_backup", "has_device_protection", "has_tech_support"]

# 2. Implied add-on prices -----------------------------------------------------
# Monthly charges are almost exactly a sum of list prices, so a linear regression on
# service flags recovers each add-on's price. R^2 close to 1 confirms the price list.
X = pd.get_dummies(cust["internet_type"], prefix="internet").astype(int)
for c in list(ADDONS) + ["has_phone", "has_multiple_lines"]:
    X[c] = cust[c].astype(int)
price_model = LinearRegression().fit(X, cust["monthly_charges"])
prices = pd.Series(price_model.coef_, index=X.columns).round(2)
price_r2 = price_model.score(X, cust["monthly_charges"])
pd.DataFrame({"addon": [ADDONS[a] for a in ADDONS],
              "implied_monthly_price": [prices[a] for a in ADDONS]}
             ).assign(model_r2=round(price_r2, 4)).to_csv(OUT / "implied_addon_prices.csv", index=False)


# Feature matrix shared by the models below.
def features(df, drop=()):
    f = pd.DataFrame(index=df.index)
    f["tenure_months"] = df["tenure_months"]
    f["monthly_base"] = df["internet_type"].eq("Fiber optic").astype(int)
    for c in ["is_senior", "has_partner", "has_dependents", "has_phone", "has_multiple_lines",
              "paperless_billing"] + list(ADDONS):
        if c not in drop:
            f[c] = df[c].astype(int)
    f = f.join(pd.get_dummies(df["contract"], prefix="contract", drop_first=True).astype(int))
    f = f.join(pd.get_dummies(df["payment_method"], prefix="pay", drop_first=True).astype(int))
    return f


# 3. Does the churn link survive controls? -------------------------------------
# Observational data, so this is association, not proof of cause. Controlling for tenure,
# contract and other traits shows whether add-ons still matter once those are held fixed.
Xc = features(inet, drop=list(ADDONS))
Xc["protection_addons"] = inet[PROTECTION].sum(axis=1)
churn_model = make_pipeline(StandardScaler(with_mean=False), LogisticRegression(max_iter=2000))
churn_model.fit(Xc, inet["churned"].astype(int))
coef = churn_model[-1].coef_[0][list(Xc.columns).index("protection_addons")] / churn_model[0].scale_[list(Xc.columns).index("protection_addons")]
odds_ratio = float(np.exp(coef))
pd.DataFrame([{"metric": "odds ratio of churn per extra protection add-on (controls: tenure, contract, payment, household, other services)",
               "value": round(odds_ratio, 3)}]).to_csv(OUT / "churn_adjusted_effect.csv", index=False)

# 4. Look-alike propensity per add-on --------------------------------------------
# For each add-on: model "has it" from everything else, using out-of-fold predictions so no
# customer is scored by a model that saw them. High-scoring non-adopters look like adopters.
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
scores, model_quality = {}, []
for col, name in ADDONS.items():
    Xp, y = features(inet, drop=[col]), inet[col].astype(int)
    model = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000))
    p = cross_val_predict(model, Xp, y, cv=cv, method="predict_proba")[:, 1]
    scores[col] = p
    model_quality.append({"addon": name, "adoption_rate": round(y.mean(), 3),
                          "cv_auc": round(roc_auc_score(y, p), 3)})
pd.DataFrame(model_quality).to_csv(OUT / "propensity_model_quality.csv", index=False)

# 5. Next best offer and pipeline forecast --------------------------------------
# Value of an offer = new subscription revenue + revenue kept because churn risk falls.
# The churn effect comes from observational data, so only half of it is counted
# (CAUSAL_HAIRCUT). Streaming add-ons show almost no churn link, so they carry no retention value.
CAUSAL_HAIRCUT = 0.5
active = inet[~inet["churned"]].copy()
Xa = features(active, drop=list(ADDONS))
Xa["protection_addons"] = active[PROTECTION].sum(axis=1)
Xa_plus = Xa.copy()
Xa_plus["protection_addons"] += 1
active["churn_prob"] = churn_model.predict_proba(Xa)[:, 1]
active["churn_prob_plus_one"] = churn_model.predict_proba(Xa_plus)[:, 1]
active["retention_value_annual"] = (CAUSAL_HAIRCUT
                                    * (active["churn_prob"] - active["churn_prob_plus_one"])
                                    * active["monthly_charges"] * 12)

rows = []
for col, name in ADDONS.items():
    p = pd.Series(scores[col], index=inet.index).loc[active.index]
    eligible = ~active[col]
    is_prot = col in PROTECTION
    rows.append(pd.DataFrame({
        "customer_id": active.loc[eligible, "customer_id"],
        "offer": name,
        "offer_type": "Protection" if is_prot else "Streaming",
        "propensity": p[eligible].round(3),
        "new_revenue_annual": round(prices[col] * 12, 2),
        "retention_value_annual": (active.loc[eligible, "retention_value_annual"].round(2) if is_prot else 0.0),
    }))
offers = pd.concat(rows)
offers["value_if_converted"] = offers["new_revenue_annual"] + offers["retention_value_annual"]
offers["expected_annual_value"] = (offers["propensity"] * offers["value_if_converted"]).round(2)
nbo = (offers.sort_values("expected_annual_value", ascending=False)
             .groupby("customer_id", as_index=False).first())
nbo = nbo.merge(active[["customer_id", "contract", "tenure_band", "protection_addons",
                        "monthly_charges", "churn_prob"]], on="customer_id")
nbo["churn_prob"] = nbo["churn_prob"].round(3)
# Priority: Tier 1 = top 30% of expected annual value.
cut = nbo["expected_annual_value"].quantile(0.70)
nbo["tier"] = np.where(nbo["expected_annual_value"] >= cut, "Tier 1", "Tier 2")
nbo["motion"] = np.where(nbo["offer_type"] == "Protection", "Protection cross-sell", "Streaming upsell")
nbo.sort_values(["tier", "expected_annual_value"], ascending=[True, False]).to_csv(
    OUT / "next_best_offer_targets.csv", index=False)

# Forecast for Tier 1. Conversion rates are planning ASSUMPTIONS, shown as a range.
SCENARIOS = {"low": 0.05, "base": 0.10, "high": 0.15}
t1 = nbo[nbo["tier"] == "Tier 1"]
fc = (t1.groupby(["motion", "offer"])
        .agg(tier1_targets=("customer_id", "size"),
             new_revenue_per_win=("new_revenue_annual", "mean"),
             retention_value_per_win=("retention_value_annual", "mean"))
        .reset_index())
for s, r in SCENARIOS.items():
    fc[f"value_{s}"] = (fc["tier1_targets"] * r * (fc["new_revenue_per_win"] + fc["retention_value_per_win"])).round(0)
fc[["new_revenue_per_win", "retention_value_per_win"]] = fc[["new_revenue_per_win", "retention_value_per_win"]].round(2)
fc = fc.sort_values("value_base", ascending=False)
fc.to_csv(OUT / "pipeline_forecast_by_offer.csv", index=False)

# Value per win by offer type (for the chart and README).
per_win = (offers.groupby("offer_type")[["new_revenue_annual", "retention_value_annual"]]
                 .mean().round(2).reset_index())
per_win_t1 = (t1.groupby("offer_type")[["new_revenue_annual", "retention_value_annual"]]
                .mean().round(2).reset_index())
per_win_t1.to_csv(OUT / "value_per_win_tier1.csv", index=False)

# Segment playbook: the dominant motion per segment, and the lead offer within that motion.
def lead(df):
    motion = df["motion"].value_counts().idxmax()
    return pd.Series({
        "active_customers": len(df),
        "avg_churn_prob": round(df["churn_prob"].mean(), 3),
        "tier1_targets": int((df["tier"] == "Tier 1").sum()),
        "lead_motion": motion,
        "lead_offer": df.loc[df["motion"] == motion, "offer"].value_counts().idxmax(),
    })
seg = nbo.groupby(["contract", "tenure_band"]).apply(lead, include_groups=False).reset_index()
seg.to_csv(OUT / "segment_playbook.csv", index=False)

# Retention pilot: new month-to-month customers with no protection add-ons. Value depends on
# how much of the churn association is causal, which only a randomised test can show.
pilot = active[(active["contract"] == "Month-to-month") & (active["tenure_months"] < 12)
               & (active[PROTECTION].sum(axis=1) == 0)]
full_effect = ((pilot["churn_prob"] - pilot["churn_prob_plus_one"]) * pilot["monthly_charges"] * 12)
pilot_rows = [{"causal_share_assumed": c,
               "pilot_customers": len(pilot),
               "avg_churn_prob": round(pilot["churn_prob"].mean(), 3),
               "retained_revenue_per_customer_won": round(c * full_effect.mean(), 2),
               "total_value_per_customer_won": round(c * full_effect.mean() + 60.24, 2)}
              for c in (0.0, 0.5, 1.0)]
pd.DataFrame(pilot_rows).to_csv(OUT / "retention_pilot_scenarios.csv", index=False)

mrr_active = active["monthly_charges"].sum()
print(f"Implied prices (R^2 {price_r2:.4f}):\n{prices[list(ADDONS)]}")
print(f"\nAdjusted churn odds ratio per protection add-on: {odds_ratio:.3f}")
print(pd.DataFrame(model_quality).to_string(index=False))
print("\nPipeline forecast (Tier 1, annual value):")
print(fc.to_string(index=False))
print(f"\nTotals: {fc[[c for c in fc.columns if c.startswith('value_')]].sum().to_dict()}")
print(f"Active internet MRR: {mrr_active:,.0f}  ARR: {mrr_active*12:,.0f}")
print(per_win_t1.to_string(index=False))
print(nbo.groupby(["tier","motion"]).size())
print(pd.DataFrame(pilot_rows).to_string(index=False))
print(f"Tier 1 targets: {len(t1)} of {len(nbo)} active internet customers")
print(seg.to_string(index=False))
