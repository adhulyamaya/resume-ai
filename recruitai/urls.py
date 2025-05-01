from django.contrib import admin
from django.urls import path,include
from django.views.generic import TemplateView
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='index.html'), name='index'),
    path('user/', include('user.urls')),
    path('notify/', include('notify.urls')),
    path("jobs/", include("jobs.urls")),
    
]

# Serve local resumes during development
if settings.DEBUG:
    urlpatterns += static('/resumes/', document_root=r"D:\ai resume analyzer\recruitai\resume_folder")
