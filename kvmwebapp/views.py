from datetime import datetime

from django.contrib import messages
from django.contrib.auth.models import User as DjangoUser
from django.contrib.auth import get_user_model, authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import (
    TemplateView,
    CreateView,
    ListView,
    DeleteView,
    DetailView,
    UpdateView,
)
from django.shortcuts import render, get_object_or_404, redirect

from kvmwebapp.models import Cross, CrossFilter, User, ServerRoom, KVM
from .forms import (
    KVMAccessForm,
    CreateServerRoomForm,
    CreateKVMForm,
    DjangoUserCreationForm,
)


def create_port_list(filtered_cross_list, server_room_number):
    port_list = []
    for row in range(1, 5):
        for rack in range(1, 15):
            for rack_port in range(1, 3):
                port_info = {
                    "row": row,
                    "rack": rack,
                    "rack_port": rack_port,
                    "kvm_port": "-",
                    "short_name": "-",
                    "username": "-",
                    "start_time": "-",
                    "server_room": "-",
                }
                cross_queryset = filtered_cross_list.filter(
                    row=row,
                    rack=rack,
                    rack_port=rack_port,
                    server_room=server_room_number,
                )
                for cross in cross_queryset:
                    port_info["kvm_port"] = cross.kvm_port if cross.kvm_port else "-"
                    port_info["server_room"] = cross.server_room.id
                    cross.kvm_id = cross.server_room.kvm_id
                    if cross.kvm_id:
                        port_info["short_name"] = cross.server_room.kvm_id.short_name
                        if cross.user:
                            port_info["username"] = cross.user.username
                            port_info["start_time"] = cross.user.start_time.strftime(
                                "%Y-%m-%d %H:%M:%S"
                            )
                            port_info["user_id"] = cross.user.id
                    else:
                        port_info["short_name"] = "-"
                        port_info["username"] = "-"
                if port_info["server_room"] == server_room_number:
                    port_list.append(port_info)
    return port_list


# class IndexView(TemplateView):
#     template_name = "base.html"
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#
#         server_rooms = ServerRoom.objects.all()
#         # Get all Cross objects and order them by row, rack, and rack_port
#         cross_list = Cross.objects.select_related('kvm_id', 'user').order_by('row', 'rack', 'rack_port')
#
#         # Create a filter instance
#         cross_filter = CrossFilter(self.request.GET, queryset=cross_list)
#
#         # Get the filtered queryset
#         filtered_cross_list = cross_filter.qs
#
#         context['port_list'] = create_port_list(filtered_cross_list)
#         context['num_racks'] = range(1, max(filtered_cross_list.values_list('rack', flat=True)) + 1)
#         context['num_rows'] = range(1, max(filtered_cross_list.values_list('row', flat=True)) + 1)
#         context['num_ports'] = range(1, max(filtered_cross_list.values_list('rack_port', flat=True)) + 1)
#         context['logs'] = logging(request=self.request)
#         context['server_rooms'] = server_rooms
#         # context['filter'] = cross_filter
#
#         return context


class IndexView(LoginRequiredMixin, TemplateView):
    template_name = "base.html"

    def get(self, request, *args, **kwargs):
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
            server_room = 1

        logs = User.objects.filter(cross__server_room_id=server_room).order_by(
            "-start_time"
        )
        # Get all Cross objects and order them by row, rack, and rack_port
        cross_list = (
            Cross.objects.filter(server_room_id=server_room)
            .select_related("kvm_id", "user", "server_room")
            .order_by("row", "rack", "rack_port", "server_room")
        )
        num_racks = max(cross_list.values_list("rack", flat=True))
        num_rows = max(cross_list.values_list("row", flat=True))

        # Create a filter instance
        cross_filter = CrossFilter(self.request.GET, queryset=cross_list)

        # Get the filtered queryset
        filtered_cross_list = cross_filter.qs

        context["port_list"] = create_port_list(filtered_cross_list, server_room)
        context["num_racks"] = range(1, num_racks + 1)

        context["num_rows"] = range(1, num_rows + 1)

        context["num_ports"] = range(
            1, max(filtered_cross_list.values_list("rack_port", flat=True)) + 1
        )
        context["logs"] = [
            {
                "user": log.username,
                "start_time": log.start_time.strftime("%d-%m-%Y %H:%M:%S"),
                "KVM": Cross.objects.get(user=log.id).kvm_id.short_name,
            }
            for log in logs
        ]
        context[
            "current_server_room"
        ] = server_room  # Add the current server_room to the context

        return context


