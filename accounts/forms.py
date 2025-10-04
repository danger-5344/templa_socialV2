from django import forms
from django.contrib.auth import get_user_model
from .models import Profile

User = get_user_model()

class ProfileForm(forms.ModelForm):
    email = forms.EmailField(required=True)  # from User model, we’ll sync manually

    class Meta:
        model = Profile
        fields = ["display_name", "company", "avatar"]  # avatar optional

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user")
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields["email"].initial = user.email

    def save(self, commit=True):
        profile = super().save(commit=False)
        # Sync email on User
        self.user.email = self.cleaned_data["email"]
        if commit:
            self.user.save()
            profile.user = self.user
            profile.save()
        return profile
