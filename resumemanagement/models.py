from django.db import models 
from user.models import Candidate,Organization

class ResumeAnalysis(models.Model): 
    recruiter_id = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    missing_keywords = models.TextField() 
    suggestions = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True) 
    updated_at = models.DateTimeField(auto_now_add=True) 


class ResumeShortlisting(models.Model):
    RESUME_STATUS_CHOICE=[
        ('Selected','Selected'),
        ('OnHold','OnHold'),
        ('Rejected','Rejected')
    ]
    hr_id = models.ForeignKey(Organization, on_delete=models.CASCADE)
    resume_status = models.CharField(max_length=8, choices=RESUME_STATUS_CHOICE)
    created_at = models.DateTimeField(auto_now_add=True) 
    updated_at = models.DateTimeField(auto_now_add=True) 