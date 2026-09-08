from django.urls import path

from clinic import views

app_name = 'clinic'

urlpatterns = [
    path('', views.home, name='home'),
    path('directions/', views.directions_list, name='directions'),
    path('directions/<slug:slug>/', views.direction_detail, name='direction_detail'),
    path('doctors/', views.doctors_list, name='doctors'),
    path('doctors/<slug:slug>/', views.doctor_detail, name='doctor_detail'),
    path('services/', views.services_list, name='services'),
    path('services/<slug:slug>/', views.service_detail, name='service_detail'),
    path('price/', views.price_list, name='price'),
    path('surgical-operations/', views.surgical_operations_list, name='surgical_operations'),
    path('about/', views.about_us, name='about_us'),
    path('hearing-aids/', views.hearing_aids_list, name='hearing_aids'),
    path('contacts/', views.contacts, name='contacts'),
    path('booking/', views.booking, name='booking'),
    path('booking/services/', views.booking_services, name='booking_services'),
    path('booking/doctors/', views.booking_doctors, name='booking_doctors'),
    path('privacy/', views.privacy, name='privacy'),
    path('webhooks/keycrm/<str:token>/', views.keycrm_webhook, name='keycrm_webhook'),
]
