from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from attendance.models import Student, Section
from attendance.utils import generate_qr_code
import json

def register_student(request):
    if request.method == 'POST':
        try:
            # Get form data
            data = {
                'first_name': request.POST.get('first_name'),
                'last_name': request.POST.get('last_name'),
                'lrn': request.POST.get('lrn'),
                'student_id': request.POST.get('student_id'),
                'email': request.POST.get('email'),
                'birth_date': request.POST.get('birth_date'),
                'section_id': request.POST.get('section'),
                'parent_name': request.POST.get('parent_name'),
                'parent_email': request.POST.get('parent_email'),
                'parent_mobile': request.POST.get('parent_mobile'),
            }
            
            # Create student object
            student = Student.objects.create(**data)
            
            # Generate QR code data
            qr_data = {
                'id': student.id,
                'student_id': student.student_id,
                'name': f"{student.first_name} {student.last_name}",
                'lrn': student.lrn
            }
            
            # Generate QR code
            qr_code_base64 = generate_qr_code(json.dumps(qr_data))
            
            # Prepare and send email
            subject = 'Your Student QR Code'
            message = render_to_string('email/qr_code_email.html', {
                'student': student,
                'school_name': settings.SCHOOL_NAME
            })
            
            email = EmailMessage(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [student.email]
            )
            email.content_subtype = "html"
            email.attach('qr_code.png', qr_code_base64, 'image/png')
            
            if email.send():
                messages.success(request, 'Registration successful! Please check your email for your QR code.')
                return redirect('registration_success')
            else:
                messages.warning(request, 'Registration successful but failed to send email. Please contact administrator.')
                return redirect('registration_success')
                
        except Exception as e:
            messages.error(request, f'Registration failed: {str(e)}')
            return redirect('register_student')
    
    # GET request - show form
    sections = Section.objects.all()
    return render(request, 'register_student.html', {'sections': sections})