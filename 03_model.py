"""
03_model.py
Univariate rates (02_analysis.sql) can mislead because factors overlap: e.g. SMS
reminders only go out for appointments booked well ahead. This script fits one
logistic regression with everything in it, to see which effects survive when the
others are held constant, and checks how well the factors predict on future data.

Run after run_analysis.py:   python 03_model.py
Outputs: results/model_odds_ratios.csv, results/model_metrics.csv
"""
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parent
con = sqlite3.connect(ROOT / "data" / "noshow.db")
df = pd.read_sql_query("SELECT * FROM appointments", con)
con.close()

# --- feature engineering -----------------------------------------------------
df["history"] = np.select(
    [df.prior_appointments == 0, df.prior_no_shows == 0, df.prior_no_shows == 1],
    ["1. No earlier visit", "2. Earlier visits, none missed", "3. One earlier no-show"],
    default="4. Two+ earlier no-shows",
)
df["male"] = (df.gender == "M").astype(int)

# Reference group for each categorical = its largest group (standard practice)
REFS = {"lead_bucket": "1. Same day", "age_group": "5. 45-59", "history": "1. No earlier visit"}
LABELS = {"lead_bucket": "Lead time", "age_group": "Age", "history": "History"}
BINARY = {
    "sms_received": "SMS reminder received",
    "scholarship": "Scholarship (welfare enrolment)",
    "hypertension": "Hypertension",
    "diabetes": "Diabetes",
    "alcoholism": "Alcoholism",
    "handicap": "Handicap",
    "male": "Male (vs female)",
}

parts, names = [], {}
for col, ref in REFS.items():
    d = pd.get_dummies(df[col]).astype(int).drop(columns=[ref])
    for c in d.columns:
        names[f"{col}::{c}"] = f"{LABELS[col]}: {c[3:]} (vs {ref[3:].lower() if col != 'history' else ref[3:].lower()})"
    d.columns = [f"{col}::{c}" for c in d.columns]
    parts.append(d)
for col, label in BINARY.items():
    parts.append(df[[col]].rename(columns={col: col}))
    names[col] = label
X = pd.concat(parts, axis=1).astype(float)
y = df["no_show"].astype(int)

# --- 1) adjusted odds ratios on all data ------------------------------------
fit = sm.Logit(y, sm.add_constant(X)).fit(disp=False)
ci = fit.conf_int()
or_table = pd.DataFrame(
    {
        "factor": [names[c] for c in X.columns],
        "odds_ratio": np.exp(fit.params[X.columns]),
        "ci_low": np.exp(ci.loc[X.columns, 0]),
        "ci_high": np.exp(ci.loc[X.columns, 1]),
        "p_value": fit.pvalues[X.columns],
    }
).round(4)
or_table.to_csv(ROOT / "results" / "model_odds_ratios.csv", index=False)
print(or_table.to_string(index=False))

# --- 2) how predictable is it? time-based split ------------------------------
# Train on earlier appointment dates, test on the later ones (like real use).
cut = df["appointment_date"].sort_values().iloc[int(len(df) * 0.7)]
train, test = df.appointment_date <= cut, df.appointment_date > cut


def auc(cols):
    m = LogisticRegression(max_iter=2000).fit(X.loc[train, cols], y[train])
    return roc_auc_score(y[test], m.predict_proba(X.loc[test, cols])[:, 1])


lead_cols = [c for c in X.columns if c.startswith("lead_bucket::")]
metrics = pd.DataFrame(
    {
        "model": ["Guess the base rate (no information)", "Lead time only", "All factors"],
        "test_auc": [0.5, auc(lead_cols), auc(list(X.columns))],
    }
).round(3)
metrics.to_csv(ROOT / "results" / "model_metrics.csv", index=False)
print(f"\ntrain rows: {train.sum():,} (appointments up to {cut}) | test rows: {test.sum():,}")
print(metrics.to_string(index=False))
