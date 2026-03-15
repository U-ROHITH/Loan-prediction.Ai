from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class LoanApplication(models.Model):
    GENDER_CHOICES       = [('Male', 'Male'), ('Female', 'Female')]
    MARITAL_CHOICES      = [('Married', 'Married'), ('Single', 'Single'), ('Divorced', 'Divorced')]
    EDUCATION_CHOICES    = [('High School', 'High School'), ('Graduate', 'Graduate'), ('Postgraduate', 'Postgraduate')]
    EMPLOYMENT_CHOICES   = [('Employed', 'Employed'), ('Self-Employed', 'Self-Employed'), ('Unemployed', 'Unemployed')]
    OCCUPATION_CHOICES   = [('Salaried', 'Salaried'), ('Professional', 'Professional'), ('Business', 'Business'), ('Freelancer', 'Freelancer')]
    RESIDENTIAL_CHOICES  = [('Own', 'Own'), ('Rent', 'Rent'), ('Other', 'Other')]
    CITY_CHOICES         = [('Urban', 'Urban'), ('Suburban', 'Suburban'), ('Rural', 'Rural')]
    PURPOSE_CHOICES      = [('Home', 'Home'), ('Vehicle', 'Vehicle'), ('Education', 'Education'), ('Personal', 'Personal')]
    LOAN_TYPE_CHOICES    = [('Secured', 'Secured'), ('Unsecured', 'Unsecured')]

    # Personal
    full_name   = models.CharField(max_length=100)
    age         = models.IntegerField(validators=[MinValueValidator(18), MaxValueValidator(70)])
    gender      = models.CharField(max_length=10, choices=GENDER_CHOICES)
    marital_status  = models.CharField(max_length=20, choices=MARITAL_CHOICES)
    dependents  = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(3)])
    education   = models.CharField(max_length=30, choices=EDUCATION_CHOICES)

    # Employment
    employment_status  = models.CharField(max_length=20, choices=EMPLOYMENT_CHOICES)
    occupation_type    = models.CharField(max_length=30, choices=OCCUPATION_CHOICES)
    residential_status = models.CharField(max_length=20, choices=RESIDENTIAL_CHOICES)
    city_town          = models.CharField(max_length=20, choices=CITY_CHOICES)

    # Financial
    annual_income               = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    monthly_expenses            = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    credit_score                = models.IntegerField(validators=[MinValueValidator(300), MaxValueValidator(849)])
    existing_loans              = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(2)])
    total_existing_loan_amount  = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    outstanding_debt            = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    loan_history                = models.BooleanField(default=False)
    bank_account_history        = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(9)])
    transaction_frequency       = models.IntegerField(validators=[MinValueValidator(5), MaxValueValidator(29)])

    # Loan
    loan_amount  = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(1000)])
    loan_term    = models.IntegerField(validators=[MinValueValidator(12), MaxValueValidator(240)])
    loan_purpose = models.CharField(max_length=20, choices=PURPOSE_CHOICES)
    loan_type    = models.CharField(max_length=20, choices=LOAN_TYPE_CHOICES)
    co_applicant = models.BooleanField(default=False)

    # Result
    prediction  = models.BooleanField()
    confidence  = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    emi         = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    applied_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-applied_at']
        verbose_name = 'Loan Application'
        verbose_name_plural = 'Loan Applications'

    def __str__(self):
        status = 'Approved' if self.prediction else 'Rejected'
        return f"{self.full_name} — {status} ({self.applied_at.strftime('%d %b %Y')})"
