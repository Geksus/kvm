from django import forms

from .models import User, ServerRoom, KVM
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
        if data in [u.username for u in User.objects.all()]:
            raise forms.ValidationError(f"{data} already has access to KVM.")
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
        if data.get("kvm_id") and data["kvm_id"].server_room_id is not None:
            raise forms.ValidationError(
                "KVM is already assigned to another server room."
            )
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
