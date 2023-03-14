from django.contrib.auth.hashers import make_password
from django.http import JsonResponse, HttpResponseNotFound
from django.utils.crypto import get_random_string
from django.utils import timezone

from kvmwebapp.models import KVM, Cross, CrossFilter, User
from .forms import UserForm

import random
import string

from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm


def index(request):
    # Get all Cross objects and order them by row, rack, and rack_port
    cross_list = Cross.objects.all().order_by('row', 'rack', 'rack_port')

    # Create a filter instance
    cross_filter = CrossFilter(request.GET, queryset=cross_list)

    # Get the filtered queryset
    filtered_cross_list = cross_filter.qs

    # Create a list of dictionaries to store the information for each port
    port_list = []
    for row in range(1, 5):
        for rack in range(1, 15):
            for rack_port in range(1, 3):
                port_info = {'row': row, 'rack': rack, 'rack_port': rack_port, 'kvm_port': '-', 'short_name': '-',
                             'username': '-'}
                try:
                    cross_queryset = filtered_cross_list.filter(row=row, rack=rack, rack_port=rack_port)
                    for cross in cross_queryset:
                        port_info['kvm_port'] = cross.kvm_port if cross.kvm_port else '-'
                        if cross.kvm_id:
                            port_info['short_name'] = cross.kvm_id.short_name
                            if cross.user:
                                port_info['username'] = cross.user.username
                        else:
                            port_info['short_name'] = '-'
                            port_info['username'] = '-'
                    port_list.append(port_info)
                except Cross.DoesNotExist:
                    pass
                if port_info not in port_list:
                    port_list.append(port_info)

    context = {'port_list': port_list, 'num_racks': range(1, 15), 'num_rows': range(1, 5), 'num_ports': range(1, 3),
               'filter': cross_filter}

    return render(request, 'base.html', context)

def create_user(request):
    row, rack, rack_port = getting_data(request)
    cross = None

    if row is not None and rack is not None and rack_port is not None:
        cross = Cross.objects.get(row=int(row), rack=int(rack), rack_port=int(rack_port))

    if request.method == 'POST':
        form = UserForm(request.POST, cross)
        if form.is_valid():
            user = form.save(commit=False)
            user.password = make_password(User.objects.make_random_password())
            user.start_time = timezone.now()
            user.save()
            cross.user = user
            cross.kvm_port_active = True
            cross.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'errors': form.errors})
    else:
        form = UserForm(cross)
        context = {
            'form': form,
            'row': row,
            'rack': rack,
            'rack_port': rack_port,
            'current_time': timezone.now().strftime('%H:%M'),
        }
        return render(request, 'create_user.html', context)



def getting_data(request):
    row = request.GET.get('row', None)
    rack = request.GET.get('rack', None)
    rack_port = request.GET.get('rack_port', None)

    return [row, rack, rack_port]




def create_user_success(request):
    password = request.GET.get('password', '')
    return render(request, 'create_user_success.html', {'password': password})
