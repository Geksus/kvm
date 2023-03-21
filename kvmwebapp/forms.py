from django import forms

from .models import User


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("username",)

    def clean_username(self):
        data = self.cleaned_data["username"]
        if not data.isalnum():
            raise forms.ValidationError(
                "username should only contain alphanumeric characters."
            )
        if not 3 <= len(data) <= 12:
            raise forms.ValidationError(
                "username should be between 3 and 12 characters."
            )
        return data
