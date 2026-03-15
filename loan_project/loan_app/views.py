import os
import logging
import joblib
import pandas as pd
from django.shortcuts import render
from .models import LoanApplication

logger = logging.getLogger('loan_app')

# ── Load pipeline once at startup ─────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_pipeline_path = os.path.join(BASE_DIR, 'ml_model', 'loan_pipeline.pkl')

try:
    pipeline = joblib.load(_pipeline_path)
    logger.info('ML pipeline loaded successfully.')
except Exception as e:
    pipeline = None
    logger.error(f'Failed to load ML pipeline: {e}')

# ── Constants ─────────────────────────────────────────
INTEREST_RATES = {
    'Home':      8.75,
    'Vehicle':   9.5,
    'Education': 8.5,
    'Personal':  12.0,
}

PURPOSE_LABELS = {
    'Home':      'Home Loan',
    'Vehicle':   'Vehicle Loan',
    'Education': 'Education Loan',
    'Personal':  'Personal Loan',
}

VALID_GENDERS      = {'Male', 'Female'}
VALID_MARITAL      = {'Married', 'Single', 'Divorced'}
VALID_EDUCATION    = {'High School', 'Graduate', 'Postgraduate'}
VALID_EMPLOYMENT   = {'Employed', 'Self-Employed', 'Unemployed'}
VALID_OCCUPATION   = {'Salaried', 'Professional', 'Business', 'Freelancer'}
VALID_RESIDENCE    = {'Own', 'Rent', 'Other'}
VALID_CITY         = {'Urban', 'Suburban', 'Rural'}
VALID_PURPOSE      = set(INTEREST_RATES.keys())
VALID_LOAN_TYPE    = {'Secured', 'Unsecured'}
VALID_CO_APPLICANT = {'Yes', 'No'}


def calculate_emi(principal, annual_rate, tenure_months):
    r = annual_rate / 12 / 100
    if r == 0:
        return round(principal / tenure_months, 2)
    emi = principal * r * (1 + r) ** tenure_months / ((1 + r) ** tenure_months - 1)
    return round(emi, 2)


def get_rejection_reasons(d):
    reasons = []
    if d['Credit_Score'] < 550:
        reasons.append(f"Credit score of {int(d['Credit_Score'])} is below our minimum threshold of 550.")
    if d['Loan_Amount_Requested'] > d['Annual_Income'] * 3:
        reasons.append("Requested loan amount exceeds 3× your annual income.")
    if d['Outstanding_Debt'] > d['Annual_Income'] * 0.5:
        reasons.append("Outstanding debt exceeds 50% of your annual income.")
    if d['Employment_Status'] == 'Unemployed':
        reasons.append("Stable employment is required for loan approval.")
    if d['Loan_History'] == 1:
        reasons.append("Previous loan default history affects eligibility.")
    if d['Monthly_Expenses'] > (d['Annual_Income'] / 12) * 0.75:
        reasons.append("Monthly expenses are too high relative to your income.")
    if not reasons:
        reasons.append("Your overall financial profile did not meet our model's approval criteria.")
    return reasons


def _validate_input(p):
    """Validate and coerce POST data. Returns (data_dict, error_string)."""
    errors = []

    def req(key):
        v = p.get(key, '').strip()
        if not v:
            errors.append(f"'{key}' is required.")
        return v

    def req_int(key, lo=None, hi=None):
        v = req(key)
        try:
            n = int(v)
            if lo is not None and n < lo:
                errors.append(f"'{key}' must be at least {lo}.")
            if hi is not None and n > hi:
                errors.append(f"'{key}' must be at most {hi}.")
            return n
        except (ValueError, TypeError):
            if v:
                errors.append(f"'{key}' must be a whole number.")
            return None

    def req_float(key, lo=None):
        v = req(key)
        try:
            n = float(v)
            if lo is not None and n < lo:
                errors.append(f"'{key}' must be at least {lo}.")
            return n
        except (ValueError, TypeError):
            if v:
                errors.append(f"'{key}' must be a number.")
            return None

    def req_choice(key, valid_set):
        v = req(key)
        if v and v not in valid_set:
            errors.append(f"'{key}' has an invalid value.")
        return v

    data = {
        'full_name':                    req('full_name'),
        'Gender':                       req_choice('gender', VALID_GENDERS),
        'Age':                          req_int('age', 18, 70),
        'Marital_Status':               req_choice('marital_status', VALID_MARITAL),
        'Dependents':                   req_int('dependents', 0, 3),
        'Education':                    req_choice('education', VALID_EDUCATION),
        'Employment_Status':            req_choice('employment_status', VALID_EMPLOYMENT),
        'Occupation_Type':              req_choice('occupation_type', VALID_OCCUPATION),
        'Residential_Status':           req_choice('residential_status', VALID_RESIDENCE),
        'City/Town':                    req_choice('city_town', VALID_CITY),
        'Annual_Income':                req_float('annual_income', 0),
        'Monthly_Expenses':             req_float('monthly_expenses', 0),
        'Credit_Score':                 req_int('credit_score', 300, 849),
        'Existing_Loans':               req_int('existing_loans', 0, 2),
        'Total_Existing_Loan_Amount':   req_float('total_existing_loan_amount', 0),
        'Outstanding_Debt':             req_float('outstanding_debt', 0),
        'Loan_History':                 req_int('loan_history', 0, 1),
        'Bank_Account_History':         req_int('bank_account_history', 0, 9),
        'Transaction_Frequency':        req_int('transaction_frequency', 5, 29),
        'Loan_Amount_Requested':        req_float('loan_amount', 1000),
        'Loan_Term':                    req_int('loan_term', 12, 240),
        'Loan_Purpose':                 req_choice('loan_purpose', VALID_PURPOSE),
        'Loan_Type':                    req_choice('loan_type', VALID_LOAN_TYPE),
        'Co-Applicant':                 req_choice('co_applicant', VALID_CO_APPLICANT),
    }

    if errors:
        return None, ' | '.join(errors[:3])  # show first 3
    return data, None


