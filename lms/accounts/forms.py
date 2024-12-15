from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Course, Module, CustomUser
from django.forms import modelformset_factory

class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'role', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user

class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['name', 'description', 'concepts', 'duration', 'deadline']
        widgets = {
            'deadline': forms.DateInput(attrs={'type': 'date'}),
        }

ModuleFormSet = modelformset_factory(
    Module,
    fields=('title', 'content', 'order'),
    extra=3,
    can_delete=True,
    widgets={
        'content': forms.Textarea(attrs={'rows': 4})
    }
)
from django import forms
from .models import Course, Module, CourseFeedback  # Add CourseFeedback to imports

class CourseFeedbackForm(forms.ModelForm):
    class Meta:
        model = CourseFeedback
        fields = ['feedback_text', 'rating']
        widgets = {
            'rating': forms.RadioSelect()
        }

from django import forms
from .models import Request

class RequestForm(forms.ModelForm):
    class Meta:
        model = Request
        fields = ('name', 'description', 'concept', 'duration', 'deadline')