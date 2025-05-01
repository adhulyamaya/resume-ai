from django.urls import path
from . import views

app_name = 'user'

urlpatterns = [
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('signup/', views.signup_view, name='signup'),
    path('edit_profile/', views.edit_profile, name='edit_profile'),
    path('forgot_password/', views.forgot_password, name='forgot_password'),
    path('candidate_home/', views.candidate_home, name='candidate_home'),
    path('recruiter_home/', views.recruiter_home, name='recruiter_home'),
    path('search-candidates/', views.search_candidates, name='search_candidates'),
    path('candidate-action/<int:candidate_id>/', views.candidate_action, name='candidate_action'),

]



