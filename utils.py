import re
import json
import fitz
from groq import Groq
from operator import itemgetter
from jobs.models import ResumeData, Job


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


def filter_jobs(resume_data: ResumeData, jobs: list[Job]) -> list[Job]:
    """Filter jobs based on skills, location, and experience."""
    filtered_jobs = []
    
    # experience
    experience_years = 0
    if resume_data.experience:
        match = re.search(r'(\d+(?:\.\d+)?)', resume_data.experience)
        if match:
            experience_years = float(match.group(1))
    
    # filtering
    for job in jobs:
        skill_match = False
        for skill in resume_data.skills:
            if skill.lower() in [s.lower() for s in job.required_skills]:
                skill_match = True
                break
        
        location_match = False
        if resume_data.location and job.location:
            location_match = resume_data.location.lower() in job.location.lower()
        
        experience_match = experience_years >= job.min_experience

        if skill_match and location_match and experience_match:
            filtered_jobs.append(job)
    
    return filtered_jobs


def rank_job(resume_data: ResumeData, job: Job, api_key: str) -> float:
    """Rank a job against a resume using Groq LLM."""
    client = Groq(api_key=api_key)
    
    prompt = f"""
    You are a hiring manager evaluating a candidate for a job position.
    
    Job Title: {job.title}
    Job Description: {job.description}
    Required Skills: {', '.join(job.required_skills)}
    Job Location: {job.location}
    Minimum Experience: {job.min_experience} years
    
    Candidate Resume:
    {resume_data.raw_text}
    
    Based on the match between the resume and job requirements, assign a score from 0 to 100.
    Consider skills match, experience relevance, and overall fit. Analyzing should be strict and fair.
    
    Return ONLY a valid JSON object with the following structure:
    {{
        "score": X
    }}
    where X is a number between 0 and 100.
    """
    
    try:
        completion = client.chat.completions.create(
            messages=[
                {   "role": "system",
                    "content": "You are a hiring manager that evaluates job candidates. Always respond with valid JSON."
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
        print(f"Ranking Score: {data}")
        
        return data.get("score", 0)
            
    except Exception as e:
        print(f"Error calling Groq API (2): {e}")
        return 0


def rank_sort_jobs(resume_data: ResumeData, filtered_jobs: list[Job], api_key: str) -> list[dict[str, str]]:
    """Rank and sort all filtered jobs against the resume."""
    ranked_jobs = []
    
    for job in filtered_jobs:
        score = rank_job(resume_data, job, api_key)
        ranked_jobs.append({
            "job_id": job.id,
            "score": score,
        })
    
    # sort jobs by score
    ranked_jobs.sort(key=itemgetter("score"), reverse=True)
    
    return ranked_jobs


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.getenv("GROQ_API_KEY")
    resume_text = parse_resume_pdf("Sahal-Rasheed-Resume.pdf")
    resume_data = extract_resume_data(resume_text, api_key)
    print(resume_data)