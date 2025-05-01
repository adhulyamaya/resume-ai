from django.urls import path
from . import views

app_name = "jobs"

urlpatterns = [
    path('manage-jobs/', views.job_list, name='job_list'),
    path('create/', views.create_job, name='create_job'),
    path('delete/<int:job_id>/', views.delete_job, name='delete_job'),

    path('rank_job/', views.rank_jobs, name='rank_job'),    
]
