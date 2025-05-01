from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from .models import User,UserProfile,Candidate,Organization
from django.contrib.auth.decorators import login_required

from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
    
from django.contrib import messages
from .forms import CandidateSearchForm  

import os
from django.conf import settings
import re
import json
import fitz
from groq import Groq
from operator import itemgetter
from jobs.models import ResumeData, Job
from django.core.files.storage import FileSystemStorage


def parse_resume_pdf(file_path: str) -> str:
    """Extract text from a PDF file."""
    try:
        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    except Exception as e:
        print(f"Error parsing PDF: {e}")
        return ""


def extract_resume_data(resume_text: str, api_key: str) -> ResumeData:
    """Extract skills, location, and experience from resume text using Groq LLM."""

    client = Groq(api_key=api_key)
    
    prompt = f"""
    Extract the following information from the resume text and format as JSON:
    1. Skills: A list of technical and soft skills mentioned
    2. Location: Current location or preferred work location if mentioned
    3. Experience: Total years of professional experience if mentioned

    Format the response as a valid JSON object with this exact structure:
    {{
        "skills": ["skill1", "skill2"],
        "location": "location string or null",
        "experience": "experience string or null"
    }}

    Resume text:
    {resume_text}

    Return only the JSON object with no additional text or formatting.
    """
    
    try:
        completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant designed to output JSON."
                },
                {   "role": "user", 
                    "content": prompt
                }
            ],
            model="llama3-70b-8192",
            response_format={"type": "json_object"},
            temperature=0.5,
        )
        
        content = completion.choices[0].message.content
        
        data = json.loads(content)

        return ResumeData(
            skills=data.get("skills", []),
            location=data.get("location"),
            experience=data.get("experience"),
            raw_text=resume_text
        )
            
    except Exception as e:
        print(f"Error calling Groq API (1): {e}")
        return ResumeData(skills=[], location=None, experience=None, raw_text=resume_text)




# Define resume folder settings locally in view (optional if you want to avoid touching settings.py)
RESUME_ROOT = r"D:\ai resume analyzer\recruitai\resume_folder"
RESUME_URL = "/resumes/"  # URL to serve resumes


# Create your views here.
def user_login(request):
    try:
        if request.method == "POST":
            email = request.POST.get("email")
            password = request.POST.get("password")

            # Manually verify user credentials
            try:
                user = User.objects.get(email=email, password=password)
                
                # Store user ID in session
                request.session['user_id'] = user.id
                request.session['user_role'] = user.role  # Store role for easy access
                print('AAAAAAAAAAAAAA')

                if user.role == "candidate":
                    return redirect("user:candidate_home")
                elif user.role == "recruiter":
                    print('BBBBBBBBB')
                    return redirect("user:recruiter_home")
                else:
                    messages.error(request, "Invalid email or password")
            except User.DoesNotExist:
                messages.error(request, "Invalid email or password")

    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
    
    return render(request, "login.html")



def user_logout(request):
    request.session.flush()  # Clears all session data
    messages.success(request, "Logged out successfully!")
    return redirect("user:login")
 


