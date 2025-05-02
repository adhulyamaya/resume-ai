from django.shortcuts import render,redirect
from .models import JobAlert 
from django.shortcuts import get_object_or_404
from user.models import Candidate

from django.shortcuts import get_object_or_404, render
from django.http import JsonResponse
from .models import Candidate, JobAlert
from user.models import User


def messages_display(request):
    user_id = request.session.get("user_id")
    print(f"User ID from session: {user_id}")

    if not user_id:
        return JsonResponse({'error': 'You must be logged in to view job alerts.'}, status=400)

    user = get_object_or_404(User, id=user_id)
    print("Logged-in user:", user)

    candidate = get_object_or_404(Candidate, user_id=user)
    print("Candidate ID:", candidate.id)

    job_alerts = JobAlert.objects.filter(cand_id=candidate).select_related('job_alert_id').order_by('-created_at')
    print("Number of job alerts:", job_alerts.count())

    for alert in job_alerts:
        print("Alert -> Job Title:", alert.job_alert_id.title)
        print("Created at:", alert.created_at)

    context = {
        'user': user,
        'job_alerts': job_alerts,
    }
    return render(request, 'message_list.html', context)


# def messages_display(request):
#     user = request.user
#     print("Logged-in user:", user)

#     # Get the Candidate instance for the logged-in user
#     candidate = get_object_or_404(Candidate, user_id=request.user.id)

#     print("Candidate ID:", candidate.id)

#     job_alerts = JobAlert.objects.filter(cand_id=candidate).select_related('job_alert_id').order_by('-created_at')
#     print("Number of job alerts:", job_alerts.count())

#     for alert in job_alerts:
#         print("Alert -> Job Title:", alert.job_alert_id.title)
#         # print("Company:", alert.job_alert_id.company_name)
#         print("Created at:", alert.created_at)

#     context = {
#         'user': user,
#         'job_alerts': job_alerts,
#     }
#     return render(request, 'message_list.html', context)


def resume_format(request):
    return render(request, "resume.html")

def top_jobs(request):
    return render(request, "top_jobs.html")

def success_stories(request):
    return render(request, "success_stories.html")

def cover_letter(request):
    return render(request, "cover_letter.html")
