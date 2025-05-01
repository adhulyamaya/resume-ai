from django.contrib import admin
from .models import User, UserProfile, Candidate, Organization

# Register the User model (custom model that inherits from AbstractUser)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'fullname', 'email', 'role', 'created_at', 'last_login')
    search_fields = ('username', 'fullname', 'email', 'role')
    list_filter = ('role', 'created_at')
    
admin.site.register(User, UserAdmin)


# Register the Candidate model
class CandidateAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'skill', 'exp', 'created_at', 'updated_at','extracted_skills', 'extracted_location', 'extracted_experience')
    search_fields = ('user_id__username', 'skill')
    list_filter = ('created_at',)
    
admin.site.register(Candidate, CandidateAdmin)

# Register the Organization model
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'company_name', 'company_email', 'created_at')
    search_fields = ('company_name', 'company_email')
    list_filter = ('created_at',)
    
admin.site.register(Organization, OrganizationAdmin)
