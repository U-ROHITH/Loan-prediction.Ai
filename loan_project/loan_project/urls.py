from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('loan_app.urls')),
]

handler404 = 'loan_app.views.error_404'
handler500 = 'loan_app.views.error_500'
