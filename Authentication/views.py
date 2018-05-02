import datetime
import json
from django.contrib import messages
from permission import group_required
from django.contrib.auth.hashers import make_password
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group,User
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db import IntegrityError
from django.http import HttpResponseRedirect, Http404, HttpResponse, JsonResponse
from django.shortcuts import render, render_to_response, redirect
from django.template import RequestContext, context
from django.urls import reverse_lazy
from django.utils.datastructures import MultiValueDictKeyError
from django.views.generic import DeleteView

from Authentication.forms import CurrentAddressForm, PermanentAddressForm, AddVehicleForm,DriverLogin, BorrowVehicleForm
from Authentication.models import Address, UserProfile, Vehicle, TrackVehicle
from django.contrib.auth import logout, authenticate, login


# def index(request):
#     return render_to_response("base.html",
#                               RequestContext(request))

# Create your views here.
@login_required
def address_view(request):
    # if this is a POST request we need to process the form data
    # cur_form,per_form = 0,0
    cur_form = 0
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        cur_form = CurrentAddressForm(request.POST)
        # per_form = PermanentAddressForm(request.POST)
        # check whether it's valid:
        if cur_form.is_valid():
            #current address form reading


            phone_number = cur_form.cleaned_data['phone_number']
            district = cur_form.cleaned_data['district']
            sub_district = cur_form.cleaned_data['sub_district']
            city = cur_form.cleaned_data['city']
            zip = cur_form.cleaned_data['zip']
            user_type = cur_form.cleaned_data['user_type']
            print(user_type)
            print("Working it")
            print(district)
            user_profile = None
            if request.user.is_authenticated:
                #user_profile = UserProfile( user=request.user )
                user_profile = request.user
                # if request.user.is_authenticated():
                #     user = request.user
                if str(user_type) == 'client':
                    #user_profile  =  request.user
                    group = Group.objects.get( name='Client' )
                    user_profile .groups.add( group )
                else:
                    #user_profile  =  request.user
                    group = Group.objects.get( name='Owner' )
                    user_profile .groups.add( group )
            current_address = Address.objects.create(district=district, sub_district=sub_district, city=city, zip=zip,phone_number =  phone_number)
            #user_profile.current_ = current_address
            current_address.user = user_profile
            current_address.save()
            #
            #
            # phone_number = per_form.cleaned_data['phone_number']
            # district = per_form.cleaned_data['district']
            # sub_district = per_form.cleaned_data['sub_district']
            # city = per_form.cleaned_data['city']
            # zip = per_form.cleaned_data['zip']
            # permanent_address = Address.objects.create( district=district, sub_district=sub_district, city=city, zip=zip,phone_number = phone_number )
            # print(district)
            # profile.permanent_address = permanent_address
            # profile.save()

        else:
            cur_form = CurrentAddressForm()
            # per_form = CurrentAddressForm()



        return HttpResponseRedirect('/')

    # if a GET (or any other method) we'll create a blank form
    else:
        cur_form = CurrentAddressForm()
        # per_form  = PermanentAddressForm()

    return render(request, 'AddressFormSheet.html', {'cur_form': cur_form})

@login_required
@group_required('Owner')
def add_vehicle_view(request):
    if request.method == 'POST':
        add_veh = AddVehicleForm(request.POST)
        if add_veh.is_valid():
            try:
                license_no = add_veh.cleaned_data['license_no']
                chassis_no = add_veh.cleaned_data['chassis_no']
                driver_code = add_veh.cleaned_data['driver_code']
                #journey_date = add_veh.cleaned_data['journey_date']
                capacity = add_veh.cleaned_data['capacity']
                model = add_veh.cleaned_data['model']
                passwd_veh = add_veh.cleaned_data['vehicle_password']
                place = add_veh.cleaned_data["place"]
                passwd_hashed = make_password(str(passwd_veh))
                print("Time")
                user_profile = None
                # if request.user.is_authenticated():
                # user_profile = request.userauth_group_permissions
                user_profile = request.user
                #print(journey_date)
                vehicle = Vehicle.objects.create( license_no = license_no, chassis_no = chassis_no,
                                                  journey_date=datetime.date.today(),capacity=capacity, model=model, place= place)
                vehicle.user = user_profile
                group = Group.objects.get( name='Driver' )

                driver_user = User.objects.create( username= driver_code, password=passwd_hashed,is_active= True)
                # vehicle.driver_code_name.username = driver_code
                # vehicle.driver_code_name.password = passwd_veh
                # vehicle.driver_code_name.is_active = True
                vehicle.driver_code_name = driver_user
                driver_user.groups.add( group )
                driver_user.save()
                vehicle.save()
                veh_track = TrackVehicle.objects.create(latitude=None, longitude=None,this_vehicle= vehicle )
                veh_track.save()

            except IntegrityError as e:
                return HttpResponseRedirect( '/accounts/add_vehicle' )
        messages.info( request, 'You have added the vehicle successfully!' )
        # return HttpResponseRedirect( '/accounts/add_vehicle' )
        return redirect( add_vehicle_view)
    else:
        add_veh = AddVehicleForm()
    #messages.info( request, 'You have added the vehicle successfully!' )
    return  render(request, 'AddVehicleFormSheet.html', {'add_veh': add_veh})

@login_required
@group_required('Client')
def borrow_vehicle_view(request):
    borr_veh = None
    if request.method == 'POST':
        borr_veh = BorrowVehicleForm(request.POST)
        if borr_veh.is_valid():
            journey_date = borr_veh.cleaned_data['journey_date']
            capacity = borr_veh.cleaned_data['capacity']
            current_place = borr_veh.cleaned_data['current_place']
            destination_place = borr_veh.cleaned_data['destination_place']
            request.session['capacity'] = float(capacity)
            request.session['journey_date'] = str(journey_date)
            request.session['current_place'] = str(current_place)
            request.session['destination_place'] = str(destination_place)
            print(journey_date)
            print("Time")
            # user_profile = None
            # if request.user.is_authenticated():
            #   user_profile = request.user
            # print(journey_date)
            # vehicle = Vehicle.objects.create( license_no = license_no, chassis_no = chassis_no,
            #                                   journey_date=journey_date,capacity=capacity, model=model)
            # vehicle.user = user_profile
            # vehicle.save()
        return HttpResponseRedirect( '/accounts/borrow_vehicle_list' )
    else:
        borr_veh = BorrowVehicleForm()

    return  render(request, 'BorrowVehicleFormSheet.html', {'borr_veh': borr_veh})

@login_required
@group_required('Client')
def borrow_vehicle_list_view(request):
    _capacity = request.session.get('capacity')
    _journey_date = request.session.get('journey_date')
    borrow_vehicle_list = Vehicle.objects.filter( capacity__gte= _capacity ).exclude(journey_date__lte=_journey_date).exclude(client_id__isnull=False)
    page = request.GET.get('page', 1)
    #borrow_vehicle = None
    paginator = Paginator(borrow_vehicle_list,2)
    try:
        borrow_vehicle = paginator.page(page)
    except PageNotAnInteger:
        borrow_vehicle = paginator.page(1)
    except EmptyPage:
        borrow_vehicle = paginator.page(paginator.num_pages)
    return render( request, 'BorrowVehicleListSheet.html', {'borrow_vehicle': borrow_vehicle} )

