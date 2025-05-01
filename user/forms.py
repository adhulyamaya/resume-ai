from django import forms

class CandidateSearchForm(forms.Form):
    qualifications = forms.CharField(required=False)
    location = forms.CharField(required=False)
    job_position = forms.CharField(required=False)
