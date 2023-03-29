from django import forms

from .models import User, ServerRoom, KVM
from django.contrib.auth.models import User as DjangoUser


class KVMAccessForm(forms.ModelForm):
    # username = forms.ModelChoiceField(queryset=DjangoUser.objects.all())

    class Meta:
        model = User
        fields = ("username", "email")

    def clean_username(self):
        list_of_users = [u.username for u in DjangoUser.objects.all()]
        print(list_of_users)
        data = self.cleaned_data["username"]
        if data not in list_of_users:
            raise forms.ValidationError("User does not exist.")
        if not data.isalnum():
            raise forms.ValidationError(
                "username should only contain alphanumeric characters."
            )
        if not 3 <= len(data) <= 12:
            raise forms.ValidationError(
                "username should be between 3 and 12 characters."
            )
        return data


class DjangoUserCreationForm(forms.ModelForm):
    class Meta:
        model = DjangoUser
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "password",
            "is_superuser",
        )

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


class CreateServerRoomForm(forms.ModelForm):
    class Meta:
        model = ServerRoom
        fields = (
            "name",
            "description",
            "num_rows",
            "num_racks",
            "ports_per_rack",
            "kvm_id",
        )

    def clean(self):
        data = self.cleaned_data
        if not 3 <= len(data["name"]) <= 12:
            raise forms.ValidationError("Name should be between 3 and 12 characters.")
        if data["num_rows"] <= 0:
            raise forms.ValidationError("Number of rows should be greater than 0.")
        if data["num_racks"] <= 0:
            raise forms.ValidationError("Number of racks should be greater than 0.")
        return data


class CreateKVMForm(forms.ModelForm):
    class Meta:
        model = KVM
        fields = ("fqdn", "short_name", "ip", "number_of_ports", "server_room_id")

    def clean(self):
        data = self.cleaned_data
        if not data["short_name"].is_alphanumeric():
            raise forms.ValidationError(
                "Short name should only contain alphanumeric characters."
            )
        if not 3 <= len(data["short_name"]) <= 5:
            raise forms.ValidationError(
                "Short name should be between 3 and 5 characters."
            )
        if data["number_of_ports"] <= 0:
            raise forms.ValidationError("Number of ports should be greater than 0.")
        return data