@login_required
def give_kvm_access(request, *args, **kwargs):
    row, rack, rack_port, server_room = getting_data(request)

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
            email = user.email
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
            return JsonResponse(
                {
                    "success": True,
                    "username": user.username,
                    "password": user.password,
                    "first_name": first_name,
                    "last_name": last_name,
                    "email": email,
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

    user_data = {
        "username": user.username,
        "password": user.password,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
    }
    return JsonResponse(user_data)


def access_info(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    print(user.__dict__)
    duration = timezone.now() - user.start_time
    first_name = DjangoUser.objects.filter(username=user.username).first().first_name
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
    return JsonResponse(user_data)


class UserDetailView(DetailView):
    model = User
    template_name = "user_detail.html"


@login_required
@user_passes_test(lambda u: u.is_superuser)
def delete_user(request, user_id):
    user = get_object_or_404(DjangoUser, pk=user_id)
    user.delete()
    return JsonResponse({"success": True})


@login_required
@user_passes_test(lambda u: u.is_superuser)
def remove_access(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    cross = Cross.objects.get(user=user)
    cross.user = None
    cross.kvm_port_active = False
    cross.save()
    user.delete()
    return JsonResponse({"success": True})


def logging(request):
    logs = User.objects.all().order_by("-start_time")
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
        return response


class UpdateServerRoom(UserPassesTestMixin, UpdateView):
    model = ServerRoom
    form_class = CreateServerRoomForm
    template_name = "serverroom_form.html"
    success_url = reverse_lazy("kvmwebapp:index")

    def test_func(self):
        return self.request.user.is_superuser

    def remove_crosses(self):
        crosses = Cross.objects.filter(server_room=self.object)
        print(len(crosses))
        crosses.delete()


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
@user_passes_test(lambda u: u.is_superuser)
def delete_server_room(*args, **kwargs):
    server_room = get_object_or_404(ServerRoom, pk=kwargs["room_id"])
    server_room.delete()
    return redirect("kvmwebapp:index")


class KVMListView(ListView):
    model = KVM
    template_name = "kvm_list.html"
    context_object_name = "kvm_list"


@login_required
@user_passes_test(lambda u: u.is_superuser)
def delete_kvm(*args, **kwargs):
    kvm = get_object_or_404(KVM, pk=kwargs["kvm_id"])
    kvm.delete()
    return redirect("kvmwebapp:index")


def login_view(request):
    print("Login view called")  # Debug print
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            print("Form is valid")  # Debug print
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect("kvmwebapp:index")
            else:
                messages.error(request, "Invalid username or password.")
                print("Form errors:", form.errors)
        else:
            messages.error(request, "Invalid username or password.")
            print("Form errors:", form.errors)
    form = AuthenticationForm()
    return render(request, "login.html", {"form": form})


@login_required
@user_passes_test(lambda u: u.is_superuser)
def register(request):
    if request.method == "POST":
        form = DjangoUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password"])
            user.save()
            # login(request, user)
            return redirect(
                "kvmwebapp:index"
            )  # Replace 'home' with the name of the view you want to redirect to after registration
    else:
        form = DjangoUserCreationForm()
    return render(request, "register.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect(
        "kvmwebapp:index"
    )  # Replace 'login' with the name of the view you want to redirect to after logout


class UserListView(ListView):
    model = DjangoUser
    ordering = ["username"]
    template_name = "user_list.html"
    context_object_name = "user_list"
