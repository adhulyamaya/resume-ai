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

def create_job(request):
    if request.method == "POST":
        # Ensure user is authenticated
        if not request.session.get("user_id"):
            messages.error(request, "You must be logged in to create a job.")
            return redirect("user:login")

        # Get the data from the POST request
        title = request.POST.get("title")
        description = request.POST.get("description")
        skills_required = request.POST.get("skills_required")
        location = request.POST.get("location")
        min_experience = request.POST.get("min_experience")
        job_type = request.POST.get("job_type")
        salary = request.POST.get("salary")

        try:
            Job.objects.create(
                title=title,
                description=description,
                skills_required=skills_required,
                location=location,
                min_experience=min_experience or 0,  # default to 0 if empty
                job_type=job_type,
                salary=salary or 0  # default to 0 if empty
            )
            messages.success(request, "Job created successfully!")
        except Exception as e:
            messages.error(request, f"Error creating job: {e}")

        return redirect("jobs:job_list")

    return redirect("jobs:job_list")


# def create_job(request):
  
#     if request.method == "POST":
#         # Ensure recruiter is logged in
#         if not request.user.is_authenticated:
#             messages.error(request, "You must be a recruiter to create a job.")
#             return redirect("user:login")

#         # Get the data from the POST request
#         job_desc = request.POST.get("job_desc")
#         skills_required = request.POST.get("skills_required")
#         location = request.POST.get("location")
#         salary = request.POST.get("salary")
#         job_type = request.POST.get("job_type")

#         try:
#             Job.objects.create(
#                 recruiter_id=request.user,
#                 job_desc=job_desc,
#                 skills_required=skills_required,
#                 location=location,
#                 salary=salary,
#                 job_type=job_type
#             )
#             messages.success(request, "Job created successfully!")
#         except Exception as e:
#             messages.error(request, f"Error creating job: {e}")

#         return redirect("jobs:job_list")  

#     return redirect("jobs:job_list") 

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
        # Fetch the candidate by user_id
        candidate = Candidate.objects.get(user_id=user_id)  
        
        # Now access the related user object (User model)
        print(f"DEBUG: Candidate found: {candidate.user_id.email}")  # Accessing the email of the related User model

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

        for job in filtered_jobs:
            print(f"Ranking job: {job.title}")
            score = rank_job(resume_data, job, api_key)
            print(f"Score for job '{job.title}': {score}")
            ranked_jobs.append({
                "job_id": job.id,
                "job_title": job.title,
                "score": score,
            })

        ranked_jobs.sort(key=lambda x: x['score'], reverse=True)
        print(f"Ranked jobs sorted: {ranked_jobs}")

        return render(request, 'candidate_home.html', {'matched_jobs': ranked_jobs})

    except Candidate.DoesNotExist:
        print("Error: Candidate not found")
        return JsonResponse({'error': 'Candidate not found'}, status=404)
