from datetime import datetime

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core import serializers
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import generic, View
from django.views.generic import TemplateView

from kvmwebapp.models import Cross, CrossFilter, User, KVM
from .forms import UserForm


from django.shortcuts import render, get_object_or_404, redirect


def create_port_list(filtered_cross_list):
    port_list = []
    for row in range(1, 5):
        for rack in range(1, 15):
            for rack_port in range(1, 3):
                port_info = {'row': row, 'rack': rack, 'rack_port': rack_port, 'kvm_port': '-', 'short_name': '-',
                             'username': '-', 'start_time': '-'}
                cross_queryset = filtered_cross_list.filter(row=row, rack=rack, rack_port=rack_port)
                for cross in cross_queryset:
                    port_info['kvm_port'] = cross.kvm_port if cross.kvm_port else '-'
                    port_info['server_room'] = cross.server_room
                    if cross.kvm_id:
                        port_info['short_name'] = cross.kvm_id.short_name
                        if cross.user:
                            port_info['username'] = cross.user.username
                            port_info['start_time'] = cross.user.start_time.strftime('%Y-%m-%d %H:%M:%S')
                            port_info['user_id'] = cross.user.id
                    else:
                        port_info['short_name'] = '-'
                        port_info['username'] = '-'
                port_list.append(port_info)
    return port_list


class IndexView1(TemplateView):
    template_name = "base.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get all Cross objects and order them by row, rack, and rack_port
        cross_list = Cross.objects.select_related('kvm_id', 'user').order_by('row', 'rack', 'rack_port').filter(server_room=1)

        # Create a filter instance
        cross_filter = CrossFilter(self.request.GET, queryset=cross_list)

        # Get the filtered queryset
        filtered_cross_list = cross_filter.qs

        context['port_list'] = create_port_list(filtered_cross_list)
        context['num_racks'] = range(1, max(filtered_cross_list.values_list('rack', flat=True)) + 1)
        context['num_rows'] = range(1, max(filtered_cross_list.values_list('row', flat=True)) + 1)
        context['num_ports'] = range(1, max(filtered_cross_list.values_list('rack_port', flat=True)) + 1)
        context['logs'] = logging(request=self.request)
        # context['filter'] = cross_filter

        return context


class IndexView2(TemplateView):
    template_name = "base2.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get all Cross objects and order them by row, rack, and rack_port
        cross_list = Cross.objects.select_related('kvm_id', 'user').order_by('row', 'rack', 'rack_port').filter(server_room=2)

        # Create a filter instance
        cross_filter = CrossFilter(self.request.GET, queryset=cross_list)

        # Get the filtered queryset
        filtered_cross_list = cross_filter.qs

        context['port_list'] = create_port_list(filtered_cross_list)
        context['num_racks'] = range(1, max(filtered_cross_list.values_list('rack', flat=True)) + 1)
        context['num_rows'] = range(1, max(filtered_cross_list.values_list('row', flat=True)) + 1)
        context['num_ports'] = range(1, max(filtered_cross_list.values_list('rack_port', flat=True)) + 1)
        context['logs'] = logging(request=self.request)
        # context['filter'] = cross_filter

        return context

def create_user(request):
    print("Request POST:", request.POST)  # Debugging line
    row, rack, rack_port, server_room = getting_data(request)

    if request.method == 'POST':
        form = UserForm(request.POST)
        print("Form data:", request.POST)  # Debugging line
        if form.is_valid():
            cross = Cross.objects.get(row=int(request.POST['row']), rack=int(request.POST['rack']),
                                      rack_port=int(request.POST['rack_port']), server_room=int(request.POST['server_room']))
            user = form.save(commit=False)
            user.start_time = datetime.now()
            User = get_user_model()
            password = User.objects.make_random_password(length=10)
            user.password = make_password(password)
            user.save()
            if cross is not None:
                cross.user_id = user.id
                cross.kvm_port_active = True
                cross.save()
            return JsonResponse({'success': True, 'username': user.username, 'password': password})
        else:
            print("Form errors:", form.errors)  # Debugging line
            return JsonResponse({'errors': form.errors})
    else:
        form = UserForm()
        context = {
            'form': form,
            'row': row,
            'rack': rack,
            'rack_port': rack_port,
            'current_time': datetime.now().strftime('%H:%M'),
            'server_room': server_room,
        }
        return render(request, 'create_user.html', context)


def getting_data(request):
    row = request.GET.get('row', None)
    rack = request.GET.get('rack', None)
    rack_port = request.GET.get('rack_port', None)
    server_room = request.GET.get('server_room', None)
    print("Request GET:", request.GET)  # Debugging line

    return [row, rack, rack_port, server_room]


def create_user_success(request):
    password = request.GET.get('password', '')
    return render(request, 'create_user_success.html', {'password': password})


def user_info(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    duration = timezone.now() - user.start_time

    # Calculate the total number of seconds
    total_seconds = int(duration.total_seconds())

    # Convert the duration to hours, minutes, and seconds
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    # Format the result as a string
    active_for = f"{hours}h {minutes}m {seconds}s"
    user_data = {
        'username': user.username,
        'start_time': user.start_time.strftime('%d-%m-%Y %H:%M:%S'),
        'active_for': active_for,
    }
    return JsonResponse(user_data)


def delete_user(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    cross = Cross.objects.get(user=user)
    cross.user = None
    cross.kvm_port_active = False
    cross.save()
    user.delete()
    return JsonResponse({'success': True})


def logging(request):
    logs = User.objects.all().select_related('cross').order_by('-start_time')
    return [{'user': log.username, 'start_time': log.start_time.strftime('%d-%m-%Y %H:%M:%S'), 'KVM': Cross.objects.get(user=log.id).kvm_id.short_name} for log in logs]


def redirect_to_index(request):
    return redirect('/1')