@login_required
@group_required('Client')
def borrow_vehicle_details_view(request, pk):
    prices=0
    try:
        vehicle = Vehicle.objects.get( pk=pk )
        price = {'Dhaka': {'Dhaka': 0, 'Bagerhat': 178, 'Bandarbon': 316, 'Barguna': 247, 'Barishal': 169, 'Bhola': 205,
                           'Bogra': 109, 'Brahmanbaria': 109, 'Chandpur': 115, 'Chittagong': 242, 'Chuadanga': 215,
                           'Comilla': 96, 'Coxs Bazar': 391, 'Dinajpur': 338, 'Faridpur': 101, 'Feni': 149,
                           'Gaibandha': 268, 'Gazipur': 37, 'Gopalganj': 127, 'Habijang': 163, 'Jamalpur': 179,
                           'Jessore': 164, 'Jhalokhati': 182, 'Jhenaidah': 178, 'Joypurhat': 249, 'Khagrachhari': 259,
                           'Khulna': 184, 'Kishoreganj': 117, 'Kurigram': 348, 'Kushtia': 183, 'Lakshimpur': 137,
                           'Lalmonirhat': 343, 'Madaripur': 90, 'Magura': 150, 'Manikjang': 63, 'Meherpur': 240,
                           'Moulvibazar': 203, 'Munshiganj': 27, 'Mymensing': 122, 'Naogan': 247, 'Narail': 130,
                           'Naraynganj': 17, 'Narsingdhi': 51, 'Natore': 210, 'Nawabganj': 302, 'Netrokona': 158,
                           'Nilphamari': 359, 'Noakhali': 158, 'Pabna': 216, 'Panchagrah': 443, 'Patuakhali': 204,
                           'Pirojpur': 185, 'Rajbari': 118, 'Rajshahi': 256, 'Rangamati': 293, 'Rangpur': 304,
                           'Satkhira': 240, 'Shariatpur': 101, 'Sherpur': 188, 'Sirajganj': 134, 'Sunamjang': 296,
                           'Sylhet': 241, 'Tangail': 92, 'Thakurgaon': 407},
                 'Bagerhat': {'Dhaka': 178, 'Bagerhat': 0, 'Bandarbon': 437, 'Barguna': 160, 'Barishal': 119,
                              'Bhola': 205, 'Bogra': 155, 'Brahmanbaria': 283, 'Chandpur': 182, 'Chittagong': 363,
                              'Chuadanga': 175, 'Comilla': 269, 'Coxs Bazar': 512, 'Dinajpur': 467, 'Faridpur': 140,
                              'Feni': 270, 'Gaibandha': 397, 'Gazipur': 215, 'Gopalganj': 52, 'Habijang': 336,
                              'Jamalpur': 357, 'Jessore': 93, 'Jhalokhati': 100, 'Jhenaidah': 139, 'Joypurhat': 139,
                              'Khagrachhari': 381, 'Khulna': 34, 'Kishoreganj': 290, 'Kurigram': 477, 'Kushtia': 184,
                              'Lakshimpur': 209, 'Lalmonirhat': 472, 'Madaripur': 110, 'Magura': 136, 'Manikjang': 200,
                              'Meherpur': 201, 'Moulvibazar': 376, 'Munshiganj': 179, 'Mymensing': 300, 'Naogan': 357,
                              'Narail': 107, 'Naraynganj': 186, 'Narsingdhi': 225, 'Natore': 260, 'Nawabganj': 352,
                              'Netrokona': 336, 'Nilphamari': 488, 'Noakhali': 244, 'Pabna': 234, 'Panchagrah': 572,
                              'Patuakhali': 151, 'Pirojpur': 66, 'Rajbari': 167, 'Rajshahi': 306, 'Rangamati': 415,
                              'Rangpur': 433, 'Satkhira': 94, 'Shariatpur': 134, 'Sherpur': 366, 'Sirajganj': 311,
                              'Sunamjang': 470, 'Sylhet': 414, 'Tangail': 270, 'Thakurgaon': 536},
                 'Bandarbon': {'Dhaka': 316, 'Bagerhat': 437, 'Bandarbon': 0, 'Barguna': 469, 'Barishal': 391,
                               'Bhola': 427, 'Bogra': 510, 'Brahmanbaria': 301, 'Chandpur': 271, 'Chittagong': 85,
                               'Chuadanga': 526, 'Comilla': 225, 'Coxs Bazar': 121, 'Dinajpur': 651, 'Faridpur': 413,
                               'Feni': 167, 'Gaibandha': 581, 'Gazipur': 350, 'Gopalganj': 386, 'Habijang': 376,
                               'Jamalpur': 492, 'Jessore': 476, 'Jhalokhati': 404, 'Jhenaidah': 490, 'Joypurhat': 563,
                               'Khagrachhari': 133, 'Khulna': 439, 'Kishoreganj': 379, 'Kurigram': 661, 'Kushtia': 499,
                               'Lakshimpur': 229, 'Lalmonirhat': 656, 'Madaripur': 327, 'Magura': 461, 'Manikjang': 379,
                               'Meherpur': 552, 'Moulvibazar': 416, 'Munshiganj': 329, 'Mymensing': 436, 'Naogan': 561,
                               'Narail': 442, 'Naraynganj': 314, 'Narsingdhi': 339, 'Natore': 524, 'Nawabganj': 616,
                               'Netrokona': 444, 'Nilphamari': 672, 'Noakhali': 208, 'Pabna': 530, 'Panchagrah': 757,
                               'Patuakhali': 426, 'Pirojpur': 438, 'Rajbari': 434, 'Rajshahi': 569, 'Rangamati': 74,
                               'Rangpur': 618, 'Satkhira': 499, 'Shariatpur': 317, 'Sherpur': 501, 'Sirajganj': 447,
                               'Sunamjang': 509, 'Sylhet': 454, 'Tangail': 406, 'Thakurgaon': 720},
                 'Barguna': {'Dhaka': 247, 'Bagerhat': 160, 'Bandarbon': 469, 'Barguna': 0, 'Barishal': 84, 'Bhola': 36,
                             'Bogra': 366, 'Brahmanbaria': 273, 'Chandpur': 135, 'Chittagong': 317, 'Chuadanga': 244,
                             'Comilla': 202, 'Coxs Bazar': 465, 'Dinajpur': 505, 'Faridpur': 131, 'Feni': 244,
                             'Gaibandha': 202, 'Gazipur': 465, 'Gopalganj': 196, 'Habijang': 505, 'Jamalpur': 426,
                             'Jessore': 209, 'Jhalokhati': 95, 'Jhenaidah': 286, 'Joypurhat': 495, 'Khagrachhari': 413,
                             'Khulna': 150, 'Kishoreganj': 360, 'Kurigram': 594, 'Kushtia': 301, 'Lakshimpur': 241,
                             'Lalmonirhat': 589, 'Madaripur': 143, 'Magura': 258, 'Manikjang': 270, 'Meherpur': 348,
                             'Moulvibazar': 446, 'Munshiganj': 248, 'Mymensing': 370, 'Naogan': 473, 'Narail': 227,
                             'Naraynganj': 255, 'Narsingdhi': 294, 'Natore': 377, 'Nawabganj': 469, 'Netrokona': 406,
                             'Nilphamari': 604, 'Noakhali': 276, 'Pabna': 350, 'Panchagrah': 689, 'Patuakhali': 44,
                             'Pirojpur': 96, 'Rajbari': 236, 'Rajshahi': 423, 'Rangamati': 447, 'Rangpur': 550,
                             'Satkhira': 206, 'Shariatpur': 166, 'Sherpur': 435, 'Sirajganj': 381, 'Sunamjang': 539,
                             'Sylhet': 483, 'Tangail': 340, 'Thakurgaon': 652},
                 'Barishal': {'Dhaka': 169, 'Bagerhat': 119, 'Bandarbon': 391, 'Barguna': 84, 'Barishal': 0,
                              'Bhola': 36, 'Bogra': 366, 'Brahmanbaria': 273, 'Chandpur': 135, 'Chittagong': 317,
                              'Chuadanga': 244, 'Comilla': 202, 'Coxs Bazar': 465, 'Dinajpur': 505, 'Faridpur': 131,
                              'Feni': 244, 'Gaibandha': 202, 'Gazipur': 435, 'Gopalganj': 117, 'Habijang': 327,
                              'Jamalpur': 348, 'Jessore': 204, 'Jhalokhati': 55, 'Jhenaidah': 243, 'Joypurhat': 552,
                              'Khagrachhari': 370, 'Khulna': 145, 'Kishoreganj': 317, 'Kurigram': 551, 'Kushtia': 258,
                              'Lakshimpur': 198, 'Lalmonirhat': 546, 'Madaripur': 100, 'Magura': 215, 'Manikjang': 227,
                              'Meherpur': 306, 'Moulvibazar': 403, 'Munshiganj': 205, 'Mymensing': 327, 'Naogan': 431,
                              'Narail': 184, 'Naraynganj': 213, 'Narsingdhi': 251, 'Natore': 334, 'Nawabganj': 251,
                              'Netrokona': 334, 'Nilphamari': 426, 'Noakhali': 363, 'Pabna': 562, 'Panchagrah': 233,
                              'Patuakhali': 308, 'Pirojpur': 646, 'Rajbari': 77, 'Rajshahi': 89, 'Rangamati': 194,
                              'Rangpur': 380, 'Satkhira': 404, 'Shariatpur': 507, 'Sherpur': 200, 'Sirajganj': 123,
                              'Sunamjang': 393, 'Sylhet': 338, 'Tangail': 496, 'Thakurgaon': 441},
                 'Bhola': {'Dhaka': 205, 'Bagerhat': 155, 'Bandarbon': 427, 'Barguna': 120, 'Barishal': 36, 'Bhola': 0,
                           'Bogra': 402, 'Brahmanbaria': 309, 'Chandpur': 171, 'Chittagong': 353, 'Chuadanga': 280,
                           'Comilla': 238, 'Coxs Bazar': 501, 'Dinajpur': 541, 'Faridpur': 167, 'Feni': 260,
                           'Gaibandha': 471, 'Gazipur': 242, 'Gopalganj': 153, 'Habijang': 153, 'Jamalpur': 363,
                           'Jessore': 204, 'Jhalokhati': 55, 'Jhenaidah': 243, 'Joypurhat': 452, 'Khagrachhari': 370,
                           'Khulna': 145, 'Kishoreganj': 317, 'Kurigram': 551, 'Kushtia': 258, 'Lakshimpur': 198,
                           'Lalmonirhat': 546, 'Madaripur': 100, 'Magura': 215, 'Manikjang': 227, 'Meherpur': 306,
                           'Moulvibazar': 403, 'Munshiganj': 205, 'Mymensing': 327, 'Naogan': 431, 'Narail': 184,
                           'Naraynganj': 213, 'Narsingdhi': 251, 'Natore': 334, 'Nawabganj': 251, 'Netrokona': 334,
                           'Nilphamari': 426, 'Noakhali': 363, 'Pabna': 562, 'Panchagrah': 233, 'Patuakhali': 308,
                           'Pirojpur': 646, 'Rajbari': 77, 'Rajshahi': 89, 'Rangamati': 194, 'Rangpur': 380,
                           'Satkhira': 404, 'Shariatpur': 507, 'Sherpur': 200, 'Sirajganj': 123, 'Sunamjang': 393,
                           'Sylhet': 338, 'Tangail': 496, 'Thakurgaon': 441},
                 'Bogra': {'Dhaka': 197, 'Bagerhat': 328, 'Bandarbon': 510, 'Barguna': 445, 'Barishal': 366,
                           'Bhola': 402, 'Bogra': 0, 'Brahmanbaria': 247, 'Chandpur': 309, 'Chittagong': 437,
                           'Chuadanga': 192, 'Comilla': 291, 'Coxs Bazar': 585, 'Dinajpur': 141, 'Faridpur': 239,
                           'Feni': 344, 'Gaibandha': 71, 'Gazipur': 169, 'Gopalganj': 324, 'Habijang': 324,
                           'Jamalpur': 328, 'Jessore': 172, 'Jhalokhati': 235, 'Jhenaidah': 379, 'Joypurhat': 190,
                           'Khagrachhari': 52, 'Khulna': 454, 'Kishoreganj': 295, 'Kurigram': 201, 'Kushtia': 151,
                           'Lakshimpur': 144, 'Lalmonirhat': 331, 'Madaripur': 146, 'Magura': 287, 'Manikjang': 217,
                           'Meherpur': 188, 'Moulvibazar': 368, 'Munshiganj': 221, 'Mymensing': 178, 'Naogan': 50,
                           'Narail': 269, 'Naraynganj': 211, 'Narsingdhi': 217, 'Natore': 68, 'Nawabganj': 160,
                           'Netrokona': 217, 'Nilphamari': 162, 'Noakhali': 353, 'Pabna': 127, 'Panchagrah': 246,
                           'Patuakhali': 401, 'Pirojpur': 350, 'Rajbari': 208, 'Rajshahi': 114, 'Rangamati': 488,
                           'Rangpur': 107, 'Satkhira': 307, 'Shariatpur': 298, 'Sherpur': 188, 'Sirajganj': 72,
                           'Sunamjang': 462, 'Sylhet': 406, 'Tangail': 105, 'Thakurgaon': 210},
                 'Brahmanbaria': {'Dhaka': 109, 'Bagerhat': 283, 'Bandarbon': 301, 'Barguna': 352, 'Barishal': 273,
                                  'Bhola': 309, 'Bogra': 247, 'Brahmanbaria': 0, 'Chandpur': 143, 'Chittagong': 227,
                                  'Chuadanga': 320, 'Comilla': 81, 'Coxs Bazar': 375, 'Dinajpur': 416, 'Faridpur': 206,
                                  'Feni': 134, 'Gaibandha': 345, 'Gazipur': 114, 'Gopalganj': 231, 'Habijang': 231,
                                  'Jamalpur': 76, 'Jessore': 203, 'Jhalokhati': 269, 'Jhenaidah': 287, 'Joypurhat': 283,
                                  'Khagrachhari': 327, 'Khulna': 244, 'Kishoreganj': 285, 'Kurigram': 79,
                                  'Kushtia': 425, 'Lakshimpur': 268, 'Lalmonirhat': 164, 'Madaripur': 420,
                                  'Magura': 195, 'Manikjang': 254, 'Meherpur': 148, 'Moulvibazar': 326,
                                  'Munshiganj': 116, 'Mymensing': 123, 'Naogan': 147, 'Narail': 325, 'Naraynganj': 235,
                                  'Narsingdhi': 107, 'Natore': 67, 'Nawabganj': 288, 'Netrokona': 380,
                                  'Nilphamari': 144, 'Noakhali': 436, 'Pabna': 294, 'Panchagrah': 521,
                                  'Patuakhali': 308, 'Pirojpur': 290, 'Rajbari': 204, 'Rajshahi': 334, 'Rangamati': 382,
                                  'Rangpur': 344, 'Satkhira': 205, 'Shariatpur': 204, 'Sherpur': 211, 'Sirajganj': 209,
                                  'Sunamjang': 153, 'Sylhet': 170, 'Tangail': 484, 'Thakurgaon': 210},
                 'Chandpur': {'Dhaka': 115, 'Bagerhat': 182, 'Bandarbon': 271, 'Barguna': 214, 'Barishal': 135,
                              'Bhola': 171, 'Bogra': 309, 'Brahmanbaria': 143, 'Chandpur': 0, 'Chittagong': 198,
                              'Chuadanga': 257, 'Comilla': 67, 'Coxs Bazar': 346, 'Dinajpur': 450, 'Faridpur': 144,
                              'Feni': 105, 'Gaibandha': 380, 'Gazipur': 149, 'Gopalganj': 130, 'Habijang': 130,
                              'Jamalpur': 218, 'Jessore': 291, 'Jhalokhati': 195, 'Jhenaidah': 149, 'Joypurhat': 220,
                              'Khagrachhari': 361, 'Khulna': 215, 'Kishoreganj': 184, 'Kurigram': 221, 'Kushtia': 460,
                              'Lakshimpur': 235, 'Lalmonirhat': 43, 'Madaripur': 455, 'Magura': 71, 'Manikjang': 192,
                              'Meherpur': 177, 'Moulvibazar': 283, 'Munshiganj': 258, 'Mymensing': 128, 'Naogan': 234,
                              'Narail': 359, 'Naraynganj': 162, 'Narsingdhi': 113, 'Natore': 137, 'Nawabganj': 311,
                              'Netrokona': 403, 'Nilphamari': 270, 'Noakhali': 471, 'Pabna': 78, 'Panchagrah': 258,
                              'Patuakhali': 555, 'Pirojpur': 170, 'Rajbari': 182, 'Rajshahi': 171, 'Rangamati': 357,
                              'Rangpur': 249, 'Satkhira': 416, 'Shariatpur': 243, 'Sherpur': 62, 'Sirajganj': 300,
                              'Sunamjang': 243, 'Sylhet': 62, 'Tangail': 300, 'Thakurgaon': 246},
                 'Chittagong': {'Dhaka': 242, 'Bagerhat': 363, 'Bandarbon': 85, 'Barguna': 396, 'Barishal': 317,
                                'Bhola': 353, 'Bogra': 437, 'Brahmanbaria': 227, 'Chandpur': 198, 'Chittagong': 0,
                                'Chuadanga': 453, 'Comilla': 151, 'Coxs Bazar': 160, 'Dinajpur': 578, 'Faridpur': 339,
                                'Feni': 93, 'Gaibandha': 507, 'Gazipur': 276, 'Gopalganj': 212, 'Habijang': 312,
                                'Jamalpur': 302, 'Jessore': 418, 'Jhalokhati': 402, 'Jhenaidah': 330, 'Joypurhat': 416,
                                'Khagrachhari': 489, 'Khulna': 117, 'Kishoreganj': 366, 'Kurigram': 305, 'Kushtia': 588,
                                'Lakshimpur': 425, 'Lalmonirhat': 155, 'Madaripur': 583, 'Magura': 253,
                                'Manikjang': 387, 'Meherpur': 305, 'Moulvibazar': 478, 'Munshiganj': 342,
                                'Mymensing': 256, 'Naogan': 362, 'Narail': 487, 'Naraynganj': 368, 'Narsingdhi': 240,
                                'Natore': 265, 'Nawabganj': 450, 'Netrokona': 542, 'Nilphamari': 370, 'Noakhali': 598,
                                'Pabna': 134, 'Panchagrah': 456, 'Patuakhali': 683, 'Pirojpur': 352, 'Rajbari': 364,
                                'Rajshahi': 360, 'Rangamati': 496, 'Rangpur': 78, 'Satkhira': 544, 'Shariatpur': 425,
                                'Sherpur': 244, 'Sirajganj': 427, 'Sunamjang': 373, 'Sylhet': 436, 'Tangail': 380,
                                'Thakurgaon': 323},
                 'Chuadanga': {'Dhaka': 215, 'Bagerhat': 175, 'Bandarbon': 526, 'Barguna': 323, 'Barishal': 344,
                               'Bhola': 280, 'Bogra': 192, 'Brahmanbaria': 320, 'Chandpur': 257, 'Chittagong': 453,
                               'Chuadanga': 0, 'Comilla': 306, 'Coxs Bazar': 601, 'Dinajpur': 331, 'Faridpur': 118,
                               'Feni': 360, 'Gaibandha': 261, 'Gazipur': 237, 'Gopalganj': 312, 'Habijang': 171,
                               'Jamalpur': 373, 'Jessore': 276, 'Jhalokhati': 82, 'Jhenaidah': 231, 'Joypurhat': 37,
                               'Khagrachhari': 243, 'Khulna': 470, 'Kishoreganj': 142, 'Kurigram': 305, 'Kushtia': 341,
                               'Lakshimpur': 49, 'Lalmonirhat': 284, 'Madaripur': 336, 'Magura': 186, 'Manikjang': 65,
                               'Meherpur': 173, 'Moulvibazar': 26, 'Munshiganj': 413, 'Mymensing': 216, 'Naogan': 282,
                               'Narail': 221, 'Naraynganj': 116, 'Narsingdhi': 223, 'Natore': 262, 'Nawabganj': 124,
                               'Netrokona': 217, 'Nilphamari': 321, 'Noakhali': 352, 'Pabna': 319, 'Panchagrah': 98,
                               'Patuakhali': 437, 'Pirojpur': 279, 'Rajbari': 198, 'Rajshahi': 108, 'Rangamati': 170,
                               'Rangpur': 504, 'Satkhira': 297, 'Shariatpur': 154, 'Sherpur': 209, 'Sirajganj': 291,
                               'Sunamjang': 176, 'Sylhet': 507, 'Tangail': 451, 'Thakurgaon': 209},
                 'Comilla': {'Dhaka': 96, 'Bagerhat': 269, 'Bandarbon': 225, 'Barguna': 281, 'Barishal': 202,
                             'Bhola': 238, 'Bogra': 291, 'Brahmanbaria': 81, 'Chandpur': 67, 'Chittagong': 151,
                             'Chuadanga': 306, 'Comilla': 0, 'Coxs Bazar': 300, 'Dinajpur': 432, 'Faridpur': 193,
                             'Feni': 58, 'Gaibandha': 361, 'Gazipur': 130, 'Gopalganj': 171, 'Habijang': 218,
                             'Jamalpur': 156, 'Jessore': 272, 'Jhalokhati': 256, 'Jhenaidah': 215, 'Joypurhat': 270,
                             'Khagrachhari': 343, 'Khulna': 169, 'Kishoreganj': 272, 'Kurigram': 159, 'Kushtia': 441,
                             'Lakshimpur': 279, 'Lalmonirhat': 89, 'Madaripur': 436, 'Magura': 138, 'Manikjang': 241,
                             'Meherpur': 159, 'Moulvibazar': 332, 'Munshiganj': 196, 'Mymensing': 109, 'Naogan': 216,
                             'Narail': 341, 'Naraynganj': 222, 'Narsingdhi': 94, 'Natore': 119, 'Nawabganj': 304,
                             'Netrokona': 396, 'Nilphamari': 224, 'Noakhali': 452, 'Pabna': 67, 'Panchagrah': 310,
                             'Patuakhali': 537, 'Pirojpur': 237, 'Rajbari': 249, 'Rajshahi': 214, 'Rangamati': 350,
                             'Rangpur': 203, 'Satkhira': 398, 'Shariatpur': 331, 'Sherpur': 128, 'Sirajganj': 281,
                             'Sunamjang': 227, 'Sylhet': 290, 'Tangail': 234, 'Thakurgaon': 186},
                 'Coxs Bazar': {'Dhaka': 391, 'Bagerhat': 512, 'Bandarbon': 121, 'Barguna': 544, 'Barishal': 465,
                                'Bhola': 501, 'Bogra': 585, 'Brahmanbaria': 375, 'Chandpur': 346, 'Chittagong': 160,
                                'Chuadanga': 601, 'Comilla': 300, 'Coxs Bazar': 0, 'Dinajpur': 726, 'Faridpur': 487,
                                'Feni': 241, 'Gaibandha': 655, 'Gazipur': 425, 'Gopalganj': 218, 'Habijang': 460,
                                'Jamalpur': 450, 'Jessore': 567, 'Jhalokhati': 550, 'Jhenaidah': 479, 'Joypurhat': 564,
                                'Khagrachhari': 637, 'Khulna': 252, 'Kishoreganj': 514, 'Kurigram': 453, 'Kushtia': 736,
                                'Lakshimpur': 573, 'Lalmonirhat': 303, 'Madaripur': 731, 'Magura': 401,
                                'Manikjang': 536, 'Meherpur': 453, 'Moulvibazar': 626, 'Munshiganj': 490,
                                'Mymensing': 404, 'Naogan': 510, 'Narail': 635, 'Naraynganj': 516, 'Narsingdhi': 389,
                                'Natore': 413, 'Nawabganj': 598, 'Netrokona': 690, 'Nilphamari': 518, 'Noakhali': 747,
                                'Pabna': 282, 'Panchagrah': 604, 'Patuakhali': 831, 'Pirojpur': 500, 'Rajbari': 512,
                                'Rajshahi': 509, 'Rangamati': 644, 'Rangpur': 195, 'Satkhira': 692, 'Shariatpur': 574,
                                'Sherpur': 392, 'Sirajganj': 576, 'Sunamjang': 522, 'Sylhet': 584, 'Tangail': 528,
                                'Thakurgaon': 480},
                 'Dinajpur': {'Dhaka': 338, 'Bagerhat': 467, 'Bandarbon': 651, 'Barguna': 584, 'Barishal': 505,
                              'Bhola': 541, 'Bogra': 141, 'Brahmanbaria': 416, 'Chandpur': 450, 'Chittagong': 578,
                              'Chuadanga': 331, 'Comilla': 432, 'Coxs Bazar': 726, 'Dinajpur': 0, 'Faridpur': 378,
                              'Feni': 485, 'Gaibandha': 120, 'Gazipur': 310, 'Gopalganj': 460, 'Habijang': 463,
                              'Jamalpur': 469, 'Jessore': 313, 'Jhalokhati': 374, 'Jhenaidah': 519, 'Joypurhat': 329,
                              'Khagrachhari': 89, 'Khulna': 595, 'Kishoreganj': 434, 'Kurigram': 342, 'Kushtia': 134,
                              'Lakshimpur': 238, 'Lalmonirhat': 472, 'Madaripur': 129, 'Magura': 428, 'Manikjang': 355,
                              'Meherpur': 329, 'Moulvibazar': 321, 'Munshiganj': 509, 'Mymensing': 362, 'Naogan': 320,
                              'Narail': 127, 'Naraynganj': 408, 'Narsingdhi': 352, 'Natore': 358, 'Nawabganj': 207,
                              'Netrokona': 216, 'Nilphamari': 359, 'Noakhali': 57, 'Pabna': 494, 'Panchagrah': 266,
                              'Patuakhali': 94, 'Pirojpur': 540, 'Rajbari': 489, 'Rajshahi': 347, 'Rangamati': 205,
                              'Rangpur': 629, 'Satkhira': 78, 'Shariatpur': 446, 'Sherpur': 439, 'Sirajganj': 329,
                              'Sunamjang': 213, 'Sylhet': 603, 'Tangail': 547, 'Thakurgaon': 246},
                 'Faridpur': {'Dhaka': 101, 'Bagerhat': 140, 'Bandarbon': 413, 'Barguna': 209, 'Barishal': 131,
                              'Bhola': 167, 'Bogra': 239, 'Brahmanbaria': 206, 'Chandpur': 144, 'Chittagong': 339,
                              'Chuadanga': 118, 'Comilla': 193, 'Coxs Bazar': 487, 'Dinajpur': 378, 'Faridpur': 0,
                              'Feni': 246, 'Gaibandha': 308, 'Gazipur': 128, 'Gopalganj': 463, 'Habijang': 89,
                              'Jamalpur': 260, 'Jessore': 235, 'Jhalokhati': 96, 'Jhenaidah': 144, 'Joypurhat': 81,
                              'Khagrachhari': 290, 'Khulna': 356, 'Kishoreganj': 155, 'Kurigram': 214, 'Kushtia': 388,
                              'Lakshimpur': 96, 'Lalmonirhat': 171, 'Madaripur': 383, 'Magura': 73, 'Manikjang': 52,
                              'Meherpur': 65, 'Moulvibazar': 143, 'Munshiganj': 300, 'Mymensing': 102, 'Naogan': 203,
                              'Narail': 268, 'Naraynganj': 100, 'Narsingdhi': 109, 'Natore': 148, 'Nawabganj': 171,
                              'Netrokona': 264, 'Nilphamari': 239, 'Noakhali': 399, 'Pabna': 206, 'Panchagrah': 145,
                              'Patuakhali': 484, 'Pirojpur': 166, 'Rajbari': 147, 'Rajshahi': 31, 'Rangamati': 390,
                              'Rangpur': 345, 'Satkhira': 168, 'Shariatpur': 96, 'Sherpur': 250, 'Sirajganj': 190,
                              'Sunamjang': 393, 'Sylhet': 337, 'Tangail': 148, 'Thakurgaon': 447},
                 'Feni': {'Dhaka': 140, 'Bagerhat': 270, 'Bandarbon': 167, 'Barguna': 303, 'Barishal': 224,
                          'Bhola': 260, 'Bogra': 344, 'Brahmanbaria': 134, 'Chandpur': 105, 'Chittagong': 93,
                          'Chuadanga': 360, 'Comilla': 68, 'Coxs Bazar': 241, 'Dinajpur': 485, 'Faridpur': 246,
                          'Feni': 0, 'Gaibandha': 414, 'Gazipur': 183, 'Gopalganj': 89, 'Habijang': 219,
                          'Jamalpur': 209, 'Jessore': 325, 'Jhalokhati': 309, 'Jhenaidah': 237, 'Joypurhat': 323,
                          'Khagrachhari': 396, 'Khulna': 110, 'Kishoreganj': 273, 'Kurigram': 212, 'Kushtia': 495,
                          'Lakshimpur': 332, 'Lalmonirhat': 62, 'Madaripur': 490, 'Magura': 160, 'Manikjang': 294,
                          'Meherpur': 212, 'Moulvibazar': 385, 'Munshiganj': 249, 'Mymensing': 163, 'Naogan': 269,
                          'Narail': 394, 'Naraynganj': 275, 'Narsingdhi': 147, 'Natore': 172, 'Nawabganj': 357,
                          'Netrokona': 449, 'Nilphamari': 277, 'Noakhali': 505, 'Pabna': 41, 'Panchagrah': 363,
                          'Patuakhali': 590, 'Pirojpur': 259, 'Rajbari': 271, 'Rajshahi': 267, 'Rangamati': 403,
                          'Rangpur': 144, 'Satkhira': 451, 'Shariatpur': 332, 'Sherpur': 151, 'Sirajganj': 334,
                          'Sunamjang': 280, 'Sylhet': 343, 'Tangail': 287, 'Thakurgaon': 239},
                 'Gaibandha': {'Dhaka': 268, 'Bagerhat': 397, 'Bandarbon': 581, 'Barguna': 513, 'Barishal': 435,
                               'Bhola': 471, 'Bogra': 71, 'Brahmanbaria': 345, 'Chandpur': 380, 'Chittagong': 507,
                               'Chuadanga': 261, 'Comilla': 361, 'Coxs Bazar': 655, 'Dinajpur': 120, 'Faridpur': 308,
                               'Feni': 414, 'Gaibandha': 239, 'Gazipur': 392, 'Gopalganj': 219, 'Habijang': 399,
                               'Jamalpur': 243, 'Jessore': 304, 'Jhalokhati': 448, 'Jhenaidah': 259, 'Joypurhat': 77,
                               'Khagrachhari': 524, 'Khulna': 363, 'Kishoreganj': 271, 'Kurigram': 120, 'Kushtia': 212,
                               'Lakshimpur': 402, 'Lalmonirhat': 115, 'Madaripur': 358, 'Magura': 285, 'Manikjang': 259,
                               'Meherpur': 250, 'Moulvibazar': 439, 'Munshiganj': 292, 'Mymensing': 249, 'Naogan': 117,
                               'Narail': 338, 'Naraynganj': 382, 'Narsingdhi': 282, 'Natore': 287, 'Nawabganj': 137,
                               'Netrokona': 229, 'Nilphamari': 288, 'Noakhali': 131, 'Pabna': 423, 'Panchagrah': 195,
                               'Patuakhali': 216, 'Pirojpur': 470, 'Rajbari': 419, 'Rajshahi': 277, 'Rangamati': 182,
                               'Rangpur': 558, 'Satkhira': 76, 'Shariatpur': 376, 'Sherpur': 368, 'Sirajganj': 258,
                               'Sunamjang': 142, 'Sylhet': 532, 'Tangail': 476, 'Thakurgaon': 176},
                 'Gazipur': {'Dhaka': 37, 'Bagerhat': 215, 'Bandarbon': 350, 'Barguna': 284, 'Barishal': 206,
                             'Bhola': 242, 'Bogra': 169, 'Brahmanbaria': 114, 'Chandpur': 149, 'Chittagong': 276,
                             'Chuadanga': 237, 'Comilla': 130, 'Coxs Bazar': 425, 'Dinajpur': 310, 'Faridpur': 128,
                             'Feni': 183, 'Gaibandha': 239, 'Gazipur': 0, 'Gopalganj': 392, 'Habijang': 164,
                             'Jamalpur': 168, 'Jessore': 151, 'Jhalokhati': 216, 'Jhenaidah': 219, 'Joypurhat': 200,
                             'Khagrachhari': 221, 'Khulna': 294, 'Kishoreganj': 217, 'Kurigram': 99, 'Kushtia': 320,
                             'Lakshimpur': 184, 'Lalmonirhat': 171, 'Madaripur': 315, 'Magura': 127, 'Manikjang': 172,
                             'Meherpur': 64, 'Moulvibazar': 208, 'Munshiganj': 61, 'Mymensing': 93, 'Naogan': 219,
                             'Narail': 167, 'Naraynganj': 51, 'Narsingdhi': 56, 'Natore': 182, 'Nawabganj': 274,
                             'Netrokona': 129, 'Nilphamari': 330, 'Noakhali': 193, 'Pabna': 188, 'Panchagrah': 415,
                             'Patuakhali': 241, 'Pirojpur': 222, 'Rajbari': 119, 'Rajshahi': 228, 'Rangamati': 328,
                             'Rangpur': 276, 'Satkhira': 287, 'Shariatpur': 138, 'Sherpur': 159, 'Sirajganj': 105,
                             'Sunamjang': 301, 'Sylhet': 246, 'Tangail': 64, 'Thakurgaon': 378},
                 'Gopalganj': {'Dhaka': 127, 'Bagerhat': 52, 'Bandarbon': 386, 'Barguna': 196, 'Barishal': 117,
                               'Bhola': 153, 'Bogra': 324, 'Brahmanbaria': 231, 'Chandpur': 130, 'Chittagong': 312,
                               'Chuadanga': 171, 'Comilla': 218, 'Coxs Bazar': 460, 'Dinajpur': 463, 'Faridpur': 89,
                               'Feni': 219, 'Gaibandha': 392, 'Gazipur': 164, 'Gopalganj': 0, 'Habijang': 285,
                               'Jamalpur': 305, 'Jessore': 89, 'Jhalokhati': 91, 'Jhenaidah': 135, 'Joypurhat': 374,
                               'Khagrachhari': 329, 'Khulna': 54, 'Kishoreganj': 239, 'Kurigram': 473, 'Kushtia': 180,
                               'Lakshimpur': 157, 'Lalmonirhat': 468, 'Madaripur': 59, 'Magura': 105, 'Manikjang': 149,
                               'Meherpur': 197, 'Moulvibazar': 325, 'Munshiganj': 127, 'Mymensing': 249, 'Naogan': 353,
                               'Narail': 55, 'Naraynganj': 134, 'Narsingdhi': 173,'Natore': 256, 'Nawabganj': 348,
                               'Netrokona': 285, 'Nilphamari': 483, 'Noakhali': 192, 'Pabna': 230, 'Panchagrah': 568,
                               'Patuakhali': 152, 'Pirojpur': 59, 'Rajbari': 116, 'Rajshahi': 302, 'Rangamati': 363,
                               'Rangpur': 429, 'Satkhira': 114, 'Shariatpur': 82, 'Sherpur': 314, 'Sirajganj': 260,
                               'Sunamjang': 418, 'Sylhet': 363, 'Tangail': 219, 'Thakurgaon': 532},
                 'Habijang': {'Dhaka': 163, 'Bagerhat': 336, 'Bandarbon': 376, 'Barguna': 406, 'Barishal': 327,
                              'Bhola': 363, 'Bogra': 328, 'Brahmanbaria': 76, 'Chandpur': 218, 'Chittagong': 302,
                              'Chuadanga': 373, 'Comilla': 156, 'Coxs Bazar': 450, 'Dinajpur': 469, 'Faridpur': 260,
                              'Feni': 209, 'Gaibandha': 399, 'Gazipur': 168, 'Gopalganj': 258, 'Habijang': 0,
                              'Jamalpur': 257, 'Jessore': 322, 'Jhalokhati': 340, 'Jhenaidah': 336, 'Joypurhat': 380,
                              'Khagrachhari': 319, 'Khulna': 338, 'Kishoreganj': 132, 'Kurigram': 479, 'Kushtia': 322,
                              'Lakshimpur': 239, 'Lalmonirhat': 474, 'Madaripur': 248, 'Magura': 308, 'Manikjang': 202,
                              'Meherpur': 380, 'Moulvibazar': 63, 'Munshiganj': 176, 'Mymensing': 200, 'Naogan': 380,
                              'Narail': 63, 'Naraynganj': 176, 'Narsingdhi': 200,'Natore': 378, 'Nawabganj': 289,
                              'Netrokona': 161, 'Nilphamari': 121, 'Noakhali': 341, 'Pabna': 433, 'Panchagrah': 197,
                              'Patuakhali': 490, 'Pirojpur': 218, 'Rajbari': 347, 'Rajshahi': 574, 'Rangamati': 362,
                              'Rangpur': 343, 'Satkhira': 257, 'Shariatpur': 387, 'Sherpur': 353, 'Sirajganj': 435,
                              'Sunamjang': 398, 'Sylhet': 259, 'Tangail': 258, 'Thakurgaon': 265},
                 'Jamalpur': {'Dhaka': 179, 'Bagerhat': 357, 'Bandarbon': 492, 'Barguna': 426, 'Barishal': 348,
                              'Bhola': 384, 'Bogra': 172, 'Brahmanbaria': 203, 'Chandpur': 291, 'Chittagong': 418,
                              'Chuadanga': 276, 'Comilla': 272, 'Coxs Bazar': 576, 'Dinajpur': 313, 'Faridpur': 235,
                              'Feni': 325, 'Gaibandha': 243, 'Gazipur': 151, 'Gopalganj': 305, 'Habijang': 257,
                              'Jamalpur': 0, 'Jessore': 319, 'Jhalokhati': 361, 'Jhenaidah': 274, 'Joypurhat': 224,
                              'Khagrachhari': 436, 'Khulna': 378, 'Kishoreganj': 125, 'Kurigram': 323, 'Kushtia': 227,
                              'Lakshimpur': 313, 'Lalmonirhat': 318, 'Madaripur': 269, 'Magura': 278, 'Manikjang': 170,
                              'Meherpur': 266, 'Moulvibazar': 297, 'Munshiganj': 203, 'Mymensing': 57, 'Naogan': 222,
                              'Narail': 309, 'Naraynganj': 193, 'Narsingdhi': 198,'Natore': 185, 'Nawabganj': 278,
                              'Netrokona': 96, 'Nilphamari': 334, 'Noakhali': 335, 'Pabna': 191, 'Panchagrah': 418,
                              'Patuakhali': 383, 'Pirojpur': 364, 'Rajbari': 226, 'Rajshahi': 231, 'Rangamati': 470,
                              'Rangpur': 279, 'Satkhira': 391, 'Shariatpur': 280, 'Sherpur': 16, 'Sirajganj': 109,
                              'Sunamjang': 391, 'Sylhet': 335, 'Tangail': 87, 'Thakurgaon': 382},
                 'Jessore': {'Dhaka': 164, 'Bagerhat': 93, 'Bandarbon': 476, 'Barguna': 209, 'Barishal': 168,
                             'Bhola': 204, 'Bogra': 235, 'Brahmanbaria': 269, 'Chandpur': 195, 'Chittagong': 402,
                             'Chuadanga': 82, 'Comilla': 256, 'Coxs Bazar': 550, 'Dinajpur': 374, 'Faridpur': 96,
                             'Feni': 309, 'Gaibandha': 304, 'Gazipur': 216, 'Gopalganj': 89, 'Habijang': 322,
                             'Jamalpur': 319, 'Jessore': 0, 'Jhalokhati': 148, 'Jhenaidah': 46, 'Joypurhat': 286,
                             'Khagrachhari': 419, 'Khulna': 59, 'Kishoreganj': 277, 'Kurigram': 384, 'Kushtia': 92,
                             'Lakshimpur': 222, 'Lalmonirhat': 379, 'Madaripur': 124, 'Magura': 44, 'Manikjang': 152,
                             'Meherpur': 108, 'Moulvibazar': 362, 'Munshiganj': 165, 'Mymensing': 291, 'Naogan': 264,
                             'Narail': 34, 'Naraynganj': 172, 'Narsingdhi': 211,'Natore': 167, 'Nawabganj': 259,
                             'Netrokona': 327, 'Nilphamari': 395, 'Noakhali': 257, 'Pabna': 141, 'Panchagrah': 480,
                             'Patuakhali': 200, 'Pirojpur': 115, 'Rajbari': 119, 'Rajshahi': 213, 'Rangamati': 453,
                             'Rangpur': 340, 'Satkhira': 72, 'Shariatpur': 147, 'Sherpur': 334, 'Sirajganj': 219,
                             'Sunamjang': 456, 'Sylhet': 400, 'Tangail': 236, 'Thakurgaon': 443},
                 'Jhalokhati': {'Dhaka': 182, 'Bagerhat': 100, 'Bandarbon': 404, 'Barguna': 95, 'Barishal': 19,
                                'Bhola': 55, 'Bogra': 379, 'Brahmanbaria': 287, 'Chandpur': 149, 'Chittagong': 330,
                                'Chuadanga': 231, 'Comilla': 215, 'Coxs Bazar': 479, 'Dinajpur': 519, 'Faridpur': 144,
                                'Feni': 237, 'Gaibandha': 448, 'Gazipur': 219, 'Gopalganj': 91, 'Habijang': 340,
                                'Jamalpur': 361, 'Jessore': 148, 'Jhalokhati': 0, 'Jhenaidah': 194, 'Joypurhat': 430,
                                'Khagrachhari': 348, 'Khulna': 90, 'Kishoreganj': 294, 'Kurigram': 528, 'Kushtia': 236,
                                'Lakshimpur': 176, 'Lalmonirhat': 523, 'Madaripur': 77, 'Magura': 193, 'Manikjang': 205,
                                'Meherpur': 256, 'Moulvibazar': 380, 'Munshiganj': 183, 'Mymensing': 305, 'Naogan': 408,
                                'Narail': 162, 'Naraynganj': 190, 'Narsingdhi': 229,'Natore': 311, 'Nawabganj': 404,
                                'Netrokona': 340, 'Nilphamari': 539, 'Noakhali': 210, 'Pabna': 285, 'Panchagrah': 624,
                                'Patuakhali': 52, 'Pirojpur': 33, 'Rajbari': 171, 'Rajshahi': 357, 'Rangamati': 382,
                                'Rangpur': 485, 'Satkhira': 145, 'Shariatpur': 101, 'Sherpur': 370, 'Sirajganj': 316,
                                'Sunamjang': 474, 'Sylhet': 418, 'Tangail': 275, 'Thakurgaon': 587}}
        cur = str(vehicle.place)
        pick = str(request.session['current_place'])
        des = str(request.session['destination_place'])
        prices = price[cur][pick]+price[pick][des]
        if datetime.datetime.now().month == 5 or datetime.datetime.now().month== 6:
            if vehicle.capacity >10:
                prices = prices*35
            else:
                prices = prices*30

        else:
            if vehicle.capacity >10:
                prices = prices*31
            else:
                prices = prices*27


    except Vehicle.DoesNotExist:
        raise Http404( "Book does not exist" )
    try:
        if request.method == 'POST' and request.POST['book'] == 'Confirm':
            veh = Vehicle.objects.get( pk=pk )
            if not veh.client:
                veh.client = request.user
                veh.place = request.session['destination_place']
                veh.save()
                message2 = "You have booked vehicle with license number: "+str(veh.license_no)+"Price: "+ str(prices)+'''
                To contact with owner:
                Owner Name:'''+ str(veh.user.username)+'''
                Email'''+str(veh.user.email)+'''
                phone'''+str(veh.user.address.phone_number)
                message1 = "Your Vehicle with license number: "+str(veh.license_no)+" has been booked by"+'''
                '''+ " Username: "+str(request.user.username)+'''
                 Email:'''+str(request.user.email)+'''
                 Phone: '''+str(request.user.address.phone_number)+'''
                Pay price to client RS: '''+str(prices)

                send_mail(
                    'Vehicle Booking Successful',
                    message2,
                    'mahirmahbub7@gmail.com',
                    [str(veh.user.email)],
                    fail_silently=False,
                )
                send_mail(
                    'Your Vehicle has been Booked',
                    message1,
                    'mahirmahbub7@gmail.com',
                    [str( request.user.email )],
                    fail_silently=False,
                )
                #return HttpResponse("Booked")
                messages.info( request, 'You have booked the vehicle successfully!' )
                return redirect(borrow_vehicle_list_view)
            else:
                # return HttpResponse( 'Can not Book.Already Booked')
                messages.info( request, 'Can not Book.Already Booked' )
                return redirect(borrow_vehicle_list_view)
    except MultiValueDictKeyError:
        raise Http404( "Internal Error" )
        #HttpResponse("Internal Error")

    # book_id=get_object_or_404(Book, pk=pk)

    return render(
        request,
        'BorrowVehicleDetails.html',
        context={'vehicle': vehicle,'prices':prices }
    )

