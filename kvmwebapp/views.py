from datetime import datetime
from time import strptime

from django.contrib import messages
from django.contrib.auth.models import User as DjangoUser
from django.contrib.auth import get_user_model, authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse, HttpResponseRedirect, HttpResponseForbidden, HttpResponse
from django.urls import reverse_lazy
from django.views.generic import (
    TemplateView,
    CreateView,
    ListView,
    UpdateView,
    FormView,
)
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q

from kvmwebapp.models import Cross, CrossFilter, KVM_user, ServerRoom, KVM
from .forms import (
    KVMAccessForm,
    CreateServerRoomForm,
    CreateKVMForm,
    DjangoUserCreationForm,
    SelectKVMPortForm,
)
from .logs import user_log, action_log


def filter_access():
    list_of_crosses = [c.user_id for c in Cross.objects.all() if c.user_id is not None]
    list_of_users = [u.id for u in KVM_user.objects.all()]
    for user in list_of_users:
        if user not in list_of_crosses:
            KVM_user.objects.get(id=user).delete()


def create_port_list(filtered_cross_list, server_room_number):
    filter_access()
    port_list = []
    for row in range(1, ServerRoom.objects.get(id=server_room_number).num_rows + 1):
        for rack in range(
            1, ServerRoom.objects.get(id=server_room_number).num_racks + 1
        ):
            for rack_port in range(
                1, ServerRoom.objects.get(id=server_room_number).ports_per_rack + 1
            ):
                try:
                    port_info = {
                        "row": row,
                        "rack": rack,
                        "rack_port": rack_port,
                        "rack_port_active": str(
                            Cross.objects.filter(
                                row=row,
                                rack=rack,
                                rack_port=rack_port,
                                server_room=server_room_number,
                            )
                            .first()
                            .rack_port_active
                        ),
                        "kvm_port": "-",
                        "short_name": "-",
                        "username": "-",
                        "start_time": "-",
                        "server_room": "-",
                    }
                except AttributeError:
                    break
                cross_queryset = filtered_cross_list.filter(
                    row=row,
                    rack=rack,
                    rack_port=rack_port,
                    server_room=server_room_number,
                )
                for cross in cross_queryset:
                    port_info["id"] = cross.id
                    port_info["kvm_port"] = cross.kvm_port or "-"
                    port_info["server_room"] = cross.server_room.id
                    cross.kvm_id = cross.server_room.kvm_id
                    if cross.kvm_id:
                        port_info["short_name"] = cross.server_room.kvm_id.short_name
                        if cross.user:
                            port_info["username"] = cross.user.username
                            port_info["start_time"] = cross.user.start_time.strftime(
                                "%Y-%m-%d %H:%M:%S"
                            )
                            port_info["current_time"] = datetime.now().strftime(
                                "%Y-%m-%d %H:%M:%S"
                            )
                            port_info["user_id"] = cross.user.id
                            if port_info["start_time"] and port_info["current_time"]:
                                port_info["time_elapsed"] = int(
                                    strptime(
                                        port_info["current_time"], "%Y-%m-%d %H:%M:%S"
                                    ).tm_hour
                                ) - int(
                                    strptime(
                                        port_info["start_time"], "%Y-%m-%d %H:%M:%S"
                                    ).tm_hour
                                )
                    else:
                        port_info["short_name"] = "-"
                        port_info["username"] = "-"
                if port_info["server_room"] == server_room_number:
                    port_list.append(port_info)
    return port_list


class IndexView(LoginRequiredMixin, TemplateView):
    template_name = "base.html"

    def get(self, request, *args, **kwargs):
        server_room_exists = ServerRoom.objects.first()
        if not server_room_exists:
            return redirect("kvmwebapp:create_server_room")
        self.server_room = kwargs.get("server_room", 1)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        server_rooms = ServerRoom.objects.all()
        context["server_rooms"] = server_rooms

        try:
            server_room = int(
                context["server_room"]
            )  # Get the server_room from the request or use a default value
        except KeyError:
            server_room = min(server_room.id for server_room in server_rooms)

        logs = KVM_user.objects.filter(cross__server_room_id=server_room).order_by(
            "-start_time"
        )
        # Get all Cross objects and order them by row, rack, and rack_port
        cross_list = (
            Cross.objects.filter(server_room_id=server_room)
            .select_related("kvm_id", "user", "server_room")
            .order_by("row", "rack", "rack_port", "server_room")
        )
        num_racks = ServerRoom.objects.get(id=server_room).num_racks
        num_rows = ServerRoom.objects.get(id=server_room).num_rows
        num_ports = ServerRoom.objects.get(id=server_room).ports_per_rack

        # Create a filter instance
        cross_filter = CrossFilter(self.request.GET, queryset=cross_list)

        # Get the filtered queryset
        filtered_cross_list = cross_filter.qs

        context["port_list"] = create_port_list(filtered_cross_list, server_room)
        context["num_racks"] = range(1, num_racks + 1)
        context["num_rows"] = range(1, num_rows + 1)
        context["num_ports"] = range(1, num_ports + 1)
        context["max_num_ports"] = num_ports
        context["logs"] = [
            {
                "user": log.username,
                "start_time": log.start_time.strftime("%d-%m-%Y %H:%M:%S"),
                "KVM": Cross.objects.get(user=log.id).server_room.kvm_id.short_name,
            }
            for log in logs
        ]
        context["current_server_room"] = ServerRoom.objects.get(
            id=server_room
        ).name  # Add the current server_room to the context

        return context


