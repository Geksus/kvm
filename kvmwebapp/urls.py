from django.urls import path

from kvmwebapp.views import (
    give_kvm_access,
    IndexView,
    user_info,
    delete_user,
    CreateServerRoom,
    CreateKVM,
    ServerRoomListView,
    delete_server_room,
    KVMListView,
    delete_kvm,
    login_view,
    register,
    logout_view,
    UserListView,
    access_info,
    remove_access,
    UpdateServerRoom,
    # modify_server_room,
)

app_name = "kvmwebapp"

urlpatterns = [
    path("", IndexView.as_view(), name="index"),
    path("create_user/", give_kvm_access, name="create_user"),
    path("server_room/<int:server_room>/", IndexView.as_view(), name="server_room"),
    path("server_room/<int:server_room>/create_user/", give_kvm_access, name="create_user"),
    path("user_info/<int:user_id>/", user_info, name="user_info"),
    path("delete_user/<int:user_id>/", delete_user, name="delete_user"),
    path("create_sroom/", CreateServerRoom.as_view(), name="create_server_room"),
    path("update_sroom/<int:pk>", UpdateServerRoom.as_view(), name="update_server_room"),
    path("create_kvm/", CreateKVM.as_view(), name="create_kvm"),
    path("sroom_list/", ServerRoomListView.as_view(), name="sroom_list"),
    path("delete_sroom/<int:room_id>/", delete_server_room, name="delete_sroom"),
    path("delete_kvm/<int:kvm_id>/", delete_kvm, name="delete_kvm"),
    path("kvm_list/", KVMListView.as_view(), name="kvm_list"),
    path("accounts/login/", login_view, name="login"),
    path("register/", register, name="register"),
    path("logout/", logout_view, name="logout"),
    path("user_list/", UserListView.as_view(), name="user_list"),
    path("access_info/<int:user_id>", access_info, name="access_info"),
    path("remove_access/<int:user_id>", remove_access, name="remove_access"),
    # path("modify_room/<int:room_id>", modify_server_room, name="modify_room"),
]