def driver_login(request):
    if request.user.is_authenticated:
        logout(request)
    if request.method == 'POST':
        driv_log_in = DriverLogin(request.POST)
        if driv_log_in.is_valid():
            driver_code = driv_log_in.cleaned_data['driver_code']
            passwd_veh = driv_log_in.cleaned_data['vehicle_password']
            #passwd_hashed = make_password(str(passwd_veh))
            user = User.objects.get( username=driver_code )
            pk = user.id
            #user = authenticate( username=driver_code, password=passwd_veh )
            user.backend = 'django.contrib.auth.backends.ModelBackend'

            login( request, user)
        return HttpResponseRedirect( '/accounts/vehicle_login/')
    else:
        driv_log_in = DriverLogin()

    return render( request, 'DriverLogin.html', {'form': driv_log_in} )

def dummy(request):
    # user = User.objects.get(username='user1')
    # #user = request.user
    # txt = "<h2>"
    # txt += "username: " + user.username
    # txt += "present address City: " + user.profile.current_address.city
    # txt += "permnent district: "  + user.profile.permanent_address.district + "</h2>"
    # return HttpResponse("Welcoome")
    # return render_to_response( "base.html",
    #                            RequestContext( request ) )
    return render( request, 'allauth/account/home.html' )
#
# class AuthorDelete(DeleteView):
#     model = Vehicle
#     success_url = reverse_lazy('borrow_vehicle_details_view')

