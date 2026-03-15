from django.contrib import admin
from .models import LoanApplication


@admin.register(LoanApplication)
class LoanApplicationAdmin(admin.ModelAdmin):
    list_display  = ('full_name', 'loan_purpose', 'loan_amount', 'prediction_badge',
                     'confidence', 'applied_at')
    list_filter   = ('prediction', 'loan_purpose', 'employment_status',
                     'residential_status', 'gender')
    search_fields = ('full_name',)
    readonly_fields = ('applied_at', 'confidence', 'prediction', 'emi')
    ordering      = ('-applied_at',)

    def prediction_badge(self, obj):
        if obj.prediction:
            return '✅ Approved'
        return '❌ Rejected'
    prediction_badge.short_description = 'Decision'
