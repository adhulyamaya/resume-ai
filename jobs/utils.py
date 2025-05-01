import re
import json
import fitz
from groq import Groq
from operator import itemgetter
import re
import json
import fitz
from groq import Groq
from operator import itemgetter
from .models import ResumeData,Job
from user.views import extract_resume_data, parse_resume_pdf

# utils.py
import re

def filter_jobs(resume_data, jobs):
    """Filter jobs based on skills, location, and experience."""
    filtered_jobs = []

    # experience
    experience_str = resume_data['experience']
    match = re.match(r'(\d+)', experience_str)  # Matches leading digits
    experience_years = float(match.group(1)) if match else 0  # Use the numeric value or default to 0

    # filtering
    for job in jobs:
        # Assuming required_skills is a comma-separated string
        required_skills_list = [skill.strip().lower() for skill in job.required_skills.split(',')]

        skill_match = any(skill.lower() in required_skills_list for skill in resume_data['skills'])
        
        location_match = resume_data['location'].lower() in job.location.lower() if resume_data['location'] else True
        
        experience_match = experience_years >= job.min_experience
        
        if skill_match and location_match and experience_match:
            filtered_jobs.append(job)

    return filtered_jobs

# def filter_jobs(resume_data, jobs):
#     """Filter jobs based on skills, location, and experience."""
#     filtered_jobs = []

#     # experience
#     experience_years = float(resume_data['experience'].split()[0]) if resume_data['experience'] else 0

#     # filtering
#     for job in jobs:
#         skill_match = any(skill.lower() in job.required_skills.lower() for skill in resume_data['skills'])
        
#         location_match = resume_data['location'].lower() in job.location.lower() if resume_data['location'] else True
        
#         experience_match = experience_years >= job.min_experience
        
#         if skill_match and location_match and experience_match:
#             filtered_jobs.append(job)

#     return filtered_jobs


# def rank_job(resume_data, job, api_key):
#     """Rank a job against a resume using Groq LLM."""
#     client = Groq(api_key=api_key)
    
#     prompt = f"""
#     You are a hiring manager evaluating a candidate for a job position.
    
#     Job Title: {job.title}
#     Job Description: {job.description}
#     Required Skills: {', '.join(job.required_skills.split(", "))}
#     Job Location: {job.location}
#     Minimum Experience: {job.min_experience} years
    
#     Candidate Resume:
#     {resume_data['raw_text']}

#     Based on the match between the resume and job requirements, assign a score from 0 to 100.
#     Consider skills match, experience relevance, and overall fit. Analyzing should be strict and fair.
    
#     Return ONLY a valid JSON object with the following structure:
#     {{
#         "score": X
#     }}
#     where X is a number between 0 and 100.
#     """
    
#     try:
#         completion = client.chat.completions.create(
#             messages=[
#                 {"role": "system", "content": "You are a hiring manager that evaluates job candidates. Always respond with valid JSON."},
#                 {"role": "user", "content": prompt}
#             ],
#             model="llama3-70b-8192",
#             response_format={"type": "json_object"},
#             temperature=0.5,
#         )
        
#         content = completion.choices[0].message.content
#         data = json.loads(content)
#         return data.get("score", 0)
        
#     except Exception as e:
#         print(f"Error calling Groq API: {e}")
#         return 0


def rank_job(resume_data, job, api_key):
    """Rank a job against a resume using Groq LLM."""
    client = Groq(api_key=api_key)
    
    # Update the prompt to include skills, location, and experience only
    prompt = f"""
    You are a hiring manager evaluating a candidate for a job position.

    Job Title: {job.title}
    Job Description: {job.description}
    Required Skills: {', '.join(job.required_skills.split(', '))}
    Job Location: {job.location}
    Minimum Experience: {job.min_experience} years

    Candidate Resume:
    Skills: {', '.join(resume_data['skills'])}
    Location: {resume_data['location']}
    Experience: {resume_data['experience']}

    Based on the match between the resume and job requirements, assign a score from 0 to 100.
    Consider skills match, experience relevance, and overall fit. Analyzing should be strict and fair.

    Return ONLY a valid JSON object with the following structure:
    {{
        "score": X
    }}
    where X is a number between 0 and 100.
    """
    
    try:
        # Call the Groq API with the updated prompt
        completion = client.chat.completions.create(
            messages=[{
                "role": "system", 
                "content": "You are a hiring manager that evaluates job candidates. Always respond with valid JSON."
            },
            {
                "role": "user", 
                "content": prompt
            }],
            model="llama3-70b-8192",
            response_format={"type": "json_object"},
            temperature=0.5,
        )
        
        # Parse the response and get the score
        content = completion.choices[0].message.content
        data = json.loads(content)
        return data.get("score", 0)
        
    except Exception as e:
        print(f"Error calling Groq API: {e}")
        return 0