@login_required
@group_required('Owner')
def added_vehicle_list_view(request):
    user = request.user
    added_vehicle_list = Vehicle.objects.filter( user= user )
    page = request.GET.get('page', 1)
    #borrow_vehicle = None
    paginator = Paginator(added_vehicle_list,4)
    try:
        added_vehicle = paginator.page(page)
    except PageNotAnInteger:
        added_vehicle = paginator.page(1)
    except EmptyPage:
        added_vehicle = paginator.page(paginator.num_pages)
    return render( request, 'AddVehiceListSheet.html', {'added_vehicle': added_vehicle} )

@login_required
@group_required('Owner')
def added_vehicle_details_view(request, pk):
    request.session['pk'] = pk
    try:
        vehicle = Vehicle.objects.get( pk=pk )
        print("Found")
        print(request.POST)
    except Vehicle.DoesNotExist:
        raise Http404( "Book does not exist" )
    try:
        if request.method == 'POST' and request.POST['delete'] == 'Delete':
            veh = Vehicle.objects.get( pk=pk )
            if veh.client_id ==None:
                print("Not Booked")
                veh.delete()
                messages.info(request,"Vehicle has been deleted")
                return redirect(added_vehicle_list_view)
            else:
                messages.info(request,"Can not delete. Already Booked")

                print("Done")
                return redirect(added_vehicle_details_view)
            # return HttpResponse( 'deleted' )
    except:
        try:
            if request.method == 'POST' and request.POST['track'] == 'Track':
                print("Got")
                try:
                    track_vehicle = TrackVehicle.objects.get(this_vehicle_id= pk)
                    print(track_vehicle.latitude)
                    # return render(
                    #     request,
                    #     'Track_borrowed_vehicle.html',
                    #     context={'track_vehicle': track_vehicle, }
                    # )
                    return render(
                        request,
                        'Vehicle_Position.html',
                        context={'track_vehicle': track_vehicle, })
                        #return HttpResponse("Booked")
                except ObjectDoesNotExist:
                    print("Cannot found")
                    HttpResponse("Cannot found")
            # print("ADADA")
            # except MultiValueDictKeyError:
            #     HttpResponse("Internal Error")

            # book_id=get_object_or_404(Book, pk=pk)
        except MultiValueDictKeyError:
            Http404("Internal Error")

    return render(
        request,
        'AddedVehicleDetails.html',
        context={'vehicle': vehicle, }
    )

