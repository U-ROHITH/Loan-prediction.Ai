"""
Loan Prediction AI — Loan Approval Model Training
Dataset: Loan Dataset.csv (52,000 rows, 26 features)
Model:   XGBoost via sklearn Pipeline
"""

import pandas as pd
import numpy as np
import joblib
import os
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.metrics import (classification_report, confusion_matrix,
                             ConfusionMatrixDisplay, roc_auc_score, accuracy_score)
from xgboost import XGBClassifier
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# ── Paths ─────────────────────────────────────────────
BASE   = os.path.dirname(os.path.abspath(__file__))
CSV    = os.path.join(BASE, 'Loan Dataset.csv')
PLOT   = os.path.join(BASE, '..', 'static', 'loan_app', 'plots')
MODEL  = os.path.join(BASE, 'loan_pipeline.pkl')

os.makedirs(PLOT, exist_ok=True)

# ── Load ──────────────────────────────────────────────
df = pd.read_csv(CSV)
print(f"Loaded: {df.shape[0]:,} rows × {df.shape[1]} cols")

# Drop leakage / ID columns
df = df.drop(columns=['Applicant_ID', 'Interest_Rate', 'Default_Risk'])

TARGET = 'Loan_Approval_Status'
X = df.drop(columns=[TARGET])
y = df[TARGET]

print(f"Approved: {y.sum():,} ({y.mean()*100:.1f}%)  |  Rejected: {(y==0).sum():,} ({(y==0).mean()*100:.1f}%)")

# ── Feature groups ────────────────────────────────────
CAT_FEATURES = [
    'Gender', 'Marital_Status', 'Education', 'Employment_Status',
    'Occupation_Type', 'Residential_Status', 'City/Town',
    'Loan_Purpose', 'Loan_Type', 'Co-Applicant'
]
NUM_FEATURES = [
    'Age', 'Dependents', 'Annual_Income', 'Monthly_Expenses',
    'Credit_Score', 'Existing_Loans', 'Total_Existing_Loan_Amount',
    'Outstanding_Debt', 'Loan_History', 'Loan_Amount_Requested',
    'Loan_Term', 'Bank_Account_History', 'Transaction_Frequency'
]

# ── Preprocessor ─────────────────────────────────────
preprocessor = ColumnTransformer([
    ('num', StandardScaler(),                               NUM_FEATURES),
    ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), CAT_FEATURES),
])

# ── Model ─────────────────────────────────────────────
xgb = XGBClassifier(
    n_estimators=300,
    max_depth=6,
    learning_rate=0.1,
    subsample=0.8,
    colsample_bytree=0.8,
    eval_metric='logloss',
    random_state=42,
    n_jobs=-1,
)

pipeline = Pipeline([
    ('preprocessor', preprocessor),
    ('model', xgb),
])

# ── Train / Test split ────────────────────────────────
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
print(f"Train: {len(X_train):,}  |  Test: {len(X_test):,}")

# ── Fit ───────────────────────────────────────────────
print("Training XGBoost pipeline...")
pipeline.fit(X_train, y_train)
print("Done.")

# ── Evaluate ──────────────────────────────────────────
y_pred      = pipeline.predict(X_test)
y_proba     = pipeline.predict_proba(X_test)[:, 1]
accuracy    = accuracy_score(y_test, y_pred)
auc         = roc_auc_score(y_test, y_proba)

print(f"\n{'='*40}")
print(f"  Accuracy : {accuracy*100:.2f}%")
print(f"  ROC-AUC  : {auc:.4f}")
print(f"{'='*40}")
print(classification_report(y_test, y_pred, target_names=['Rejected','Approved']))

# ── Confusion Matrix plot ─────────────────────────────
fig, ax = plt.subplots(figsize=(5, 4))
cm = confusion_matrix(y_test, y_pred)
ConfusionMatrixDisplay(cm, display_labels=['Rejected', 'Approved']).plot(ax=ax, colorbar=False)
ax.set_title(f'Confusion Matrix  (Accuracy {accuracy*100:.1f}%)', fontsize=11)
plt.tight_layout()
plt.savefig(os.path.join(PLOT, 'confusion_matrix.png'), dpi=120)
plt.close()
print(f"Confusion matrix saved.")

# ── Feature Importance plot ───────────────────────────
ohe_cats = pipeline.named_steps['preprocessor'] \
              .named_transformers_['cat'] \
              .get_feature_names_out(CAT_FEATURES)
all_feature_names = NUM_FEATURES + list(ohe_cats)

importances = pipeline.named_steps['model'].feature_importances_
feat_df = pd.DataFrame({'feature': all_feature_names, 'importance': importances})
feat_df = feat_df.sort_values('importance', ascending=True).tail(15)

fig, ax = plt.subplots(figsize=(7, 5))
bars = ax.barh(feat_df['feature'], feat_df['importance'], color='#0d2137')
ax.set_xlabel('Feature Importance (gain)', fontsize=10)
ax.set_title('Top 15 Features — XGBoost', fontsize=11)
plt.tight_layout()
plt.savefig(os.path.join(PLOT, 'feature_importance.png'), dpi=120)
plt.close()
print("Feature importance plot saved.")

# ── Save pipeline ─────────────────────────────────────
joblib.dump(pipeline, MODEL)
print(f"Pipeline saved → {MODEL}")
print("\nTraining complete.")
