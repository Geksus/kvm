from django.urls import path

from kvmwebapp.views import create_user, IndexView, user_info, delete_user

app_name = "kvmwebapp"

urlpatterns = [
    path("", IndexView.as_view(), name="index"),
    path("create_user/", create_user, name="create_user"),
    path("server_room/<int:server_room>/", IndexView.as_view(), name="server_room"),
    path("server_room/2/create_user/", create_user, name="create_user"),
    path("user_info/<int:user_id>/", user_info, name="user_info"),
    path("delete_user/<int:user_id>/", delete_user, name="delete_user"),
]
