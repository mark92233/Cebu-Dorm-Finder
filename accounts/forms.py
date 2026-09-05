from django import forms
from .models import User, UserProfile

class UserRegistrationForm(forms.ModelForm):
    """
    Form for capturing a user's email to start the registration process.
    """
    class Meta:
        model = User
        fields = ('email',)

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('first_name', 'last_name', 'phone_number', 'birthday')

class LoginForm(forms.Form):
    email = forms.EmailField(label="Email Address")
    password = forms.CharField(widget=forms.PasswordInput)