from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Job
import re
import json
import fitz
from groq import Groq
from operator import itemgetter
from .models import ResumeData,Job
from user.views import extract_resume_data, parse_resume_pdf

from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Candidate, Job
from .utils import  extract_resume_data, filter_jobs, rank_job
from django.shortcuts import redirect
from django.contrib import messages
from .models import Job
from notify.models import JobAlert
from django.db.models import Q
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from .models import Candidate, Job, JobApplication
from django.http import JsonResponse
from user.models import User


def create_job(request):
    if request.method == "POST":
        if not request.session.get("user_id"):
            messages.error(request, "You must be logged in to create a job.")
            print("User not logged in, redirecting to login.")
            return redirect("user:login")

        title = request.POST.get("title")
        description = request.POST.get("description")
        skills_required = request.POST.get("skills_required")
        location = request.POST.get("location")
        min_experience = request.POST.get("min_experience")
        job_type = request.POST.get("job_type")
        salary = request.POST.get("salary")

        print(f"Received job details: {title}, {description}, {skills_required}, {location}, {min_experience}, {job_type}, {salary}")

        try:
            job = Job.objects.create(
                title=title,
                description=description,
                skills_required=skills_required,
                location=location,
                min_experience=min_experience or 0,
                job_type=job_type,
                salary=salary or 0
            )

            print(f"Job created successfully: {job.title} - {job.id}")

            # Create job alerts for all candidates
            for candidate in Candidate.objects.all():
                print(f"Creating job alert for candidate: {candidate.user_id}")
                JobAlert.objects.create(
                    cand_id=candidate,
                    job_alert_id=job
                )

            messages.success(request, "Job created and alerts sent to candidates!")
            print("Job alerts sent to all candidates.")

        except Exception as e:
            messages.error(request, f"Error creating job: {e}")
            print(f"Error occurred: {e}")

        return redirect("jobs:job_list")

    print("Request method is not POST, redirecting to job list.")
    return redirect("jobs:job_list")


def search_jobs(request):
    query = request.GET.get('query', '')
    location = request.GET.get('location', '')
    job_type = request.GET.get('job_type', '')
    jobs = Job.objects.all()

    if query:
        jobs = jobs.filter(Q(title__icontains=query) | Q(description__icontains=query))

    if location:
        jobs = jobs.filter(location__icontains=location)

    if job_type:
        jobs = jobs.filter(job_type__icontains=job_type)

    return render(request, 'jobs/job_list.html', {'jobs': jobs})


def apply(request, job_id):
    if request.method == "POST":
        user_id = request.session.get("user_id")
        print(f"User ID from session: {user_id}")
        if not user_id:
            return JsonResponse({'error': 'You must be logged in to apply for a job.'}, status=400)

        user = get_object_or_404(User, id=user_id)
        candidate = get_object_or_404(Candidate, user_id=user)
        job = get_object_or_404(Job, id=job_id)

        existing_application = JobApplication.objects.filter(
            candidate_job_app_id=candidate, job_id=job
        ).first()

        if existing_application:
            if existing_application.status == 'Apply':
                return JsonResponse({'message': 'You have already applied for this job.'}, status=200)
            else:
                existing_application.status = 'Apply'
                existing_application.save()
                return JsonResponse({'message': 'Job application updated to "Applied".'}, status=200)
        else:
            JobApplication.objects.create(
                candidate_job_app_id=candidate,
                job_id=job,
                status='Apply'
            )
            return JsonResponse({'message': 'Job application submitted successfully!'}, status=200)

    return JsonResponse({'error': 'Invalid request method.'}, status=400)


def application_status(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return JsonResponse({'error': 'You must be logged in to view applications.'}, status=400)

    user = get_object_or_404(User, id=user_id)
    candidate = get_object_or_404(Candidate, user_id=user)

    applications = JobApplication.objects.filter(candidate_job_app_id=candidate).select_related('job_id')

    application_data = []
    for app in applications:
        application_data.append({
            'job_id': app.job_id.id,
            'job_title': app.job_id.title,
            'status': app.status,
        })

    return render(request, 'user/candidate_home.html', {'applications': application_data},)    


def delete_job(request, job_id):
    if request.method == "POST":
        user_id = request.session.get("user_id")
        user_role = request.session.get("user_role")

        if not user_id or user_role != "recruiter":
            messages.error(request, "You must be logged in as a recruiter to delete this job.")
            return redirect("user:login")

        job = get_object_or_404(Job, id=job_id)

        if job.recruiter_id_id != user_id:
            messages.error(request, "You don't have permission to delete this job.")
            return redirect("jobs:job_list")

        try:
            job.delete()
            messages.success(request, "Job deleted successfully!")
        except Exception as e:
            messages.error(request, f"Error deleting job: {e}")

    return redirect("jobs:job_list")


def job_list(request):
    jobs = Job.objects.all()
    print(f"DEBUG: Jobs fetched: {jobs}")
    return render(request, "jobs/job_management.html", {"jobs": jobs})


def rank_jobs(request):
    user_id = request.session.get("user_id")
    if not user_id:
        messages.error(request, "You must be logged in to access this page.")
        return redirect("user:login")
    try:
        candidate = Candidate.objects.get(user_id=user_id)  
        print(f"DEBUG: Candidate found: {candidate.user_id.email}") 
        
        resume_data = {
            'skills': candidate.extracted_skills,
            'location': candidate.extracted_location,
            'experience': candidate.extracted_experience
        }
        print(f"Resume data extracted: {resume_data}")
        
        jobs = Job.objects.all()
        print(f"Total jobs fetched: {len(jobs)}")
        
        filtered_jobs = filter_jobs(resume_data, jobs)
        print(f"Filtered jobs count: {len(filtered_jobs)}")
        
        api_key = "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"
        ranked_jobs = []
        
        if filtered_jobs:
            for job in filtered_jobs:
                print(f"Ranking job: {job.title}")
                score = rank_job(resume_data, job, api_key)
                print(f"Score for job '{job.title}': {score}")
                ranked_jobs.append({
                    "job_id": job.id,
                    "job_title": job.title,
                    "score": score,
                    "description": job.description[:150] + "..." if len(job.description) > 150 else job.description,
                    "location": job.location,
                    "job_type": job.job_type,
                    "min_experience": job.min_experience,
                })
            ranked_jobs.sort(key=lambda x: x['score'], reverse=True)
        
        print(f"Ranked jobs sorted: {ranked_jobs}")
        return render(request, 'jobs/suggested_jobs.html', {
            'matched_jobs': ranked_jobs,
            'candidate': candidate,
            'total_jobs': len(jobs),
            'filtered_jobs_count': len(filtered_jobs)
        })
    except Candidate.DoesNotExist:
        print("Error: Candidate not found")
        return JsonResponse({'error': 'Candidate not found'}, status=404)
    
    except Exception as e:
        print(f"Error in rank_jobs view: {e}")
        messages.error(request, f"An error occurred: {str(e)}")
        return render(request, 'candidate_home.html', {'error': str(e)})
    


def applied_candidates(request):
    applications = JobApplication.objects.filter(status='Apply').select_related('candidate_job_app_id', 'job_id')
    context = {
        'applications': applications,
    }
    return render(request, 'candidates_applied.html', context)



def candidates_applied(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    applications = JobApplication.objects.filter(job_id=job, status='Apply').select_related('candidate_job_app_id')
    candidates = [app.candidate_job_app_id for app in applications]

    context = {
        'job': job,
        'candidates': candidates
    }

    return render(request, 'candidates_applied.html', context)

