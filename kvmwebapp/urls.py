from django.urls import path

from kvmwebapp.views import index, create_user

app_name = "kvmwebapp"
urlpatterns = [path("", index, name="index"),
               path('create_user/', create_user, name='create_user'),
               ]
