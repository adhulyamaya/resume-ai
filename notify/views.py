from django.shortcuts import render,redirect

def resume_format(request):
    return render(request, "resume.html")

def top_jobs(request):
    return render(request, "top_jobs.html")

def success_stories(request):
    return render(request, "success_stories.html")

def cover_letter(request):
    return render(request, "cover_letter.html")
