from django.urls import path
from . import views
from attendance.views.registration import register_student

urlpatterns = [
    path('', views.index, name='index'),
    path('scan-qr/', views.scan_qr, name='scan_qr'),
    path('export-excel/', views.export_excel, name='export_excel'),
    path('register/', register_student, name='register_student'),
    path('registration-success/', views.registration_success, name='registration_success'),
]