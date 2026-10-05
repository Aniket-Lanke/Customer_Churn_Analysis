# Customer Churn Analysis & Prediction

Telecom churn project: Python cleaning and feature engineering, MySQL segmentation, Scikit-learn models, and a stakeholder dashboard.

## Run
    py -m pip install pandas numpy scikit-learn
    py run_all.py

Results and the dashboard are saved to a `churn_project_output` folder in your user folder (the dashboard opens automatically).

## Files
- `churn_analysis.py`: missing-value handling, features (tenure_group, num_addons, avg_monthly_spend, auto_pay, billing_pattern), Logistic Regression and Random Forest, accuracy, precision, recall, F1, ROC-AUC, confusion matrix, risk scores
- `sql/churn_queries.sql`: MySQL 8 schema plus joins, CTEs, aggregations and a window function for tenure, contract, billing and service segments
- `churn_dashboard.html`: churn rate by segment, revenue lost and at risk, drivers, model comparison
- `outputs/`: dashboard_data.json, churn_risk_scores.csv

## Power BI
Load `telco_churn_clean.csv` and `churn_risk_scores.csv` from `churn_project_output`, then add DAX measures:

    Churn Rate = AVERAGE(telco_churn_clean[Churn])
    Churned Customers = CALCULATE(COUNTROWS(telco_churn_clean), telco_churn_clean[Churn] = 1)
    Revenue Lost = CALCULATE(SUM(telco_churn_clean[MonthlyCharges]), telco_churn_clean[Churn] = 1)
    Revenue At Risk = CALCULATE(SUM(churn_risk_scores[MonthlyCharges]), churn_risk_scores[risk_band] = "High")
    Churn Rate vs Overall = [Churn Rate] - CALCULATE([Churn Rate], ALL(telco_churn_clean))

Note: the bundled dataset is synthetic (same schema as the public Telco Customer Churn data), so replace it with the real file before quoting numbers.