@login_required
def give_kvm_access(request, *args, **kwargs):
    if not request.user.is_superuser:
        raise PermissionDenied
    row, rack, rack_port, server_room = getting_data(request)
    used_usernames = [user.username for user in KVM_user.objects.all()]
    usernames = [
        user for user in DjangoUser.objects.all() if user.username not in used_usernames
    ]

    if request.method == "POST":
        form = KVMAccessForm(request.POST)
        if form.is_valid():
            cross = Cross.objects.get(
                row=int(request.POST["row"]),
                rack=int(request.POST["rack"]),
                rack_port=int(request.POST["rack_port"]),
                server_room=int(request.POST["server_room"]),
            )

            user = form.save(commit=False)
            user.start_time = datetime.now()
            User = get_user_model()
            user.password = User.objects.make_random_password(length=10)
            first_name = user.first_name
            last_name = user.last_name
            user.email = DjangoUser.objects.get(username=user.username).email
            start_time = user.start_time
            user.issued_by = request.user
            user.save()
            if cross is not None:
                cross.user_id = user.id
                cross.kvm_id = ServerRoom.objects.get(
                    id=int(request.POST["server_room"])
                ).kvm_id
                cross.kvm_port_active = True
                cross.save()
                action_description = f"gave access to {user.username} at {cross.server_room.name}, cross id - {cross.id}\n"
                user_log(request.user.username, action_description)
                action_log(request.user.username, action_description)
            return JsonResponse(
                {
                    "success": True,
                    "username": user.username,
                    "password": user.password,
                    "first_name": first_name,
                    "last_name": last_name,
                    "email": user.email,
                    "start_time": start_time.strftime("%d-%m-%Y %H:%M:%S"),
                    "issued_by": request.user.username,
                }
            )
        else:
            print("Form errors:", form.errors)  # Debugging line
            return JsonResponse({"errors": form.errors})
    else:
        form = KVMAccessForm()
        context = {
            "form": form,
            "row": row,
            "rack": rack,
            "rack_port": rack_port,
            "server_room": server_room,
            "current_time": datetime.now().strftime("%H:%M"),
            "usernames": usernames,
        }
        return render(request, "give_kvm_access.html", context)


def getting_data(request):
    row = request.GET.get("row", None)
    rack = request.GET.get("rack", None)
    rack_port = request.GET.get("rack_port", None)
    server_room = request.GET.get("server_room", None)

    return [row, rack, rack_port, server_room]


def user_info(request, user_id):
    user = get_object_or_404(DjangoUser, pk=user_id)
    if request.user.is_superuser or user.username == request.user.username:
        user_data = {
            "username": user.username,
            "password": user.password,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
        }
        action_description = f"viewed {user.username} info\n"
        user_log(request.user.username, action_description)
        action_log(request.user.username, action_description)
        return JsonResponse(user_data)
    action_description = f"tried to view {user.username} info\n"
    user_log(request.user.username, action_description)
    action_log(request.user.username, action_description)
    return JsonResponse({"error": "You are not allowed to view this page"})


@login_required
def access_info(request, user_id):
    user = get_object_or_404(KVM_user, pk=user_id)
    if request.user.is_superuser or user.username == request.user.username:
        duration = datetime.now() - user.start_time
        first_name = (
            DjangoUser.objects.filter(username=user.username).first().first_name
        )
        last_name = DjangoUser.objects.filter(username=user.username).first().last_name
        email = DjangoUser.objects.filter(username=user.username).first().email
        # Calculate the total number of seconds
        total_seconds = int(duration.total_seconds())

        # Convert the duration to hours, minutes, and seconds
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        # Format the result as a string
        active_for = f"{hours}h {minutes}m {seconds}s"
        user_data = {
            "username": user.username,
            "password": user.password,
            "start_time": user.start_time.strftime("%d-%m-%Y %H:%M:%S"),
            "active_for": active_for,
            "issued_by": user.issued_by.username,
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
        }
        action_description = f"viewed {user.username} access info\n"
        user_log(request.user.username, action_description)
        action_log(request.user.username, action_description)
        return JsonResponse(user_data)
    action_description = f"tried to view {user.username} access info\n"
    user_log(request.user.username, action_description)
    action_log(request.user.username, action_description)
    return HttpResponseForbidden("You are not allowed to view this page")


