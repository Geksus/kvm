import re

from django import forms

from .models import KVM_user, ServerRoom, KVM
from django.contrib.auth.models import User as DjangoUser


class SelectKVMPortForm(forms.Form):
    kvm_port = forms.IntegerField(
        label="KVM Port",
        min_value=1,
        error_messages={
            "required": "Please select a KVM port.",
            "min_value": "KVM port must be greater than or equal to 1.",
        },
    )

    def clean_kvm_port(self):
        data = self.cleaned_data["kvm_port"]
        if data < 1:
            raise forms.ValidationError("KVM port must be greater than or equal to 1.")
        return data


class KVMAccessForm(forms.ModelForm):
    class Meta:
        model = KVM_user
        fields = ("username", "email")

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


class DjangoUserCreationForm(forms.ModelForm):
    is_superuser = forms.BooleanField(required=False)
    is_staff = forms.BooleanField(required=False)

    class Meta:
        model = DjangoUser
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "password",
            "is_superuser",
            "is_staff",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs["class"] = "form-control is-invalid"
        self.fields["email"].widget.attrs["class"] = "form-control is-invalid"

    def clean_email(self):
        data = self.cleaned_data["email"]
        if not re.fullmatch(r"[^@]+@[^@]+\.[^@]+", data):
            raise forms.ValidationError("Email is not valid.")
        return data

    def clean_username(self):
        data = self.cleaned_data["username"]
        if not data.isalnum():
            raise forms.ValidationError(
                "Username should only contain alphanumeric characters."
            )
        if not 3 <= len(data) <= 12:
            raise forms.ValidationError(
                "username should be between 3 and 12 characters."
            )
        if data in [u.username for u in DjangoUser.objects.all()]:
            raise forms.ValidationError(f"{data} already exists.")
        return data

    def clean(self):
        cleaned_data = super().clean()
        is_superuser = cleaned_data.get("is_superuser")
        is_staff = cleaned_data.get("is_staff")
        if is_superuser and is_staff:
            raise forms.ValidationError("User cannot be both staff and superuser.")
        if not is_superuser and not is_staff:
            raise forms.ValidationError("User must be either staff or superuser.")
        return cleaned_data


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
        labels = {
            "name": "Name",
            "description": "Description (optional)",
            "num_rows": "Number of rows",
            "num_racks": "Number of racks",
            "ports_per_rack": "Number of ports on each rack",
            "kvm_id": "Select KVM",
        }

    def clean(self):
        data = self.cleaned_data
        if not 3 <= len(data["name"]) <= 20:
            raise forms.ValidationError("Name should be between 3 and 20 characters.")
        if data["num_rows"] <= 0:
            raise forms.ValidationError("Number of rows should be greater than 0.")
        if data["num_racks"] <= 0:
            raise forms.ValidationError("Number of racks should be greater than 0.")
        if data["kvm_id"] is None:
            raise forms.ValidationError(
                "KVM ID should not be empty. If there are no KVMs, please create one first."
            )
        if (
            data.get("kvm_id")
            and data["kvm_id"].server_room_id is not None
            and KVM.objects.get(short_name=data["kvm_id"]).server_room_id.id
            != self.instance.id
        ):
            raise forms.ValidationError(
                "KVM is already assigned to another server room."
            )
        return data


class CreateKVMForm(forms.ModelForm):
    class Meta:
        model = KVM
        fields = ("fqdn", "short_name", "ip", "number_of_ports", "server_room_id")
        labels = {
            "fqdn": "FQDN",
            "short_name": "Short name",
            "ip": "IP",
            "number_of_ports": "Number of ports",
            "server_room_id": "Server room id",
        }

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
