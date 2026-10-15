from django.urls import path
from . import views

urlpatterns = [
    path('submit/', views.submit_application, name='submit-application'),
    path('program/<int:pk>/documents/', views.program_document_requirements_json, name='program-document-requirements-json'),
    path('dashboard/', views.application_dashboard, name='application-dashboard'),
    path('<int:pk>/', views.application_detail, name='application-detail'),
    path('documents/<int:pk>/', views.download_application_document, name='application-document-download'),
    path('<int:pk>/status/', views.update_application_status, name='update-application-status'),
]