@login_required
@user_passes_test(lambda u: u.is_superuser)
def delete_user(request, user_id):
    user = get_object_or_404(DjangoUser, pk=user_id)
    kvm_user = get_object_or_404(KVM_user, username=user.username)
    user.delete()
    kvm_user.delete()
    action_description = f"deleted {user.username}\n"
    user_log(request.user.username, action_description)
    action_log(request.user.username, action_description)
    return JsonResponse({"success": True})


@login_required
@user_passes_test(lambda u: u.is_superuser)
def remove_access(request, user_id):
    user = get_object_or_404(KVM_user, pk=user_id)
    cross = Cross.objects.get(user=user)
    cross.user = None
    cross.kvm_port_active = False
    cross.save()
    user.delete()
    action_description = f"removed {user.username} access\n"
    user_log(request.user.username, action_description)
    action_log(request.user.username, action_description)
    return JsonResponse({"success": True})


def logging(request):
    logs = KVM_user.objects.all().order_by("-start_time")
    logs_list = [
        {
            "user": log.username,
            "start_time": log.start_time.strftime("%d-%m-%Y %H:%M:%S"),
            "KVM": Cross.objects.get(user=log.id).kvm_id.short_name,
            "id": log.id,
        }
        for log in logs
    ]
    context = {"logs": logs_list}
    return render(request, "logs.html", context)


class CreateServerRoom(UserPassesTestMixin, CreateView):
    model = ServerRoom
    form_class = CreateServerRoomForm
    template_name = "serverroom_form.html"
    success_url = reverse_lazy("kvmwebapp:index")

    def test_func(self):
        return self.request.user.is_superuser

    def form_valid(self, form):
        # Call the parent class's form_valid() method to save the form data
        response = super().form_valid(form)

        # Now that the form data is saved, populate the room
        for row in range(1, self.object.num_rows + 1):
            for rack in range(1, self.object.num_racks + 1):
                for rack_port in range(1, self.object.ports_per_rack + 1):
                    Cross.objects.create(
                        row=row,
                        rack=rack,
                        rack_port=rack_port,
                        server_room=self.object,
                        kvm_port_active=False,
                        kvm_id=self.object.kvm_id,
                    )
        kvm = KVM.objects.get(id=self.object.kvm_id.id)
        kvm.server_room_id = self.object
        kvm.save()
        action_description = f"created server room - {self.object.name}\n"
        user_log(self.request.user.username, action_description)
        action_log(self.request.user.username, action_description)
        return response


class UpdateServerRoom(UserPassesTestMixin, UpdateView):
    model = ServerRoom
    form_class = CreateServerRoomForm
    template_name = "serverroom_form.html"
    success_url = reverse_lazy("kvmwebapp:index")

    def test_func(self):
        return self.request.user.is_superuser

    def update_crosses(self):
        # Update or create crosses
        for row in range(1, self.object.num_rows + 1):
            for rack in range(1, self.object.num_racks + 1):
                for rack_port in range(1, self.object.ports_per_rack + 1):
                    Cross.objects.get_or_create(
                        row=row,
                        rack=rack,
                        rack_port=rack_port,
                        server_room=self.object,
                        defaults={
                            "kvm_port_active": False,
                            "kvm_id": self.object.kvm_id,
                        },
                    )

        # Delete extra crosses
        Cross.objects.filter(
            Q(server_room=self.object)
            & (
                Q(row__gt=self.object.num_rows)
                | Q(rack__gt=self.object.num_racks)
                | Q(rack_port__gt=self.object.ports_per_rack)
            )
        ).delete()

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.update_crosses()
        self.object.save()
        action_description = f"updated Server Room - {self.object.name}\n"
        user_log(self.request.user.username, action_description)
        action_log(self.request.user.username, action_description)
        return HttpResponseRedirect(self.get_success_url())


class CreateKVM(UserPassesTestMixin, CreateView):
    model = KVM
    form = CreateKVMForm
    fields = ["fqdn", "short_name", "ip", "number_of_ports"]
    template_name = "kvm_form.html"
    success_url = reverse_lazy("kvmwebapp:index")

    def test_func(self):
        return self.request.user.is_superuser


class ServerRoomListView(ListView):
    model = ServerRoom
    template_name = "serverroom_list.html"
    context_object_name = "server_rooms"


@login_required
def delete_server_room(request, *args, **kwargs):
    server_room = get_object_or_404(ServerRoom, pk=kwargs["room_id"])
    if request.user.is_superuser:
        server_room.delete()
        action_description = f"deleted Server Room - {server_room.name}\n"
        user_log(request.user.username, action_description)
        action_log(request.user.username, action_description)
        return redirect("kvmwebapp:index")
    action_description = f"tried to delete Server Room - {server_room.name}\n"
    user_log(request.user.username, action_description)
    messages.error(request, 'Permission denied.')
    return redirect('kvmwebapp:sroom_list')


