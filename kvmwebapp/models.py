from django.db import models
from datetime import datetime, timedelta
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_filters import rest_framework as filters


class KVM(models.Model):
    fqdn = models.CharField(max_length=40, unique=True, help_text="url")
    short_name = models.CharField(max_length=8, unique=False, help_text="system_name")
    ip = models.GenericIPAddressField(protocol='IPv4')
    number_of_ports = models.PositiveSmallIntegerField(default=32)

    def clean(self):
        # Validate that fqdn and short_name are alphanumeric
        if not self.fqdn.isalnum():
            raise ValidationError(_('fqdn should only contain alphanumeric characters.'))
        if not self.short_name.isalnum():
            raise ValidationError(_('short_name should only contain alphanumeric characters.'))

    class Meta:
        db_table = "KVM"


class Cross(models.Model):
    row = models.PositiveSmallIntegerField(help_text="row")
    rack = models.PositiveSmallIntegerField(help_text="rack")
    rack_port = models.PositiveSmallIntegerField(help_text="rack_port")
    kvm_id = models.ForeignKey('KVM', on_delete=models.SET_NULL, null=True, blank=True, db_column="kvm_id",
                               help_text="id_hosts")
    kvm_port = models.PositiveSmallIntegerField(unique=True, null=True, blank=True, help_text="kvm_port")
    kvm_port_active = models.BooleanField(default=False)
    user = models.OneToOneField('User', on_delete=models.SET_NULL, null=True, blank=True)

    def clean(self):
        # Validate that row is not bigger than 4, rack is not bigger than 14, and rack_port is not bigger than 2
        if self.row > 4:
            raise ValidationError(_('row should not be bigger than 4.'))
        if self.rack > 14:
            raise ValidationError(_('rack should not be bigger than 14.'))
        if self.rack_port > 2:
            raise ValidationError(_('rack_port should not be bigger than 2.'))

        # Validate that rack_port and kvm_port are within the allowed range
        if not (1 <= self.rack_port <= 2):
            raise ValidationError(_('rack_port should be between 1 and 48.'))
        if not (1 <= self.kvm_port <= self.kvm_id.number_of_ports):
            raise ValidationError(_('kvm_port should be between 1 and %(num_ports)s.'),
                                  params={'num_ports': self.kvm_id.number_of_ports})

    class Meta:
        db_table = "Cross"


class CrossFilter(filters.FilterSet):
    row = filters.NumberFilter(field_name='row')
    rack = filters.NumberFilter(field_name='rack')
    rack_port = filters.NumberFilter(field_name='rack_port')

    class Meta:
        model = Cross
        fields = ['row', 'rack', 'rack_port']


class User(models.Model):
    username = models.CharField(max_length=40, unique=True, help_text="username")
    password = models.CharField(max_length=255, unique=False, help_text="password")
    start_time = models.DateTimeField(default=datetime.now(), blank=True)

    class Meta:
        db_table = "User"
