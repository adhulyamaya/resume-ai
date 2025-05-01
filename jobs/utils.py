import re
import json
import fitz
import ast 
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
# def filter_jobs(resume_data, jobs):
#     """Filter jobs based on skills, location, and experience."""
#     import ast
#     filtered_jobs = []
#     skills = resume_data['skills'] if resume_data['skills'] else []

#     # Normalize experience
#     try:
#         experience_years = float(resume_data['experience'].split('+')[0].strip())
#     except Exception:
#         experience_years = 0

#     # Filtering logic
#     for job in jobs:
#         skill_match = any(skill.lower() in job.required_skills.lower() for skill in skills)
#         location_match = resume_data['location'].lower() in job.location.lower() if resume_data['location'] else True
#         experience_match = experience_years >= job.min_experience

#         if skill_match and location_match and experience_match:
#             filtered_jobs.append(job)

#     return filtered_jobs



def filter_jobs(resume_data, jobs):
    """Filter jobs based on skills, location, and experience, prioritizing skills_required field."""
    import ast
    filtered_jobs = []
    
    # Convert skills from string representation to actual list if needed
    if isinstance(resume_data['skills'], str):
        try:
            skills = ast.literal_eval(resume_data['skills'])
        except (ValueError, SyntaxError):
            skills = [resume_data['skills']]  # Fallback if parsing fails
    else:
        skills = resume_data['skills'] if resume_data['skills'] else []
    
    # Normalize experience
    try:
        experience_years = float(resume_data['experience'].split('+')[0].strip())
    except (AttributeError, ValueError, TypeError):
        experience_years = 0
    
    print(f"DEBUG - Parsed experience years: {experience_years}")
    print(f"DEBUG - Candidate skills: {skills[:5]}...")  # First 5 skills
    
    # Filtering logic
    for job in jobs:
        print(f"\nEvaluating job: {job.title}")
        print(f"skills_required field: '{job.skills_required}'")
        print(f"Job location: {job.location}")
        print(f"Min experience: {job.min_experience}")
        
        # Check skills match using skills_required field
        skill_match = False
        
        # Check if skills_required has data
        if job.skills_required.strip():
            for skill in skills:
                if skill.lower() in job.skills_required.lower():
                    skill_match = True
                    print(f"  ✅ Skill match found: {skill}")
                    break
            
            if not skill_match:
                print(f"  ❌ No matching skills found")
        else:
            # If skills_required is empty, consider it a match (no specific skills required)
            skill_match = True
            print(f"  ✅ No skills specified for job - considering as match")
        
        # FALLBACK: If no skills match but job title has tech keywords or candidate skills
        if not skill_match:
            # First check if any of the candidate's skills appear in the job title
            for skill in skills:
                if skill.lower() in job.title.lower():
                    skill_match = True
                    print(f"  ✅ Job title contains skill: {skill}")
                    break
            
            # If still no match, check for common tech keywords
            if not skill_match:
                tech_keywords = ['python', 'django', 'developer', 'engineer', 'programmer', 
                               'software', 'web', 'fullstack', 'full stack', 'back end', 
                               'front end', 'javascript', 'react', 'node']
                
                for keyword in tech_keywords:
                    if keyword.lower() in job.title.lower():
                        skill_match = True
                        print(f"  ✅ Job title contains tech keyword: {keyword}")
                        break
        
        # Location check - True if candidate location is None or matches
        location_match = True  # Default to True if candidate location is None
        if resume_data['location']:
            location_match = resume_data['location'].lower() in job.location.lower()
            print(f"  {'✅' if location_match else '❌'} Location match: {resume_data['location']} vs {job.location}")
        else:
            print(f"  ✅ Location check bypassed (candidate location is None)")
        
        # Experience check
        experience_match = experience_years >= job.min_experience
        print(f"  {'✅' if experience_match else '❌'} Experience match: {experience_years} vs {job.min_experience}")
        
        # Overall match
        if skill_match and location_match and experience_match:
            print(f"  ✅ Job '{job.title}' MATCHED all criteria!")
            filtered_jobs.append(job)
        else:
            print(f"  ❌ Job '{job.title}' filtered out - skill_match:{skill_match}, location_match:{location_match}, experience_match:{experience_match}")
    
    return filtered_jobs

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