def home(request):
    return render(request, 'loan_app/home.html')


def apply(request):
    return render(request, 'loan_app/apply.html')


def predict(request):
    if request.method != 'POST':
        return render(request, 'loan_app/apply.html')

    if pipeline is None:
        return render(request, 'loan_app/apply.html',
                      {'error': 'Prediction service is temporarily unavailable. Please try again later.'})

    data, err = _validate_input(request.POST)
    if err:
        return render(request, 'loan_app/apply.html', {'error': err})

    try:
        full_name   = data.pop('full_name')
        purpose     = data['Loan_Purpose']
        loan_amount = data['Loan_Amount_Requested']
        loan_term   = data['Loan_Term']

        df_input   = pd.DataFrame([data])
        raw_score  = float(pipeline.predict_proba(df_input)[0][1])
        prediction = 1 if raw_score >= 0.5 else 0
        confidence = round(raw_score * 100 if prediction == 1 else (1 - raw_score) * 100, 1)

        interest_rate  = INTEREST_RATES.get(purpose, 12.0)
        emi = total_payable = total_interest = None
        if prediction == 1:
            emi            = calculate_emi(loan_amount, interest_rate, loan_term)
            total_payable  = round(emi * loan_term, 2)
            total_interest = round(total_payable - loan_amount, 2)

        rejection_reasons = get_rejection_reasons(data) if prediction == 0 else []

        LoanApplication.objects.create(
            full_name=full_name,
            age=data['Age'],
            gender=data['Gender'],
            marital_status=data['Marital_Status'],
            dependents=data['Dependents'],
            education=data['Education'],
            employment_status=data['Employment_Status'],
            occupation_type=data['Occupation_Type'],
            residential_status=data['Residential_Status'],
            city_town=data['City/Town'],
            annual_income=data['Annual_Income'],
            monthly_expenses=data['Monthly_Expenses'],
            credit_score=data['Credit_Score'],
            existing_loans=data['Existing_Loans'],
            total_existing_loan_amount=data['Total_Existing_Loan_Amount'],
            outstanding_debt=data['Outstanding_Debt'],
            loan_history=bool(data['Loan_History']),
            bank_account_history=data['Bank_Account_History'],
            transaction_frequency=data['Transaction_Frequency'],
            loan_amount=loan_amount,
            loan_term=loan_term,
            loan_purpose=purpose,
            loan_type=data['Loan_Type'],
            co_applicant=data['Co-Applicant'] == 'Yes',
            prediction=bool(prediction),
            confidence=confidence,
            emi=emi,
        )
        logger.info(f'Application submitted: {full_name} — {"Approved" if prediction else "Rejected"} ({confidence}%)')

        return render(request, 'loan_app/result.html', {
            'full_name':         full_name,
            'prediction':        prediction,
            'confidence':        confidence,
            'emi':               emi,
            'total_payable':     total_payable,
            'total_interest':    total_interest,
            'interest_rate':     interest_rate,
            'loan_amount':       loan_amount,
            'loan_term':         loan_term,
            'loan_purpose':      purpose,
            'purpose_label':     PURPOSE_LABELS.get(purpose, 'Loan'),
            'rejection_reasons': rejection_reasons,
        })

    except Exception as e:
        logger.exception(f'Prediction error: {e}')
        return render(request, 'loan_app/apply.html',
                      {'error': 'An unexpected error occurred. Please try again.'})


def error_404(request, exception):
    return render(request, 'loan_app/404.html', status=404)


def error_500(request):
    return render(request, 'loan_app/500.html', status=500)
