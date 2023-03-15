from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.http import JsonResponse, HttpResponseNotFound
from django.utils.crypto import get_random_string
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.generic import TemplateView

from kvmwebapp.models import KVM, Cross, CrossFilter, User
from .forms import UserForm

import random
import string

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm


# def index(request):
#
#     # Get all Cross objects and order them by row, rack, and rack_port
#     cross_list = Cross.objects.all().order_by('row', 'rack', 'rack_port')
#
#     # Create a filter instance
#     cross_filter = CrossFilter(request.GET, queryset=cross_list)
#
#     # Get the filtered queryset
#     filtered_cross_list = cross_filter.qs
#
#     # Create a list of dictionaries to store the information for each port
#     port_list = []
#     for row in range(1, 5):
#         for rack in range(1, 15):
#             for rack_port in range(1, 3):
#                 port_info = {'row': row, 'rack': rack, 'rack_port': rack_port, 'kvm_port': '-', 'short_name': '-',
#                              'username': '-'}
#                 try:
#                     cross_queryset = filtered_cross_list.filter(row=row, rack=rack, rack_port=rack_port)
#                     for cross in cross_queryset:
#                         port_info['kvm_port'] = cross.kvm_port if cross.kvm_port else '-'
#                         if cross.kvm_id:
#                             port_info['short_name'] = cross.kvm_id.short_name
#                             if cross.user:
#                                 port_info['username'] = cross.user.username
#                         else:
#                             port_info['short_name'] = '-'
#                             port_info['username'] = '-'
#                     port_list.append(port_info)
#                 except Cross.DoesNotExist:
#                     pass
#                 if port_info not in port_list:
#                     port_list.append(port_info)
#
#     context = {'port_list': port_list, 'num_racks': range(1, 15), 'num_rows': range(1, 5), 'num_ports': range(1, 3),
#                'filter': cross_filter}
#
#     return render(request, 'base.html', context)

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
                    if cross.kvm_id:
                        port_info['short_name'] = cross.kvm_id.short_name
                        if cross.user:
                            port_info['username'] = cross.user.username
                            port_info['start_time'] = cross.user.start_time.strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        port_info['short_name'] = '-'
                        port_info['username'] = '-'
                port_list.append(port_info)
    return port_list


class IndexView(TemplateView):
    template_name = "base.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get all Cross objects and order them by row, rack, and rack_port
        cross_list = Cross.objects.select_related('kvm_id', 'user').order_by('row', 'rack', 'rack_port')
        # for i in cross_list:
        #     print(i.__dict__)

        # Create a filter instance
        cross_filter = CrossFilter(self.request.GET, queryset=cross_list)
        for i in cross_filter.qs:
            if i.user_id:
                print(User.objects.get(id=i.user_id).start_time)

        # Get the filtered queryset
        filtered_cross_list = cross_filter.qs

        context['port_list'] = create_port_list(filtered_cross_list)
        context['num_racks'] = range(1, 15)
        context['num_rows'] = range(1, 5)
        context['num_ports'] = range(1, 3)
        context['filter'] = cross_filter

        return context
def create_user(request):
    # cross = None
    row, rack, rack_port = getting_data(request)
    print(getting_data(request))  # Debugging line

    # if row is not None and rack is not None and rack_port is not None:


    if request.method == 'POST':
        form = UserForm(request.POST)
        print("Form data:", request.POST)  # Debugging line
        if form.is_valid():
            cross = Cross.objects.get(row=int(request.POST['row']), rack=int(request.POST['rack']),
                                      rack_port=int(request.POST['rack_port']))
            user = form.save(commit=False)
            user.start_time = timezone.now()
            User = get_user_model()
            user.password = make_password(User.objects.make_random_password())
            user.save()
            if cross is not None:
                cross.user_id = user.id
                cross.kvm_port_active = True
                cross.save()
            return JsonResponse({'success': True, 'username': user.username, 'password': user.password})
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
