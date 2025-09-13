from django.urls import path
from .views import (
    index, scan_qr, generate_qr, export_excel,
    register_student, get_subjects
)

urlpatterns = [
    path('', index, name='index'),
    path('register/', register_student, name='register_student'),
    path('scan-qr/', scan_qr, name='scan_qr'),  # QR scanner endpoint for POST
    path('qrgenerator/', generate_qr, name='generate_qr'),
    path('qrscanner/', scan_qr, name='qrscanner'),  # QR scanner page for GET
    path('api/subjects/', get_subjects, name='get_subjects'),  # Get subject list
    path('export/', export_excel, name='export_excel'),
]