def signup_view(request):
    exp_choices = [
        ('0', '0 years (Fresher)'), ('1', '1 year'), ('2', '2 years'),
        ('3', '3 years'), ('4', '4 years'), ('5', '5 years'),
        ('5-10', '5-10 years'), ('10+', '10+ years')
    ]

    if request.method == "POST":
        print("POST request received.")  # Debugging start of POST request
        
        fullname = request.POST.get("fullname")
        email = request.POST.get("email")
        phone_number = request.POST.get("phone_number")
        password = request.POST.get("password")
        role = request.POST.get("role")
        description = request.POST.get("description", "")
        
        print(f"Received data: fullname={fullname}, email={email}, phone_number={phone_number}, role={role}, description={description}")

        if not role:
            messages.error(request, "Please select a role.")
            print("Role not selected.")
            return render(request, "signup.html", {"exp_choices": exp_choices})

        try:
            print("Creating user...")
            user = User.objects.create(
                username=email, fullname=fullname, email=email,
                password=password, phone_number=phone_number,
                role=role, description=description
            )
            print(f"User created: {user}")
        except Exception as e:
            messages.error(request, f"Error creating user: {e}")
            print(f"Error creating user: {e}")
            return render(request, "signup.html", {"exp_choices": exp_choices})

        if role == "candidate":
            print("Role is candidate. Processing candidate data...")
            resume = request.FILES.get("resume")
            skill = request.POST.get("skill")
            exp = request.POST.get("exp")

            if not resume or not skill or not exp:
                messages.error(request, "Please fill in all Candidate fields.")
                user.delete()
                print("Missing resume, skill, or experience. User deleted.")
                return render(request, "signup.html", {"exp_choices": exp_choices})

            # Save resume file
            fs = FileSystemStorage(location=RESUME_ROOT)
            filename = fs.save(resume.name, resume)
            file_path = fs.path(filename)
            print(f"Resume saved to: {file_path}")

            # Parse and extract resume data
            resume_text = parse_resume_pdf(file_path)
            api_key = settings.GROQ_API_KEY
            print(f"Using API key: {api_key}")
            resume_data = extract_resume_data(resume_text, api_key)
            print(f"Extracted resume data: {resume_data}")

            print(f"Extracted Skills: {resume_data.skills}")
            print(f"Extracted Location: {resume_data.location}")
            print(f"Extracted Experience: {resume_data.experience}")

            try:
                Candidate.objects.create(
                    user_id=user,
                    resume=filename,
                    skill=skill,
                    exp=exp,
                    extracted_skills=resume_data.skills,
                    extracted_location=resume_data.location,
                    extracted_experience=resume_data.experience,
                )
                print("Candidate profile created.")
            except TypeError:
                # If model doesn't support those fields, use only the supported ones
                Candidate.objects.create(
                    user_id=user,
                    resume=filename,
                    skill=skill,
                    exp=exp,  
                )
                print("Candidate profile created without extracted fields.")

        elif role == "recruiter":
            print("Role is recruiter. Processing recruiter data...")
            company_name = request.POST.get("company_name")
            company_email = request.POST.get("company_email")
            address = request.POST.get("address")

            if not company_name or not company_email or not address:
                messages.error(request, "Please fill in all Recruiter fields.")
                user.delete()
                print("Missing company_name, company_email, or address. User deleted.")
                return render(request, "signup.html", {"exp_choices": exp_choices})

            try:
                Organization.objects.create(
                    user_id=user,
                    company_name=company_name,
                    address=address,
                    company_email=company_email,
                )
                print("Recruiter profile created.")
            except Exception as e:
                messages.error(request, f"Error saving recruiter profile: {e}")
                print(f"Error saving recruiter profile: {e}")
                user.delete()
                return render(request, "signup.html", {"exp_choices": exp_choices})

        messages.success(request, "Account created successfully! You can now log in.")
        print("Account created successfully. Redirecting to login.")
        return redirect("user:login")

    print("GET request received.")
    return render(request, "signup.html", {"exp_choices": exp_choices})


# def signup_view(request):
#     exp_choices = [
#         ('0', '0 years (Fresher)'),
#         ('1', '1 year'),
#         ('2', '2 years'),
#         ('3', '3 years'),
#         ('4', '4 years'),
#         ('5', '5 years'),
#         ('5-10', '5-10 years'),
#         ('10+', '10+ years')
#     ]

#     if request.method == "POST":
#         fullname = request.POST.get("fullname")
#         email = request.POST.get("email")
#         phone_number = request.POST.get("phone_number")
#         pass_word = request.POST.get("password")  # plain password
#         role = request.POST.get("role")
#         description = request.POST.get("description", "")
#         print(pass_word)

#         if not role:
#             messages.error(request, "Please select a role.")
#             return render(request, "signup.html", {"exp_choices": exp_choices})

#         try:
#             # Directly store password (not hashed)
#             user = User.objects.create(
#                 username=email,
#                 fullname=fullname,
#                 email=email,
#                 password=pass_word,
#                 phone_number=phone_number,
#                 role=role,
#                 description=description,
#             )
#         except Exception as e:
#             messages.error(request, "Error creating user: " + str(e))
#             return render(request, "signup.html", {"exp_choices": exp_choices})

#         if role == "candidate":
#             resume = request.FILES.get("resume")
#             skill = request.POST.get("skill")
#             exp = request.POST.get("exp")

#             if not resume or not skill or not exp:
#                 messages.error(request, "Please fill in all Candidate fields.")
#                 user.delete()
#                 return render(request, "signup.html", {"exp_choices": exp_choices})

#             Candidate.objects.create(
#                 user_id=user,
#                 resume=resume,
#                 skill=skill,
#                 exp=exp,
#             )
#         elif role == "recruiter":
#             company_name = request.POST.get("company_name")
#             company_email = request.POST.get("company_email")
#             address = request.POST.get("address")

#             if not company_name or not company_email or not address:
#                 messages.error(request, "Please fill in all Recruiter fields.")
#                 user.delete()
#                 return render(request, "signup.html", {"exp_choices": exp_choices})

#             try:
#                 Organization.objects.create(
#                     user_id=user,
#                     company_name=company_name,
#                     address=address,
#                     company_email=company_email,
#                 )
#             except Exception as e:
#                 messages.error(request, "Error saving recruiter profile: " + str(e))
#                 user.delete()
#                 return render(request, "signup.html", {"exp_choices": exp_choices})

