from django.urls import path
from . import views

urlpatterns = [
    path('', views.institution_list, name='institution-list'),
    path('profile/', views.institution_profile, name='institution-profile'),
    path('programs/<int:pk>/documents/', views.program_document_requirements, name='program-document-requirements'),
    path('<int:pk>/follow/', views.toggle_institution_follow, name='toggle-institution-follow'),
    path('<int:pk>/', views.institution_detail, name='institution-detail'),
    path('<int:pk>/reviews/new/', views.add_review, name='add-review'),
    path('<int:pk>/edit/', views.edit_institution, name='edit-institution'),
]