@login_required
@group_required('Driver')
def own_location_view(request):
    if request.method == 'POST' and request.is_ajax:
        post_text = request.body.decode('utf-8')
        #print(post_text)
        #post_text = json.load(request.body)

        #print("Raw Data: ",re
        # quest.body.decode('utf-8'))
        # if not post_text is None:
        # #
        # #     print(post_text)
        data = post_text.split('&')
        lat = data[0].split("=")[1]
        lon =  data[1].split("=")[1]
        #time = data[2].split("=")[1]
        print(lat,lon)
        user_ = request.user
        print(user_.id)
        pos = TrackVehicle.objects.get(this_vehicle__driver_code_name=user_)

        pos.latitude = float(lat)
        pos.longitude = float(lon)
        import datetime
        pos.time = str(datetime.datetime.now())
        pos.save()
        # HttpResponse( " Got it" )
    return render(
        request,
        'Vehicle_Own_Position.html',)

@login_required
def get_loc_data(request,pk):
    global lan
    track_vehicle = None
    dicto = {}
    print(pk)
    try:
        print("Yay")
        request.session['pk'] = pk
        # veh = Vehicle.objects.get( pk=pk )
        # if not veh.client:
        #     veh.client = request.user
        #     veh.save()
        # try:
        #     if request.method == "GET":
        #         track_vehicle = TrackVehicle.objects.get(this_vehicle_id= pk)
        #         print(track_vehicle.latitude)
        #         lan = track_vehicle.latitude
        #         print(lan)
        #         lng = track_vehicle.longitude
        #         dicto["lan"] = lan
        #         dicto ["lng"] = lng
        #         #return HttpResponse("Booked")
        #         return JsonResponse( dicto )
        # except ObjectDoesNotExist:
        #     print("Cannot found")
        #     HttpResponse("Cannot found")
    except MultiValueDictKeyError:
        HttpResponse("Internal Error")
    return render(request, 'Vehicle_Position.html', dicto)

