from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models


class User(AbstractUser):
    
    fullname = models.CharField(max_length=50) 
    email = models.CharField(max_length=50) 
    password = models.CharField(max_length=50) 
    phone_number=models.CharField(max_length=15, null=True, blank=True, default='0000000000') 
    role = models.CharField(max_length=10, null=True, blank=True)
    description = models.TextField() 
    created_at = models.DateTimeField(auto_now_add=True) 
    last_login = models.DateTimeField(auto_now=True, null=True, blank=True)

    groups = models.ManyToManyField(
        Group,
        related_name="custom_user_set",  # Provide unique related_name for groups
        blank=True,
        help_text="The groups this user belongs to.",
        verbose_name="groups",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name="custom_user_permissions_set",  # Provide unique related_name for permissions
        blank=True,
        help_text="Specific permissions for this user.",
        verbose_name="user permissions",
    )


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)


class Candidate(models.Model): 
    
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    resume = models.FileField(upload_to='resume_folder/') 
    skill = models.TextField() 
    exp = models.CharField(max_length=10) 
    created_at = models.DateTimeField(auto_now_add=True) 
    updated_at = models.DateTimeField(auto_now_add=True)

    extracted_skills = models.TextField(null=True, blank=True)
    extracted_location = models.CharField(max_length=255, null=True, blank=True)
    extracted_experience = models.CharField(max_length=255, null=True, blank=True)


class Organization(models.Model):
    user_id = models.OneToOneField(User, on_delete=models.CASCADE)
    company_name = models.CharField(max_length=100, unique=True)
    address = models.TextField()
    company_email = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)