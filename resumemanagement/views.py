from django.shortcuts import render, redirect
from django.contrib import messages
import os
from utils import parse_resume_pdf, extract_resume_data, filter_jobs, rank_sort_jobs
from .models import Candidate, RecommendedJob
from jobs.models import Job  # Replace with your actual job model import


def recommend_jobs_view(request):
    if not request.user.is_authenticated:
        return redirect('user:login')

    try:
        candidate = request.user.candidate
    except Candidate.DoesNotExist:
        messages.error(request, "Candidate profile not found.")
        return redirect('user:profile')

    resume_file_path = candidate.resume.path

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        messages.error(request, "API key is not set.")
        return redirect('user:profile')

    resume_text = parse_resume_pdf(resume_file_path)
    if not resume_text:
        messages.error(request, "Failed to parse resume.")
        return redirect('user:profile')

    resume_data = extract_resume_data(resume_text, api_key)

    jobs = Job.objects.all()

    # Filter and rank
    filtered_jobs = filter_jobs(resume_data, jobs)
    ranked_jobs = rank_sort_jobs(resume_data, filtered_jobs, api_key)

    for job in ranked_jobs:
        RecommendedJob.objects.create(
            candidate=candidate,
            job_id=job['job_id'],
            score=job['score']
        )

    return render(request, "candidate/recommended_jobs.html", {"ranked_jobs": ranked_jobs})