def get_data(request):
    dicto={}
    pk=request.session['pk']
    try:

        if request.method == "GET":
            track_vehicle = TrackVehicle.objects.get( this_vehicle_id=pk )
            print( track_vehicle.latitude )
            lan = track_vehicle.latitude
            print( lan )
            lng = track_vehicle.longitude
            dicto["lan"] = lan
            dicto["lng"] = lng
            dicto ["time"] = str(track_vehicle.time)
            # return HttpResponse("Booked")
            return JsonResponse( dicto )
    except ObjectDoesNotExist:
        print( "Cannot found" )
        HttpResponse( "Cannot found" )




#
#
#
#
#
@login_required
@group_required('Client')
def Borrowed_vehicle_list_view(request):
    user = request.user
    borrowed_vehicle_list = Vehicle.objects.filter( client= user )
    page = request.GET.get('page', 1)
    #borrow_vehicle = None
    paginator = Paginator(borrowed_vehicle_list,4)
    try:
        borrowed_vehicle = paginator.page(page)
    except PageNotAnInteger:
        borrowed_vehicle = paginator.page(1)
    except EmptyPage:
        borrowed_vehicle = paginator.page(paginator.num_pages)
    return render( request, 'ClientBorrowedVehicleListSheet.html', {'borrowed_vehicle': borrowed_vehicle} )

