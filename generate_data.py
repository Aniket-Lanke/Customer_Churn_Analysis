"""Generate a synthetic telecom churn dataset (Telco-style schema, 7,043 rows).
Swap data/telco_churn.csv with the real IBM/Kaggle Telco file and the rest runs unchanged."""
import numpy as np, pandas as pd
rng = np.random.default_rng(42)
n = 7043
yn = lambda p: np.where(rng.random(n) < p, "Yes", "No")
contract = rng.choice(["Month-to-month", "One year", "Two year"], n, p=[.55, .21, .24])
tenure = np.where(contract == "Month-to-month", rng.gamma(1.6, 12, n),
          np.where(contract == "One year", rng.normal(38, 18, n), rng.normal(56, 16, n)))
tenure = np.clip(tenure.round(), 0, 72).astype(int)
internet = rng.choice(["DSL", "Fiber optic", "No"], n, p=[.34, .44, .22])
phone = yn(.9)
def addon(p): return np.where(internet == "No", "No internet service", yn(p))
sec, tech, stv = addon(.3), addon(.3), addon(.45)
monthly = (20 * (phone == "Yes") + np.select([internet == "DSL", internet == "Fiber optic"], [25, 55], 0)
           + 5 * (stv == "Yes") + 4 * (sec == "Yes") + 4 * (tech == "Yes") + rng.normal(0, 3, n)).clip(18.25, 119)
pay = rng.choice(["Electronic check", "Mailed check", "Bank transfer (automatic)", "Credit card (automatic)"], n, p=[.34, .23, .22, .21])
paperless = yn(.6)
senior = (rng.random(n) < .16).astype(int)
z = (-1.7 - 0.045 * tenure + 0.018 * (monthly - 65) + 1.1 * (contract == "Month-to-month")
     - 1.2 * (contract == "Two year") + 0.5 * (internet == "Fiber optic") + 0.55 * (pay == "Electronic check")
     + 0.3 * (paperless == "Yes") + 0.3 * senior + 0.45 * (sec == "No") + 0.4 * (tech == "No") + rng.normal(0, .6, n))
churn = np.where(rng.random(n) < 1 / (1 + np.exp(-z)), "Yes", "No")
total = (tenure * monthly * rng.uniform(.95, 1.05, n)).round(2).astype(str)
total[tenure == 0] = " "          # blanks, as in the real Telco file
df = pd.DataFrame({
 "customerID": [f"{rng.integers(1000,9999)}-{''.join(rng.choice(list('ABCDEFGHIJKLMNOPQRSTUVWXYZ'),5))}" for _ in range(n)],
 "gender": rng.choice(["Male", "Female"], n), "SeniorCitizen": senior, "Partner": yn(.48), "Dependents": yn(.3),
 "tenure": tenure, "PhoneService": phone,
 "MultipleLines": np.where(phone == "No", "No phone service", yn(.42)),
 "InternetService": internet, "OnlineSecurity": sec, "TechSupport": tech, "StreamingTV": stv,
 "Contract": contract, "PaperlessBilling": paperless, "PaymentMethod": pay,
 "MonthlyCharges": monthly.round(2), "TotalCharges": total, "Churn": churn})
df.loc[:, "customerID"] = df["customerID"].where(~df["customerID"].duplicated(), df["customerID"] + "X")
df.to_csv("data/telco_churn.csv", index=False)
print(df.shape, "churn rate:", (df.Churn == "Yes").mean().round(3))