#         messages.success(request, "Account created successfully! You can now log in.")
#         return redirect("user:login")

#     return render(request, "signup.html", {"exp_choices": exp_choices})



def forgot_password(request):
    return render(request, "forgot_password.html")


def candidate_home(request):
    user_id = request.session.get('user_id')

    if not user_id:
        messages.error(request, "You must log in first.")
        return redirect("user:login")

    user = User.objects.get(id=user_id)

    try:
        candidate = Candidate.objects.get(user_id=user)
        if candidate.resume:
            # Fix the path if 'resume_folder/' is included in DB
            resume_relative_path = str(candidate.resume).replace("resume_folder/", "")
            resume_url = '/resumes/' + resume_relative_path  # URL to open in new tab

            file_path = os.path.join(r"D:\ai resume analyzer\recruitai\resume_folder", resume_relative_path)
            if not os.path.exists(file_path):
                resume_url = None
        else:
            resume_url = None
    except Candidate.DoesNotExist:
        candidate = None
        resume_url = None

    return render(request, "candidate_home.html", {
        "user": user,
        "candidate": candidate,
        "resume_url": resume_url
    })


def edit_profile(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("/user/login/?next=/user/edit_profile/")

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect("/user/login/")

    if request.method == 'POST':
        fullname = request.POST.get('fullname', '').strip()
        email = request.POST.get('email', '').strip()
        phone_number = request.POST.get('phone_number', '').strip()

        # Basic validations
        if not fullname:
            messages.error(request, "Full name is required.")
        elif not email:
            messages.error(request, "Email is required.")
        else:
            try:
                validate_email(email)
            except ValidationError:
                messages.error(request, "Invalid email format.")
            else:
                user.fullname = fullname
                user.email = email
                user.phone_number = phone_number

                if user.role == 'candidate':
                    try:
                        candidate = Candidate.objects.get(user_id=user)
                    except Candidate.DoesNotExist:
                        candidate = Candidate(user_id=user)

                    candidate.skill = request.POST.get('skill', '').strip()
                    candidate.exp = request.POST.get('exp') or 0
                    if 'resume' in request.FILES:
                        candidate.resume = request.FILES['resume']
                    candidate.save()

                elif user.role == 'recruiter':
                    try:
                        org = Organization.objects.get(user_id=user)
                    except Organization.DoesNotExist:
                        org = Organization(user_id=user)

                    org.company_name = request.POST.get('company_name', '').strip()
                    org.company_email = request.POST.get('company_email', '').strip()
                    org.address = request.POST.get('address', '').strip()
                    org.save()

                user.save()
                messages.success(request, 'Profile updated successfully!')
                return redirect('user:edit_profile')

    context = {
        'user': user,
        'candidate': None,
        'organization': None
    }

    if user.role == 'candidate':
        try:
            context['candidate'] = Candidate.objects.get(user_id=user)
        except Candidate.DoesNotExist:
            context['candidate'] = None

    elif user.role == 'recruiter':
        try:
            context['organization'] = Organization.objects.get(user_id=user)
        except Organization.DoesNotExist:
            context['organization'] = None

    return render(request, 'edit_profile.html', context)


def recruiter_home(request):
    # Ensure the user is logged in
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, "You must log in first.")
        return redirect("user:login")

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect("user:login")

    try:
        recruiter = Organization.objects.get(user_id=user)
    except Organization.DoesNotExist:
        recruiter = None

    # Handle candidate search filters
    search_form = CandidateSearchForm(request.GET or None)
    candidates = Candidate.objects.all()  # Default to all candidates if no search is done

    if search_form.is_valid():
        qualifications = search_form.cleaned_data.get("qualifications")
        location = search_form.cleaned_data.get("location")
        job_position = search_form.cleaned_data.get("job_position")

        # Apply filters based on search criteria
        if qualifications:
            candidates = candidates.filter(skill__icontains=qualifications)
        if location:
            candidates = candidates.filter(user_id__profile__location__icontains=location)  # Assuming location is part of the profile
        if job_position:
            candidates = candidates.filter(skill__icontains=job_position)  # Assuming job position can be inferred from skills

    # Placeholder for AI recommendations (top 5 candidates)
    recommended_candidates = candidates[:5]  # Replace with real AI logic as needed

    # Handle candidate actions (accept/hold/reject)
    if request.method == "POST":
        action = request.POST.get("action")
        candidate_id = request.POST.get("candidate_id")
        try:
            candidate = Candidate.objects.get(id=candidate_id)
            if action == "accept":
                candidate.status = "Accepted"
            elif action == "hold":
                candidate.status = "On Hold"
            elif action == "reject":
                candidate.status = "Rejected"
            candidate.save()
            messages.success(request, f"Candidate {action} successfully!")
        except Candidate.DoesNotExist:
            messages.error(request, "Candidate not found.")

    # Define available locations as a list (previously attempted .split in template)
    locations = ["Remote", "Delhi", "Bangalore", "Chennai"]
    qualifications = ["Bachelor's", "Master's", "PhD"]

    return render(request, "recruiter_home.html", {
        "user": user,
        "recruiter": recruiter,
        "search_form": search_form,
        "candidates": candidates,
        "recommended_candidates": recommended_candidates,
        "locations": locations,
        "qualifications": qualifications,
    })



