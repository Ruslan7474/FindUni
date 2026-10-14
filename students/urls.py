from django.urls import path
from . import views

urlpatterns = [
    path('', views.student_list, name='student-list'),
    path('<int:pk>/', views.student_detail, name='student-detail'),
    path('profile/', views.profile, name='student-profile'),
    path('profile/edit/', views.edit_profile, name='edit-profile'),
    path('<int:pk>/friend/', views.manage_friend, name='manage-friend'),
    path('comments/<int:comment_pk>/vote/', views.vote_comment, name='vote-comment'),
    path('<int:pk>/comment/', views.add_comment, name='add-comment'),
]
