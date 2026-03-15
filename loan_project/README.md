# LoanPredict.AI

An AI-powered loan eligibility prediction platform built with Django and XGBoost. Submit a loan application through a multi-step form and receive an instant decision — approved or rejected — along with a confidence score, EMI breakdown, and actionable rejection reasons.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [ML Model](#ml-model)
- [Local Development Setup](#local-development-setup)
- [Training the Model](#training-the-model)
- [Environment Variables](#environment-variables)
- [Deployment on Render](#deployment-on-render)
- [Admin Dashboard](#admin-dashboard)
- [API / URL Routes](#api--url-routes)
- [Security](#security)

---

## Overview

LoanPredict.AI is a full-stack demonstration platform that simulates a bank's loan eligibility screening system. A user fills out a 4-step application form covering personal, employment, financial, and loan details. The backend runs the input through a trained XGBoost pipeline and returns a real-time prediction.

The project is production-ready: it includes server-side input validation, structured logging, WhiteNoise static serving, CSRF/HSTS/SSL security headers, a Django Admin panel for reviewing all applications, and a `render.yaml` for one-click deployment on Render.

> **Disclaimer:** This is a demonstration project for educational purposes. It does not constitute actual financial advice and is not affiliated with any real financial institution.

---

## Features

**Application Form**
- 4-step guided form (Personal → Employment → Financial → Loan Details)
- Live EMI preview updates as the user types loan amount and term
- Custom JavaScript multi-step validation — no browser HTML5 blocking on hidden steps
- `novalidate` on the form with full client-side step-by-step checks before advancing

**Prediction Engine**
- XGBoost pipeline trained on 52,000 real-world loan applications
- Returns approval/rejection with a confidence percentage
- On approval: monthly EMI, total interest payable, total repayment amount
- On rejection: specific reasons (e.g. low credit score, high debt-to-income ratio) and improvement tips

**Interest Rates by Loan Purpose**

| Loan Type     | Annual Rate |
|---------------|-------------|
| Home          | 8.75%       |
| Vehicle       | 9.50%       |
| Education     | 8.50%       |
| Personal      | 12.00%      |

**Admin Dashboard**
- View all submitted applications with approval badge (✅ / ❌)
- Filter by prediction outcome, loan purpose, employment status, gender, residential status
- Search by applicant name
- Read-only result fields (prediction, confidence, EMI, applied_at)

**Production-Ready**
- WhiteNoise for compressed, cache-busted static file serving
- Environment-based configuration for secrets and allowed hosts
- Full security header stack: HSTS, SSL redirect, CSRF hardening, X-Frame-Options DENY
- Custom branded 404 and 500 error pages
- Structured console logging via Python's `logging` module
- `render.yaml` for zero-config Render deployment

---

## Tech Stack

| Layer       | Technology                                    |
|-------------|-----------------------------------------------|
| Framework   | Django 5.2                                    |
| ML Model    | XGBoost 3.2 via scikit-learn Pipeline         |
| Preprocessing | scikit-learn ColumnTransformer (StandardScaler + OneHotEncoder) |
| Data        | pandas 2.2, numpy 2.1                         |
| Model I/O   | joblib 1.4                                    |
| Web Server  | gunicorn 23.0                                 |
| Static Files | WhiteNoise 6.9 (CompressedManifestStaticFilesStorage) |
| Frontend    | Bootstrap 5.3 (grid/utilities) + custom CSS   |
| Database    | SQLite (dev) / PostgreSQL via DATABASE_URL (prod) |
| Deployment  | Render                                        |

---

## Project Structure

```
loan_project/
├── loan_app/
│   ├── ml_model/
│   │   ├── Loan Dataset.csv          # 52,000-row training dataset
│   │   ├── train_model.py            # Training script
│   │   └── loan_pipeline.pkl         # Serialised XGBoost pipeline (1.3 MB)
│   ├── migrations/
│   │   ├── 0001_initial.py
│   │   └── 0002_alter_loanapplication_options_and_more.py
│   ├── static/loan_app/
│   │   ├── css/style.css             # Full custom design system
│   │   └── js/script.js              # Multi-step form logic + live EMI preview
│   ├── templates/loan_app/
│   │   ├── base.html                 # Navbar, footer, meta/OG tags
│   │   ├── home.html                 # Landing page
│   │   ├── apply.html                # 4-step application form
│   │   ├── result.html               # Decision page
│   │   ├── 404.html
│   │   └── 500.html
│   ├── admin.py                      # LoanApplicationAdmin with badge display
│   ├── apps.py
│   ├── models.py                     # LoanApplication model (23 fields + result)
│   ├── urls.py
│   └── views.py                      # Validation, prediction logic, EMI calculation
├── loan_project/
│   ├── settings.py                   # Environment-based, production-hardened
│   ├── urls.py                       # Root URLs + handler404/500
│   └── wsgi.py
├── manage.py
├── procfile                          # gunicorn start command
├── render.yaml                       # Render deployment config
└── requirements.txt
```

---

## ML Model

### Dataset

- **File:** `Loan Dataset.csv`
- **Size:** 52,000 rows × 26 columns
- **Target:** `Loan_Approval_Status` (0 = Rejected, 1 = Approved)
- **Class balance:** ~64.2% approved / 35.8% rejected

Columns dropped before training to prevent data leakage:
- `Applicant_ID` — unique identifier, no predictive value
- `Interest_Rate` — set after approval decision, not a predictor
- `Default_Risk` — post-hoc risk label derived from the outcome

### Features

**Numerical (13):** Age, Dependents, Annual_Income, Monthly_Expenses, Credit_Score, Existing_Loans, Total_Existing_Loan_Amount, Outstanding_Debt, Loan_History, Loan_Amount_Requested, Loan_Term, Bank_Account_History, Transaction_Frequency

**Categorical (10):** Gender, Marital_Status, Education, Employment_Status, Occupation_Type, Residential_Status, City/Town, Loan_Purpose, Loan_Type, Co-Applicant

### Pipeline

```
ColumnTransformer
  ├── num: StandardScaler          → 13 scaled numerical features
  └── cat: OneHotEncoder           → one-hot encoded categoricals
        (handle_unknown='ignore')
XGBClassifier
  n_estimators=300, max_depth=6, learning_rate=0.1,
  subsample=0.8, colsample_bytree=0.8
```

### Results

| Metric   | Score  |
|----------|--------|
| Accuracy | 85%    |
| ROC-AUC  | 0.82   |

Training generates two plots saved to `static/loan_app/plots/`:
- `confusion_matrix.png`
- `feature_importance.png` (top 15 features by XGBoost gain)

### Prediction Logic

- `predict_proba()` returns the probability of approval (class 1)
- Threshold: `>= 0.50` → Approved
- Confidence shown to user = probability of the predicted class × 100
- EMI formula: `P × r × (1+r)^n / ((1+r)^n − 1)` where `r = annual_rate / 12 / 100`

---

## Local Development Setup

### Prerequisites

- Python 3.10+
- pip

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/your-username/Loan-Prediction-AI.git
cd Loan-Prediction-AI/loan-prediction-fullstack/loan_project

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Apply database migrations
python manage.py migrate

# 5. Collect static files (optional for dev)
python manage.py collectstatic --no-input

# 6. Run the development server
python manage.py runserver
```

Open `http://127.0.0.1:8000` in your browser.

> The app runs in development mode by default (`DEBUG=True`, SQLite database). The pre-trained `loan_pipeline.pkl` is included in the repository — no training step needed to run the app.

---

## Training the Model

Only needed if you want to retrain on the dataset or modify the pipeline.

```bash
cd loan_app/ml_model
python train_model.py
```

This will:
1. Load `Loan Dataset.csv`
2. Drop leakage columns
3. Split 80/20 train/test (stratified)
4. Fit the XGBoost pipeline
5. Print accuracy and AUC to console
6. Save confusion matrix and feature importance plots
7. Overwrite `loan_pipeline.pkl`

> Training on 52,000 rows takes approximately 30–60 seconds on a standard CPU.

---

## Environment Variables

| Variable       | Required in Prod | Description                                                      |
|----------------|-----------------|------------------------------------------------------------------|
| `SECRET_KEY`   | Yes             | Django secret key. Generate with `python -c "import secrets; print(secrets.token_hex(50))"` |
| `DEBUG`        | Yes             | Set to `False` in production                                     |
| `DJANGO_ENV`   | Yes             | Set to `production` to enforce SECRET_KEY requirement            |
| `ALLOWED_HOST` | Yes             | Your primary domain (e.g. `loan-prediction-ai.onrender.com`)    |
| `ALLOWED_HOST_2` | No            | Secondary domain if needed                                       |
| `DATABASE_URL` | No              | PostgreSQL connection string. Falls back to SQLite if not set.   |

In development, no environment variables are required — sensible defaults are applied automatically.

---

## Deployment on Render

The project includes a `render.yaml` for automatic configuration.

### Steps

**1. Push to GitHub**
```bash
git add .
git commit -m "Ready for deployment"
git push origin main
```

**2. Create a Web Service**
- Go to [render.com](https://render.com) → New + → Web Service
- Connect your GitHub repository
- Set **Root Directory** to: `loan-prediction-fullstack/loan_project`

**3. Configure the service**

| Field            | Value                                                                 |
|------------------|-----------------------------------------------------------------------|
| Runtime          | Python 3                                                              |
| Build Command    | `pip install -r requirements.txt && python manage.py migrate --run-syncdb && python manage.py collectstatic --no-input` |
| Start Command    | `gunicorn loan_project.wsgi`                                          |

**4. Set environment variables** (in Render → Environment tab)

| Key          | Value                                  |
|--------------|----------------------------------------|
| `DJANGO_ENV` | `production`                           |
| `DEBUG`      | `False`                                |
| `SECRET_KEY` | *(click Generate for a random value)*  |
| `ALLOWED_HOST` | `your-app-name.onrender.com`         |

**5. Deploy** — Render installs packages, runs migrations, collects static files, and starts gunicorn automatically.

**6. Create a superuser** (Render → Shell tab)
```bash
python manage.py createsuperuser
```

### Notes on Render Free Tier

- **SQLite persistence:** Render's free tier uses an ephemeral filesystem. The SQLite database resets on each redeploy. For persistent storage, add a Render PostgreSQL database (free tier available) and set `DATABASE_URL` — `settings.py` handles this automatically.
- **Cold starts:** Free services spin down after 15 minutes of inactivity. The first request after idle takes ~30 seconds to wake up.
- **Model file:** `loan_pipeline.pkl` (1.3 MB) is committed to Git and deploys with the code — no separate model hosting needed.

---

## Admin Dashboard

Access at `/admin/` after creating a superuser.

Features:
- **List view:** applicant name, loan purpose, loan amount, decision badge, confidence %, application date
- **Filters:** prediction outcome, loan purpose, employment status, residential status, gender
- **Search:** by applicant full name
- **Detail view:** all 23 input fields + read-only result fields (prediction, confidence, EMI, applied_at)

---

## API / URL Routes

| Method | URL        | View       | Description                              |
|--------|------------|------------|------------------------------------------|
| GET    | `/`        | `home`     | Landing page                             |
| GET    | `/apply/`  | `apply`    | 4-step loan application form             |
| POST   | `/predict/`| `predict`  | Validates input, runs model, saves record, returns result page |

Error handlers: `404` → `loan_app/404.html`, `500` → `loan_app/500.html`

---

## Security

The following security measures are active in production (`DEBUG=False`):

| Setting                          | Value         | Purpose                                        |
|----------------------------------|---------------|------------------------------------------------|
| `SECURE_SSL_REDIRECT`            | `True`        | Forces all HTTP traffic to HTTPS               |
| `SECURE_HSTS_SECONDS`            | `31,536,000`  | 1-year HSTS header                             |
| `SECURE_HSTS_INCLUDE_SUBDOMAINS` | `True`        | HSTS applies to all subdomains                 |
| `SECURE_HSTS_PRELOAD`            | `True`        | Eligible for browser HSTS preload list         |
| `CSRF_COOKIE_SECURE`             | `True`        | CSRF cookie sent over HTTPS only               |
| `SESSION_COOKIE_SECURE`          | `True`        | Session cookie sent over HTTPS only            |
| `CSRF_COOKIE_HTTPONLY`           | `True`        | CSRF cookie inaccessible to JavaScript         |
| `CSRF_COOKIE_SAMESITE`           | `Lax`         | Cross-site request restriction                 |
| `SECURE_BROWSER_XSS_FILTER`      | `True`        | Enables browser XSS auditor header             |
| `SECURE_CONTENT_TYPE_NOSNIFF`    | `True`        | Prevents MIME-type sniffing                    |
| `X_FRAME_OPTIONS`                | `DENY`        | Prevents clickjacking via iframes              |

All user input is validated server-side in `_validate_input()` before reaching the model or database, regardless of client-side validation state.
