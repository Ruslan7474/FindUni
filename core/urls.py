from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('how-to-apply/', views.how_to_apply, name='how-to-apply'),
    path('error/401/', views.unauthorized, name='error-401'),
    path('error/502/', views.bad_gateway, name='error-502'),
    path('service-unavailable/', views.service_unavailable, name='service-unavailable'),
    path('language/<str:language>/', views.language_switch, name='language-switch'),
    path('theme/<str:theme>/', views.theme_switch, name='theme-switch'),
    path('large-text/', views.large_text_switch, name='large-text-switch'),
    path('accessibility/<str:setting>/<str:value>/', views.accessibility_switch, name='accessibility-switch'),
    path('inbox/mark-read/', views.mark_inbox_read, name='inbox-mark-read'),
    path('inbox/<int:pk>/mark-read/', views.mark_notification_read, name='notification-mark-read'),
    path('inbox/delete-all/', views.delete_inbox, name='inbox-delete-all'),
    path('inbox/<int:pk>/delete/', views.delete_notification, name='notification-delete'),
]
