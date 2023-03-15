from django.urls import path

from kvmwebapp.views import create_user, IndexView

app_name = "kvmwebapp"
urlpatterns = [path("", IndexView.as_view(), name="index"),
               path('create_user/', create_user, name='create_user'),
               ]
