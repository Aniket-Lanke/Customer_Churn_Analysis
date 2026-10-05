"""Customer Churn Analysis & Prediction: cleaning, feature engineering, modelling, dashboard export."""
import json
from pathlib import Path
BASE = Path(__file__).resolve().parent            # project folder (only read from)
OUT = Path.home() / "churn_project_output"          # results are written here (always writable)
OUT.mkdir(exist_ok=True)
import numpy as np, pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix

# ---------- 1. Load & clean ----------
df = pd.read_csv(BASE / "data" / "telco_churn.csv")
print("Raw shape:", df.shape)
df["TotalCharges"] = pd.to_numeric(df["TotalCharges"].str.strip(), errors="coerce")   # blanks -> NaN
print("Missing TotalCharges:", df["TotalCharges"].isna().sum())
# New customers (tenure 0) have not been billed yet -> total charges = 0
df["TotalCharges"] = df["TotalCharges"].fillna(0)
df = df.drop_duplicates("customerID")
df["Churn"] = (df["Churn"] == "Yes").astype(int)

# ---------- 2. Feature engineering ----------
df["tenure_group"] = pd.cut(df["tenure"], [-1, 12, 24, 48, 72], labels=["0-12 mo", "13-24 mo", "25-48 mo", "49-72 mo"])
addons = ["OnlineSecurity", "TechSupport", "StreamingTV"]
df["num_addons"] = (df[addons] == "Yes").sum(axis=1)
df["avg_monthly_spend"] = np.where(df["tenure"] > 0, df["TotalCharges"] / df["tenure"].replace(0, np.nan), df["MonthlyCharges"])
df["charge_to_avg_ratio"] = df["MonthlyCharges"] / df["avg_monthly_spend"]
df["auto_pay"] = df["PaymentMethod"].str.contains("automatic").astype(int)
df["no_protection"] = ((df["OnlineSecurity"] == "No") & (df["TechSupport"] == "No")).astype(int)
df["billing_pattern"] = df["PaymentMethod"].str.replace(r" \(automatic\)", "", regex=True) + " / " + np.where(df["PaperlessBilling"] == "Yes", "Paperless", "Paper")
df.to_csv(OUT / "telco_churn_clean.csv", index=False)

# ---------- 3. Model ----------
cat_cols = ["gender", "Partner", "Dependents", "PhoneService", "MultipleLines", "InternetService", "OnlineSecurity",
            "TechSupport", "StreamingTV", "Contract", "PaperlessBilling", "PaymentMethod"]
num_cols = ["SeniorCitizen", "tenure", "MonthlyCharges", "TotalCharges", "num_addons", "avg_monthly_spend",
            "charge_to_avg_ratio", "auto_pay", "no_protection"]
X = pd.get_dummies(df[cat_cols + num_cols], columns=cat_cols, drop_first=True).astype(float)
y = df["Churn"]
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)
sc = StandardScaler().fit(Xtr)
models = {
    "Logistic Regression": (LogisticRegression(max_iter=1000, class_weight="balanced"), True),
    "Random Forest": (RandomForestClassifier(n_estimators=300, max_depth=8, min_samples_leaf=10,
                                              class_weight="balanced", random_state=42, n_jobs=-1), False)}
results, fitted = {}, {}
for name, (m, scaled) in models.items():
    A, B = (sc.transform(Xtr), sc.transform(Xte)) if scaled else (Xtr, Xte)
    m.fit(A, ytr)
    pred, proba = m.predict(B), m.predict_proba(B)[:, 1]
    tn, fp, fn, tp = confusion_matrix(yte, pred).ravel()
    results[name] = dict(accuracy=accuracy_score(yte, pred), precision=precision_score(yte, pred),
                         recall=recall_score(yte, pred), f1=f1_score(yte, pred), roc_auc=roc_auc_score(yte, proba),
                         confusion=dict(tn=int(tn), fp=int(fp), fn=int(fn), tp=int(tp)))
    fitted[name] = (m, proba)
    print(f"\n{name}\n", {k: round(v, 3) for k, v in results[name].items() if k != "confusion"},
          "\nConfusion matrix [[TN FP][FN TP]]:", [[tn, fp], [fn, tp]])
best = max(results, key=lambda k: results[k]["roc_auc"])
print("\nBest model by ROC-AUC:", best)

# Feature importance (Random Forest) and churn-risk scores for every customer
rf = fitted["Random Forest"][0]
imp = pd.Series(rf.feature_importances_, index=X.columns).sort_values(ascending=False).head(10)
bm = fitted[best][0]
df["churn_risk"] = bm.predict_proba(sc.transform(X) if best == "Logistic Regression" else X)[:, 1]
df["risk_band"] = pd.cut(df["churn_risk"], [-.01, .3, .6, 1.0], labels=["Low", "Medium", "High"])
df[["customerID", "Contract", "tenure", "MonthlyCharges", "churn_risk", "risk_band"]].sort_values(
    "churn_risk", ascending=False).to_csv(OUT / "churn_risk_scores.csv", index=False)

# ---------- 4. Dashboard metrics (what the Power BI measures compute) ----------
def seg(col):
    g = df.groupby(col, observed=True).agg(customers=("Churn", "size"), churned=("Churn", "sum"))
    g["rate"] = (g.churned / g.customers * 100).round(1)
    return [dict(name=str(i), customers=int(r.customers), rate=float(r.rate)) for i, r in g.iterrows()]
churned = df[df.Churn == 1]
at_risk = df[(df.Churn == 0) & (df.churn_risk >= .6)]
dash = dict(
    customers=int(len(df)), churned=int(df.Churn.sum()), churn_rate=round(df.Churn.mean() * 100, 1),
    monthly_revenue_lost=round(float(churned.MonthlyCharges.sum()), 0),
    revenue_at_risk=round(float(at_risk.MonthlyCharges.sum()), 0), high_risk_customers=int(len(at_risk)),
    contract=seg("Contract"), tenure=seg("tenure_group"), internet=seg("InternetService"),
    payment=seg("PaymentMethod"), billing=seg("billing_pattern"),
    drivers=[dict(name=k, value=round(float(v) * 100, 1)) for k, v in imp.items()],
    models=results, best_model=best)
json.dump(dash, open(OUT / "dashboard_data.json", "w"), indent=1)
print("\nChurn rate:", dash["churn_rate"], "% | Monthly revenue at risk: $", dash["revenue_at_risk"])

print("Results saved in:", OUT)
