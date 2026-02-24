from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from .models import Profile, Inquiry

User = get_user_model()


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ("phone", "bio")


class InquiryForm(forms.ModelForm):
    class Meta:
        model = Inquiry
        fields = ("message",)
        widgets = {
            'message': forms.Textarea(attrs={'rows':4})
        }