class KVMListView(ListView):
    model = KVM
    template_name = "kvm_list.html"
    context_object_name = "kvm_list"


@login_required
def delete_kvm(request, *args, **kwargs):
    kvm = get_object_or_404(KVM, pk=kwargs["kvm_id"])
    if request.user.is_superuser:
        kvm.delete()
        action_description = f"deleted KVM - {kvm.short_name}\n"
        user_log(request.user.username, action_description)
        action_log(request.user.username, action_description)
        return redirect("kvmwebapp:index")
    action_description = f"tried to delete KVM - {kvm.short_name}\n"
    user_log(request.user.username, action_description)
    action_log(request.user.username, action_description)
    messages.error(request, 'Permission denied.')
    return redirect('kvmwebapp:kvm_list')


def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(username=username, password=password)
            if user is not None:
                action_description = f"logged in\n"
                user_log(user.username, action_description)
                action_log(user.username, action_description)
                login(request, user)
                return redirect("kvmwebapp:index")
            else:
                action_description = f"tried to log in\n"
                user_log(username, action_description)
                action_log(username, action_description)
                messages.error(request, "Invalid username or password.")
                print("Form errors:", form.errors)
        else:
            messages.error(request, "Invalid username or password.")
            print("Form errors:", form.errors)
    form = AuthenticationForm()
    return render(request, "login.html", {"form": form})


@login_required
def register(request):
    if request.method == "POST":
        form = DjangoUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password"])
            user.save()
            action_description = f"registered user - {user.username}\n"
            user_log(request.user.username, action_description)
            action_log(request.user.username, action_description)
            # login(request, user)
            return redirect(
                "kvmwebapp:index"
            )  # Replace 'home' with the name of the view you want to redirect to after registration
        else:
            print("Form errors:", form.errors)
            return HttpResponse(f"Form errors: {str(form.errors)}")
    else:
        if request.user.is_superuser:
            form = DjangoUserCreationForm()
            return render(request, "register.html", {"form": form})
        return HttpResponseForbidden("You are not allowed to view this page")


def logout_view(request):
    action_description = f"logged out\n"
    user_log(request.user.username, action_description)
    action_log(request.user.username, action_description)
    logout(request)
    return redirect(
        "kvmwebapp:login"
    )  # Replace 'login' with the name of the view you want to redirect to after logout


class UserListView(ListView):
    model = DjangoUser
    ordering = ["username"]
    template_name = "user_list.html"
    context_object_name = "user_list"


from django.urls import reverse


def toggle_rack_port_active(request, *args, **kwargs):
    cross = Cross.objects.get(
        row=int(request.GET["row"]),
        rack=int(request.GET["rack"]),
        rack_port=int(request.GET["rack_port"]),
        server_room=int(request.GET["server_room"]),
    )
    if request.user.is_superuser:
        cross.rack_port_active = not cross.rack_port_active
        cross.save()
        action_description = (
            f"toggled rack port active to {cross.rack_port_active} - {cross}\n"
        )
        user_log(request.user.username, action_description)
        action_log(request.user.username, action_description)
        server_room_url = reverse("kvmwebapp:server_room", args=[cross.server_room.id])
        return redirect(server_room_url)
    action_description = (
        f"tried to toggle rack port active to {cross.rack_port_active} - {cross}\n"
    )
    user_log(request.user.username, action_description)
    action_log(request.user.username, action_description)
    messages.error(request, 'Permission denied.')
    return redirect('kvmwebapp:index')


class SelectKVMPortView(UserPassesTestMixin, FormView):
    template_name = "select_kvm_port.html"
    form_class = SelectKVMPortForm
    success_url = reverse_lazy("kvmwebapp:index")

    def test_func(self):
        return self.request.user.is_superuser

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cross_id = self.kwargs["cross_id"]
        cross = get_object_or_404(Cross, id=cross_id)
        context["cross"] = cross
        context["kvm_ports"] = range(1, cross.kvm_id.number_of_ports + 1)
        context["is_superuser"] = self.request.user.is_superuser
        return context

    def form_valid(self, form):
        cross_id = self.kwargs["cross_id"]
        cross = get_object_or_404(Cross, id=cross_id)
        kvm_port = form.cleaned_data["kvm_port"]
        cross.kvm_port = kvm_port
        cross.kvm_port_active = True
        cross.save()
        action_description = f"selected KVM port number {cross.kvm_port} - {cross}\n"
        user_log(self.request.user.username, action_description)
        action_log(self.request.user.username, action_description)
        return super().form_valid(form)
