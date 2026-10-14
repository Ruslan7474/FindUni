from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('how-to-apply/', views.how_to_apply, name='how-to-apply'),
    path('language/<str:language>/', views.language_switch, name='language-switch'),
    path('theme/<str:theme>/', views.theme_switch, name='theme-switch'),
    path('large-text/', views.large_text_switch, name='large-text-switch'),
]
