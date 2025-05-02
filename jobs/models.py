from django.db import models 
from user.models import User,Candidate

# class Job(models.Model): 
#     JOB_TYPE_CHOICES= [
#         ('Onsite','Onsite'),
#         ('WorkFromHome','WorkFromHome'),
#         ('Hybrid','Hybrid')
#     ]
#     recruiter_id = models.ForeignKey(User, on_delete=models.CASCADE)
#     job_desc = models.TextField() 
#     skills_required = models.TextField() 
#     location = models.CharField(max_length=100) 
#     salary = models.DecimalField(max_digits=7, decimal_places=2)
#     job_type = models.CharField(max_length=15, choices=JOB_TYPE_CHOICES)
#     created_at = models.DateTimeField(auto_now_add=True) 
#     updated_at = models.DateTimeField(auto_now=True)
    
class Job(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    skills_required = models.TextField()
    location = models.CharField(max_length=255)
    min_experience = models.FloatField()
    job_type = models.CharField(max_length=50)
    required_skills = models.TextField() 
    salary = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.title 
    
class JobApplication(models.Model):
    STATUS_CHOICE=[
        ('Not_applied','Not_applied'),
        ('Apply','Apply'),
        ('Save_for_later','Save_for_later'),
        ('Ignore','Ignore'),
    ]
    job_id = models.ForeignKey(Job, on_delete=models.CASCADE)
    candidate_job_app_id = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    status = models.CharField(max_length=15, choices=STATUS_CHOICE)
    applied_at = models.DateTimeField(auto_now_add=True) 
    updated_at = models.DateTimeField(auto_now_add=True) 

    def __str__(self):
        return f"{self.candidate_job_app_id} - {self.job_id} - {self.status}"

from django.db import models

class ResumeData(models.Model):
    skills = models.JSONField(default=list) 
    location = models.CharField(max_length=255, null=True, blank=True)  
    experience = models.CharField(max_length=255, null=True, blank=True)  
    raw_text = models.TextField()  

    def __str__(self):
        return f"ResumeData - {self.location or 'No Location'}"
