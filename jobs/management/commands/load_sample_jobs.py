import json
from django.core.management.base import BaseCommand
from jobs.models import Job  

class Command(BaseCommand):
    help = "Load sample jobs into the database"

    def handle(self, *args, **kwargs):
        
        json_file_path = 'data/sample_jobs.json'
        try:
            with open(json_file_path, 'r') as file:
                jobs_data = json.load(file)
        except FileNotFoundError:
            self.stderr.write(self.style.ERROR(f"File not found: {json_file_path}"))
            return
        
        for job_data in jobs_data:
            Job.objects.create(
                title=job_data["title"],
                description=job_data["description"],
                skills_required=",".join(job_data["skills_required"]),  
                location=job_data["location"],
                min_experience=job_data["min_experience"],
                job_type=job_data["job_type"],
                salary=job_data["salary"]
            )

        self.stdout.write(self.style.SUCCESS("Successfully loaded sample jobs!"))
