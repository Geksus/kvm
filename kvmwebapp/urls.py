from django.urls import path

from kvmwebapp.views import create_user, IndexView1, user_info, delete_user, IndexView2, redirect_to_index

app_name = "kvmwebapp"

urlpatterns = [
    path("", redirect_to_index, name="index"),
    path("2/", IndexView2.as_view(), name="index2"),
    path("1/", IndexView1.as_view(), name="index1"),
    path("create_user/", create_user, name="create_user"),
    path("2/create_user/", create_user, name="create_user"),
    path("1/create_user/", create_user, name="create_user"),
    path("user_info/<int:user_id>/", user_info, name="user_info"),
    path("delete_user/<int:user_id>/", delete_user, name="delete_user"),
]
