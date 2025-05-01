from django.db import models 
from user.models import Candidate
from jobs.models import Job

class JobAlert(models.Model): 
    cand_id = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    job_alert_id = models.ForeignKey(Job, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True) 
    updated_at = models.DateTimeField(auto_now_add=True) 
