from django.urls import path
from .views import recommend_jobs_view

urlpatterns = [
    path('recommend-jobs/', recommend_jobs_view, name='recommend_jobs'),
]