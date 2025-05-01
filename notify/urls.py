from django.urls import path
from . import views

app_name = 'notify'

urlpatterns = [
    path('resume_format/', views.resume_format, name='resume_format'),
    path('success_stories/', views.success_stories, name='success_stories'),
    path('top_jobs/', views.top_jobs, name='top_jobs'),
    path('cover_letter/', views.cover_letter, name='cover_letter'),
    path('messages_display/', views.messages_display, name='messages_display'),

]