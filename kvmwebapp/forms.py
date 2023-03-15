from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.hashers import make_password
from django.utils import timezone

from .models import Cross, User


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username',)
    #
    # def __init__(self, cross, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self.cross = cross

    # def save(self, commit=True):
    #     user = super().save(commit=False)
    #     user.password = make_password(User.objects.make_random_password())
    #     user.start_time = timezone.now()
    #     user.stop_time = self.cleaned_data['stop_time']
    #     user.save(commit=True)
    #     self.cross.user = user
    #     self.cross.kvm_port_active = True
    #     self.cross.save()
    #     return user