# def recruiter_home(request):
#     # Ensure the user is logged in
#     user_id = request.session.get('user_id')
#     if not user_id:
#         messages.error(request, "You must log in first.")
#         return redirect("user:login")

#     try:
#         user = User.objects.get(id=user_id)
#     except User.DoesNotExist:
#         messages.error(request, "User not found.")
#         return redirect("user:login")

#     try:
#         recruiter = Organization.objects.get(user_id=user)
#     except Organization.DoesNotExist:
#         recruiter = None

#     # Handle candidate search filters
#     search_form = CandidateSearchForm(request.GET or None)
#     candidates = Candidate.objects.all()  # Default to all candidates if no search is done

#     if search_form.is_valid():
#         qualifications = search_form.cleaned_data.get("qualifications")
#         location = search_form.cleaned_data.get("location")
#         job_position = search_form.cleaned_data.get("job_position")

#         # Apply filters based on search criteria
#         if qualifications:
#             candidates = candidates.filter(skill__icontains=qualifications)
#         if location:
#             candidates = candidates.filter(user_id__profile__location__icontains=location)  # Assuming location is part of the profile
#         if job_position:
#             candidates = candidates.filter(skill__icontains=job_position)  # Assuming job position can be inferred from skills

#     # Placeholder for AI recommendations (top 5 candidates)
#     recommended_candidates = candidates[:5]  # Here we are using the first 5 candidates as placeholder for AI recommendations

#     # Handle candidate actions (accept/hold/reject)
#     if request.method == "POST":
#         action = request.POST.get("action")
#         candidate_id = request.POST.get("candidate_id")
#         try:
#             candidate = Candidate.objects.get(id=candidate_id)
#             if action == "accept":
#                 candidate.status = "Accepted"
#             elif action == "hold":
#                 candidate.status = "On Hold"
#             elif action == "reject":
#                 candidate.status = "Rejected"
#             candidate.save()
#             messages.success(request, f"Candidate {action} successfully!")
#         except Candidate.DoesNotExist:
#             messages.error(request, "Candidate not found.")

#     # Render the template with all the necessary data
#     return render(request, "recruiter_home.html", {
#         "user": user,
#         "recruiter": recruiter,
#         "search_form": search_form,
#         "candidates": candidates,
#         "recommended_candidates": recommended_candidates,
#     })

def search_candidates(request):
    # Get the search parameters from GET request
    job_title = request.GET.get('job_title', '')
    location = request.GET.get('location', '')
    qualification = request.GET.get('qualification', '')
    
    # Filter candidates based on the search criteria
    candidates = Candidate.objects.all()

    if job_title:
        candidates = candidates.filter(skill__icontains=job_title)
    if location:
        candidates = candidates.filter(user_id__profile__location__icontains=location)
    if qualification:
        candidates = candidates.filter(user_id__profile__qualification__icontains=qualification)

    # Get the AI recommendations (Placeholder for actual AI logic)
    ai_recommendations = candidates[:5]  # Placeholder for top 5 recommended candidates

    return render(request, 'recruiter_home.html', {
        'candidates': candidates,
        'ai_recommendations': ai_recommendations,
        'job_title': job_title,
        'location': location,
        'qualification': qualification,
    })

# View for Handling Candidate Actions (Accept, Hold, Reject)
def candidate_action(request, candidate_id):
    action = request.POST.get('action')

    try:
        candidate = Candidate.objects.get(id=candidate_id)
        if action == 'accept':
            candidate.status = 'Accepted'
        elif action == 'hold':
            candidate.status = 'On Hold'
        elif action == 'reject':
            candidate.status = 'Rejected'
        else:
            messages.error(request, "Invalid action.")
            return redirect('recruiter:search_candidates')
        
        candidate.save()
        messages.success(request, f"Candidate {action} successfully!")
    except Candidate.DoesNotExist:
        messages.error(request, "Candidate not found.")
    
    return redirect('recruiter:search_candidates')