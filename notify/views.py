from django.shortcuts import render,redirect
from .models import JobAlert 

def messages_display(request):
    candidate = request.user  
    print("Logged-in user:", candidate)

    job_alerts = JobAlert.objects.filter(cand_id=candidate).select_related('job_alert_id').order_by('-created_at')
    print("Number of job alerts:", job_alerts.count())

    for alert in job_alerts:
        print("Alert -> Job Title:", alert.job_alert_id.title)
        print("Company:", alert.job_alert_id.company_name)
        print("Created at:", alert.created_at)

    context = {
        'user': candidate,
        'job_alerts': job_alerts,
    }
    return render(request, 'candidate_home.html', context)


def resume_format(request):
    return render(request, "resume.html")

def top_jobs(request):
    return render(request, "top_jobs.html")

def success_stories(request):
    return render(request, "success_stories.html")

def cover_letter(request):
    return render(request, "cover_letter.html")
