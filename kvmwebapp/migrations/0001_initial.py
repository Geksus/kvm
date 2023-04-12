# Generated by Django 4.1.7 on 2023-03-01 15:02

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="KVM",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("fqdn", models.CharField(help_text="url", max_length=40, unique=True)),
                (
                    "short_name",
                    models.CharField(
                        help_text="system_name", max_length=8, unique=True
                    ),
                ),
                ("ip", models.GenericIPAddressField(protocol="IPv4")),
                ("number_of_ports", models.PositiveSmallIntegerField(default="32")),
            ],
            options={
                "db_table": "KVM",
            },
        ),
        migrations.CreateModel(
            name="KVM_user",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "username",
                    models.CharField(help_text="username", max_length=40, unique=True),
                ),
                (
                    "password",
                    models.CharField(help_text="password", max_length=40, unique=True),
                ),
                (
                    "start_time",
                    models.DateTimeField(blank=True, default=datetime.datetime.now),
                ),
                ("stop_time", models.DateTimeField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name="Cross",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("row", models.PositiveSmallIntegerField(help_text="row")),
                ("rack", models.PositiveSmallIntegerField(help_text="rack")),
                ("rack_port", models.PositiveSmallIntegerField(help_text="rack_port")),
                (
                    "kvm_port",
                    models.PositiveSmallIntegerField(
                        blank=True, help_text="kvm_port", null=True
                    ),
                ),
                (
                    "kvm_id",
                    models.ForeignKey(
                        blank=True,
                        db_column="kvm_id",
                        db_index=False,
                        help_text="id_hosts",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="kvmwebapp.kvm",
                    ),
                ),
            ],
            options={
                "db_table": "Cross",
            },
        ),
    ]