@login_required
@group_required('Client')
def Borrowed_vehicle_details_view(request, pk):
    request.session['pk'] = pk
    try:
        vehicle = Vehicle.objects.get( pk=pk )
    except Vehicle.DoesNotExist:
        raise Http404( "Book does not exist" )
    try:
        # if request.method == 'POST' and request.POST['delete'] == 'Delete':
        #     veh = Vehicle.objects.get( pk=pk )
        #     veh.delete()
        #     return HttpResponse( 'deleted' )
        if request.method == 'POST' and request.POST['track'] == 'Track':
            print("Got")
            try:
                track_vehicle = TrackVehicle.objects.get(this_vehicle_id= pk)
                print(track_vehicle.latitude)
                return render(
                    request,
                    'Vehicle_Position.html',
                    context={'track_vehicle': track_vehicle, }
                )
                #return HttpResponse("Booked")
            except ObjectDoesNotExist:
                print("Cannot found")
                #HttpResponse("Cannot found")
    except MultiValueDictKeyError:
        HttpResponse("Internal Error")

    # book_id=get_object_or_404(Book, pk=pk)

    return render(
        request,
        'ClientBorrowedVehicleDetails.html',
        context={'vehicle': vehicle, }
    )

def contact_us(request):
    return render( request, 'Contact.html' )

def credit(request):
    return render( request, 'Credit.html' )